"""Basic class for properties"""

import logging
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from .table import DigikamTable
from .exceptions import DigikamObjectNotFound, DigikamMultipleObjectsFound


log = logging.getLogger(__name__)


class BasicProperties(DigikamTable):
    """
    Basic class for properties
    
    Instances of this class belong to a Digikam object that has a property
    (e.g. ``properties``) that points to the BasicProperties instance. The
    individual properties can be accessed similarly to ``dict`` values:
    
    .. code-block:: python
        
        obj.properties['myprop'] = 'myvalue'        # set a property
        if 'myprop' in obj.properties:              # check if a property exists
            opj.properties.remove('myprop')         # remove a property
    
    The class is iterable, yielding all property names, and has a method
    :meth:`~BasicProperties.items` similar to that of :meth:`dict <dict.items>`.
    
    The number of properties can be found with ``len(obj.properties)``
    
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
        super().__init__(parent.digikam, log_create = False)
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
        return self._select_prop(prop).count() > 0
    
    def __getitem__(self, prop: Union[str, int, Sequence]) -> str:  # noqa: F821
        """[] operator"""
        try:
            if self._raise_on_not_found:
                ret = self._select_prop(prop).one()
            else:
                ret = self._select_prop(prop).one_or_none()
                if ret is None:
                    log.debug('No record found, returning None')
                    return None
        except NoResultFound:
            raise DigikamObjectNotFound('No %s object for %s=%s' % (
                self.Class.__name__, self._id_column, prop
            ))
        except MultipleResultsFound:                        # pragma: no cover
            raise DigikamMultipleObjectsFound('Multiple %s objects for %s=%s' % (
                self.Class.__name__, self._id_column, prop
            ))
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
        
        try:
            row = self._select_prop(prop).one_or_none()
        except MultipleResultsFound:                        # pragma: no cover
            raise DigikamMultipleObjectsFound('Multiple %s objects for %s=%s' % (
                self.Class.__name__, self._id_column, prop
            ))
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
    
    def get(
        self,
        prop: Union[str, int, Sequence],
        default: Any = None
    ) -> str:
        """
        Works similar to :meth:`dict.get`.
        """
        ret = self._select_prop(prop).one_or_none()
        if ret is None:
            return default
        else:
            return self._post_process_value(ret)
    
    def items(self) -> Iterable[Tuple]:
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
    
    def update(self, values: Optional[Mapping] = None, **kwargs):
        """
        Updates multiple properties.
        
        This method behaves like :meth:`dict.update`.
        
        Args:
            values:     ``dict`` with new values
            kwargs:     Mapping for new values
        """
        if values:
            for key, value in values.items():
                self[key] = value
        if kwargs:
            for key, value in kwargs.items():
                self[key] = value
    
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
        try:
            row = self._select_prop(prop).one_or_none()
        except MultipleResultsFound:                        # pragma: no cover
            raise DigikamMultipleObjectsFound('Multiple %s objects for %s=%s' % (
                self.Class.__name__, self._id_column, prop
            ))
        if row is not None:
            self._session.delete(row)
    
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
            if len(ret) > len(self._key_col):               # pragma: no cover
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
        if isinstance(self._value_col, str):                # pragma: no cover
            return value
        
        if value is None:
            ret = []
        elif isinstance(value, (str, int)):
            ret = [value]
        else:
            # value must be iterable from here on
            ret = list(value)
            if len(ret) > len(self._value_col):             # pragma: no cover
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

