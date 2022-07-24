"""Basic class for properties"""

import logging
from typing import Iterable, Optional

from .table import DigikamTable


log = logging.getLogger(__name__)


class BasicProperties(DigikamTable):
    """
    Basic class for properties
    
    Instances of this class belong to a Digikam object that has a property
    named ``properties`` that points to the BasicProperties instance. The
    individual properties can be accessed as follows:
    
    .. code:: python
        
        obj.properties['myprop'] = 'myvalue'        # set a property
        if 'myprop' in obj.properties:              # check if a property exists
            opj.properties.remove('myprop')         # remove a property
    
    The class is iterable, yielding all property names, and has a method
    :meth:`~BasicProperties.items` similar to that of :class:`python.dict`.
    
    Args:
        digikam:    Digikam object.
        parent:     Object the properties belong to.
    """
    
    # Parent id column
    _parent_id_col = None
    
    # Key column
    _key_col = None
    
    # Value column
    _value_col = None
    
    def __init__(self, parent: 'DigikamObject'):            # noqa: F821
        log.debug('Creating properties object for %d', parent.id)
        super().__init__(parent._container.digikam)
        self._parent = parent
    
    @property
    def parent(self) -> 'DigikamObject':                    # noqa: F821
        """Returns the parent object."""
        return self._parent
    
    def __contains__(self, prop: str) -> bool:
        """in operator"""
        kwargs = { self._parent_id_col: self.parent.id, self._key_col: prop }
        return self._select(**kwargs).one_or_none() is not None
    
    def __getitem__(self, prop: str) -> str:                # noqa: F821
        """[] operator"""
        kwargs = { self._parent_id_col: self._parent.id, self._key_col: prop }
        return getattr(self._select(**kwargs).one(), self._value_col)
    
    def __setitem__(self, prop: str, value: Optional[str]):
        """[] operator"""
        log.debug(
            'Setting %s[%s] of %d to %s',
            self.__class__.__name__,
            prop,
            self._parent.id,
            value
        )
        kwargs = { self._parent_id_col: self.parent.id, self._key_col: prop }
        row = self._select(**kwargs).one_or_none()
        if row:
            setattr(row, self._value_col, value)
        else:
            kwargs[self._value_col] = value
            self._insert(**kwargs)
    
    def __iter__(self) -> Iterable:
        kwargs = { self._parent_id_col: self.parent.id }
        for row in self._select(**kwargs):
            yield getattr(row, self._value_col)
    
    def items(self) -> Iterable:
        """
        Returns the properties as an iterable yielding (key, value) tuples.
        """
        kwargs = { self._parent_id_col: self.parent.id }
        for row in self._select(**kwargs):
            yield getattr(row, self._key_col), getattr(row, self._value_col)
    
    def remove(self, prop: str):
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
        kwargs = { self._parent_id_col: self.parent.id, self._key_col: prop }
        self._delete(**kwargs)

