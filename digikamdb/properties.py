"""Basic class for properties"""

import logging
from typing import Iterable, Optional

from sqlalchemy import delete, func, insert, select, text, update


# TagProperties and ImageProperties have no primary key in Digikam, so
# the ORM will not work. Instead, we use derivatives of this class to
# access properties.


log = logging.getLogger(__name__)


class BasicProperties:
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
        parent:     Object the properties belong to.
    """
    
    # Parent id column
    _parent_id_col = None
    
    # Key column
    _key_col = None
    
    # Value column
    _value_col = None
    
    def __init__(
        self,
        parent: 'DigikamObject'                             # noqa: F821
    ):
        log.debug(
            'Creating %s object for %d',
            self.__class__.__name__,
            parent.id
        )
        self._parent = parent
        self._table  = parent.properties_table
        self._session = parent.session
    
    def __contains__(self, prop: str) -> bool:
        return self._session.connection().execute(
            select(func.count('*'))
            .select_from(self._table)
            .filter(text("%s = '%s'" %
                         (self._parent_id_col, self._parent.id)))
            .filter(text("%s = '%s'" %
                         (self._key_col, prop)))
        ).one()[0] > 0
    
    def __getitem__(self, prop: str) -> 'TagProperty':      # noqa: F821
        return self._session.connection().execute(
            select(self._table)
            .filter(text("%s = '%s'" %
                         (self._parent_id_col, self._parent.id)))
            .filter(text("%s = '%s'" %
                         (self._key_col, prop)))
        ).one().value
    
    def __setitem__(self, prop: str, value: Optional[str]):
        log.debug(
            'Setting %s[%s] of %d to %s',
            self.__class__.__name__,
            prop,
            self._parent.id,
            value
        )
        conn = self._session.connection()
        if prop in self:
            kwargs = {
                self._value_col:  value
            }
            conn.execute(
                update(self._table)
                .filter(text("%s = '%s'" % (self._parent_id_col, self._parent.id)))
                .filter(text("%s = '%s'" % (self._key_col, prop)))
                .values(**kwargs)
            )
        else:
            kwargs = {
                self._parent_id_col:    self._parent.id,
                self._key_col:          prop,
                self._value_col:        value
            }
            conn.execute(
                insert(self._table).values(**kwargs)
            )

    def __iter__(self) -> Iterable:
        for row in self._session.connection().execute(
            select(self._table)
            .filter("%s = '%s'" % (self._parent_id_col, self._parent.id))
        ):
            yield row[self._key_col]
    
    def items(self) -> Iterable:
        """
        Returns the properties as an iterable yielding (key, value) tuples.
        """
        for row in self._session.connection().execute(
            select(self._table)
            .filter(text("%s = '%s'" %
                         (self._parent_id_col, self._parent.id)))
        ):
            yield row[self._key_col], row[self._value_col]
    
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
        conn = self._session.connection()
        conn.execute(
            delete(self._table)
            .filter(text("%s = %s" %
                         (self._parent_id_col, self._parent.id)))
            .filter(text("%s = '%s'" %
                         (self._key_col, prop))))
        conn.commit()
