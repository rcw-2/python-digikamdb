"""
Basic Digikam Table Class
"""

import logging
from typing import Iterable, Optional

from sqlalchemy import delete, select, text


log = logging.getLogger(__name__)


class DigikamTable:
    """
    An abstract base class for table classes
    
    Provides some low-level methods for accessing data:
    
    * Members can be accessed by id via ``object[id]``.
    * Class is iterable, returning all rows of the table.
    * Some internal functionality
    
    Parameters:
        parent:     ``Digikam`` object
    """
    
    _class_function = None
    
    def __init__(self, parent: 'Digikam'):                  # noqa: F821
        self.parent = parent
        self.engine = self.parent.engine
        self.session = self.parent.session
        self.is_mysql = self.parent.is_mysql
        self.Class = self.__class__._class_function(self.parent)
        self.Class.engine = self.engine
        self.Class.session = self.session
        self.Class.is_mysql = self.is_mysql
        
    def __iter__(self) -> Iterable:
        return self.session.scalars(select(self.Class))
    
    def __getitem__(self, key: int) -> 'DigikamObject':     # noqa: F821
        return self.session.scalars(
            select(self.Class).filter_by(id = key)
        ).one()
    
    def _select(
        self,
        where_clause: Optional[str] = None,
        **kwargs
    ) -> '~sqlalchemy.engine.ScalarResult':                 # noqa: F821
        """
        Returns a select result for the table.
        
        Args:
            where_clause:   Contains a SQL WHERE clause, processed by
                            :func:`~sqlalchemy.sql.expression.text` and
                            :meth:`~sqlalchemy.orm.Query.where`.
            kwargs:         Other keyword arguments are used as arguments for
                            :meth:`~sqlalchemy.orm.Query.filter_by`.
        Returns:
            Iterable query result.
        """
        log.debug(
            'Selecting %s objects with %s and %s',
            self.__class__.__name__,
            where_clause,
            kwargs
        )
        if where_clause:
            if kwargs:
                return self.session.scalars(
                    select(self.Class)
                    .where(text(where_clause))
                    .filter_by(**kwargs))
            else:
                return self.session.scalars(
                    select(self.Class)
                    .where(text(where_clause)))
        else:
            if kwargs:
                return self.session.scalars(
                    select(self.Class)
                    .filter_by(**kwargs))
            else:
                return self.session.scalars(
                    select(self.Class))
    
    def _insert(self, **kwargs) -> 'DigikamObject':          # noqa: F821
        """
        Inserts a new record.
        
        Args:
            kwargs: The keyword arguments are used as properties for the new record.
        Returns:
            The generated object.
        """
        log.debug(
            'Creating %s object with %s',
            self.__class__.__name__,
            kwargs
        )
        new = self.Class(**kwargs)
        self.session.add(new)
#        self.session.commit()
        return new
    
    def _delete(
        self,
        where_clause: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Deletes rows from the table.
        
        Args:
            where_clause:   Contains a SQL WHERE clause, processed by
                            :func:`~sqlalchemy.sql.expression.text` and
                            :meth:`~sqlalchemy.orm.Query.where`.
            kwargs:         Other keyword arguments are used as arguments for
                            :meth:`~sqlalchemy.orm.Query.filter_by`.
        """
        log.debug(
            'Deleting %s objects with %s and %s',
            self.__class__.__name__,
            where_clause,
            kwargs
        )
        if where_clause:
            if kwargs:
                self.session.execute(
                    delete(self.Class)
                    .where(text(where_clause))
                    .filter_by(**kwargs))
            else:
                self.session.execute(
                    delete(self.Class)
                    .where(text(where_clause)))
        else:
            if kwargs:
                self.session.execute(
                    delete(self.Class)
                    .filter_by(**kwargs))
            else:
                self.session.execute(
                    delete(self.Class))

