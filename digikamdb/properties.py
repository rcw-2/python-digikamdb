"""Basic class for properties"""

import logging
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .table import DigikamTable


log = logging.getLogger(__name__)


class BasicProperties(DigikamTable):
    """
    Basic class for properties
    
    Instances of this class belong to a Digikam object that has a property
    named ``properties`` that points to the BasicProperties instance. The
    individual properties can be accessed as follows:
    
    .. code-block:: python
        
        obj.properties['myprop'] = 'myvalue'        # set a property
        if 'myprop' in obj.properties:              # check if a property exists
            opj.properties.remove('myprop')         # remove a property
    
    The class is iterable, yielding all property names, and has a method
    :meth:`~BasicProperties.items` similar to that of :meth:`dict <dict.items>`.
    
    Args:
        parent:     Object the properties belong to.
    """
    
    #: Column specifying the parent's id
    _parent_id_col = None
    
    #: Relationship on the parent side
    _relationship = None
    
    #: Key column(s)
    #:
    #: Can be str or a sequence of str if there are multiple columns.
    #: Property keys passed as arguments to ``[]`` or ``in`` are
    #: converted to tuples in the latter case.
    _key_col = None
    
    #: Value column(s)
    #:
    #: Can be str or a sequence of str if there are multiple columns.
    #: 
    #: Property values passed as arguments to ``[]`` or ``in`` are
    #: converted to tuples in the latter case.
    _value_col = None
    
    #: Remove item when set to ``None``?
    _remove_on_set_none = False
    
    def __init__(self, parent: 'DigikamObject'):            # noqa: F821
        log.debug(
            'Creating %s object for %s %d',
            self.__class__.__name__,
            parent.__class__.__name__,
            parent.id
        )
        super().__init__(parent._container.digikam, log_create = False)
        self._parent = parent
    
    @property
    def parent(self) -> 'DigikamObject':                    # noqa: F821
        """Returns the parent object."""
        return self._parent
    
    def __len__(self) -> int:
        """
        Returns the number of rows containing properties for the parent.
        """
        return self._select_self().count()
    
    def __contains__(self, prop: Union[str, int, Sequence]) -> bool:
        """in operator"""
        return self._select_prop(prop).one_or_none() is not None
    
    def __getitem__(self, prop: Union[str, int, Sequence]) -> str:  # noqa: F821
        """[] operator"""
        if self._raise_on_not_found:
            ret = self._select_prop(prop).one()
        else:
            ret = self._select_prop(prop).one_or_none()
            if ret is None:
                log.debug('No record found, returning None')
                return None
        return self._post_process_value(ret)
    
    def __setitem__(
        self,
        prop: Union[str, int, Sequence, None],
        value: Union[str, int, Tuple, None]
    ):
        """[] operator"""
        log.debug(
            'Setting %s[%s] of %s(id=%d) to %s',
            self.__class__.__name__,
            prop,
            self._parent.__class__.__name__,
            self._parent.id,
            value
        )
        
        if value is None and self._remove_on_set_none:
            log.debug(
                'Removing %s[%s] as new value is None',
                self.__class__.__name__, prop
            )
            self.remove(prop)
            return
        
        if isinstance(self._value_col, str):
            values = { self._value_col: value }
        else:
            values = dict(zip(
                self._value_col,
                self._pre_process_value(value)
            ))
        
        row = self._select_prop(prop).one_or_none()
        if row:
            for k, v in values.items():
                setattr(row, k, v)
        else:
            attrs = self._prop_attributes(prop, **values)
            log.debug(
                '%s: creating %s object with %s', self.__class__.__name__,
                self.Class.__name__,
                attrs
            )
            self._session.add(self.Class(**attrs))
    
    def __iter__(self) -> Iterable:
        """Iterates over all properties of parent"""
        log.debug('%s: iterating over objects', self.__class__.__name__)
        yield from self._select_self()
    
    def items(self) -> Iterable:
        """
        Returns the properties as an iterable yielding (key, value) tuples.
        """
        log.debug('%s: iterating over items', self.__class__.__name__)
        for row in self._select_self():
            if isinstance(self._key_col, str):
                key = getattr(row, self._key_col)
            else:
                key = tuple(getattr(row, col) for col in self._key_col)
            
            yield self._post_process_key(key), self._post_process_value(row)
    
    def _select_self(self) -> '~sqlalchemy.orm.Query':      # noqa: F821
        """Selects all properties of the parent object."""
        return self._select(**{ self._parent_id_col: self.parent.id })
    
    def _select_prop(
        self,
        prop: Union[str, int, Iterable, None]
    ) -> '~sqlalchemy.orm.Query':                           # noqa: F821
        """Selects a specific property."""
        kwargs = {}
        if isinstance(self._key_col, str):
            kwargs[self._key_col] = self._pre_process_key(prop)
        else:
            kwargs.update(dict(zip(
                self._key_col,
                self._pre_process_key(prop)
            )))
        
        return self._select_self().filter_by(**kwargs)
    
    def _prop_attributes(self, prop: Union[str, int, Iterable, None], **values):
        """Returns **all** attributes for a new property object."""
        attrs = { self._parent_id_col: self.parent.id }
        if isinstance(self._key_col, str):
            attrs[self._key_col] = self._pre_process_key(prop)
        else:
            attrs.update(dict(zip(
                self._key_col,
                self._pre_process_key(prop)
            )))
        attrs.update(**values)
        return attrs
    
    def filter_by(self, **kwargs) -> Iterable['DigikamObject']:  # noqa: F821
        """
        Returns the result of ``filter_by`` on the parent's relationship
        attribute.
        """
        return getattr(self.parent, self._relationship).filter_by(**kwargs)
    
    def remove(self, prop: Union[str, int, Iterable, None]):
        """
        Removes the given property.
        
        Args:
            prop:   Property to remove.
        """
        log.debug(
            'Removing %s[%s] from %d',
            self.__class__.__name__,
            prop,
            self._parent.id,
        )
        row = self._select_prop(prop).one_or_none()
        if row is not None:
            self._session.delete(row)
    
    def _key_col_kwargs(
        self,
        prop: Any,
        add_parent_id: bool = True,
        **kwargs
    ) -> Mapping[str, Any]:
        """
        Returns kwargs suitable for filtering queries.
        """
        ret = {}
        if add_parent_id:
            ret = {self._parent_id_col: self._parent.id}
        
        if isinstance(self._key_col, str):
            ret[self._key_col] = self._pre_process_key(prop)
        else:
            ret.update(dict(zip(
                self._key_col,
                self._pre_process_key(prop)
            )))
        ret.update(kwargs)
        return ret
    
    def _pre_process_key(self, key: Union[str, int, Iterable, None]) -> Tuple:
        """Preprocesses key for [] operations."""
        # No preprocessing if parent id is a single column
        if isinstance(self._key_col, str):
            return key
        
        if key is None:
            ret = []
        elif isinstance(key, (str, int)):
            ret = [key]
        else:
            # key must be iterable from here on
            ret = list(key)
            if len(ret) > len(self._key_col):
                ret = ret[:len(self._key_col)]
        
        # make sure list is long enough
        while len(ret) < len(self._key_col):
            ret.append(None)
        
        return tuple(ret)
    
    def _post_process_key(self, key: Union[str, Tuple]) -> Any:
        """Postprocesses key from :meth:`~BasicProperties.items`"""
        return key
    
    def _pre_process_value(
        self,
        value: Union[str, int, Tuple, List, None]
    ) -> Union[str, int, Tuple]:
        """Preprocesses values for [] operations."""
        if isinstance(self._value_col, str):
            return value
        
        if value is None:
            ret = []
        elif isinstance(value, (str, int)):
            ret = [value]
        else:
            # value must be iterable from here on
            ret = list(value)
            if len(ret) > len(self._value_col):
                ret = ret[:len(self._value_col)]
        
        # make sure list is long enough
        while len(ret) < len(self._value_col):
            ret.append(None)
        
        return tuple(ret)
    
    def _post_process_value(
        self,
        obj: 'DigikamObject'                                # noqa: F821
    ) -> Union[str, int, Tuple, None]:
        """Postprocesses values from [] operations."""
        # Return object property if there is only one value column:
        if isinstance(self._value_col, str):
            return getattr(obj, self._value_col)
        
        # Generate tuple for multiple columns:
        return tuple(getattr(obj, attr) for attr in self._value_col)

