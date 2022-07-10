"""Basic class for properties"""

from typing import Iterable, Optional

from sqlalchemy import delete, func, insert, select, text, update

# TagProperties and ImageProperties have no primary key in Digikam, so
# the ORM will not work. Instead, we use derivatives of this class to
# access properties.

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
    """
    
    # Parent id column
    _parent_id_col = None
    
    # Key column
    _key_col = None
    
    # Value column
    _value_col = None
    
    def __init__(
        self,
        parent: 'DigikamObject'
    ):
        self.parent = parent
        self.table  = parent.properties_table
        self.session = parent.session
    
    def __contains__(self, prop: str) -> bool:
        return self.session.connection().execute(
            select(func.count('*'))
                .select_from(self.table)
                .filter(text("%s = '%s'" %
                                (self._parent_id_col, self.parent.id)))
                .filter(text("%s = '%s'" %
                                (self._key_col, prop)))
        ).one()[0] > 0
    
    def __getitem__(self, prop: str) -> 'TagProperty':
        return self.session.connection().execute(
            select(self.table)
                .filter(text("%s = '%s'" %
                                (self._parent_id_col, self.parent.id)))
                .filter(text("%s = '%s'" %
                                (self._key_col, prop)))
        ).one().value
    
    def __setitem__(self, prop: str, value: Optional[str]):
        conn = self.session.connection()
        if prop in self:
            kwargs = {
                self._parent.value_col:  value }
            conn.execute(
                update(self.table)
                    .filter("%s = '%s'" %
                            (self._parent_id_col, self.parent.id))
                    .filter("%s = '%s'" % (self._key_col, prop))
                    .values(**kwargs))
        else:
            kwargs = {
                self._parent_id_col:     self.parent.id,
                self._parent.key_col:    prop,
                self._parent.value_col:  value }
            conn.execute(
                insert(self.table).values(**kwargs))
        conn.commit()

    def __iter__(self) -> Iterable:
        for row in self.session.connection().execute(
            select(self.table)
                .filter("%s = '%s'" % (self._parent_id_col, self.parent.id))
        ):
            yield row[self._key_col]
    
    def items(self) -> Iterable:
        """
        Returns the properties as an iterable yielding (key, value) tuples
        """
        for row in self.session.connection().execute(
            select(self.table)
                .filter(text("%s = '%s'" %
                                (self._parent_id_col, self.parent.id)))
        ):
            yield row[self._key_col], row[self._value_col]
    
    def remove(self, prop: str):
        """Removes the given property"""
        conn = self.session.connection()
        conn.execute(
            delete(self.table)
                .filter(text("%s = %s" %
                                (self._parent_id_col, self.parent.id)))
                .filter(text("%s = '%s'" %
                                (self._key_col, prop))))
        conn.commit()
