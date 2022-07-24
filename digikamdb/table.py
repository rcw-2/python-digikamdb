"""
Basic Digikam Table Class
"""

import logging
from typing import Any, Iterable, Optional, Union

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
        digikam:     ``Digikam`` object
    """
    
    _class_function = None
    _id_column = 'id'
    
    def __init__(self, digikam: 'Digikam'):                 # noqa: F821
        log.debug('Creating %s', self.__class__.__name__)
        self._digikam = digikam
        self._session = self.digikam.session
        self.is_mysql = self.digikam.is_mysql
        self.Class = self.__class__._class_function(self.digikam)
        self.Class._session = self._session
        self.Class.is_mysql = self.is_mysql
        self.Class._container = self
    
    @property
    def digikam(self) -> 'Digikam':                         # noqa: F821
        """
        Returns digikam object.
        
        For Prope
        """
        return self._digikam
    
    def __iter__(self) -> Iterable:
        yield from self._select()
    
    def __contains__(self, key: str) -> bool:
        kwargs = { self._id_column: key }
        return self._select(**kwargs).one_or_none() is not None
    
    def __getitem__(self, key: Any) -> 'DigikamObject':     # noqa: F821
        kwargs = { self._id_column: key }
        return self._select(**kwargs).one()
    
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
                return self._session.scalars(
                    select(self.Class).where(text(where_clause)).filter_by(**kwargs))
            else:
                return self._session.scalars(
                    select(self.Class).where(text(where_clause)))
        else:
            if kwargs:
                return self._session.scalars(
                    select(self.Class).filter_by(**kwargs))
            else:
                return self._session.scalars(
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
        self._session.add(new)
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
        
        .. todo:: Do we need the where clause?
        """
        log.debug(
            'Deleting %s objects with %s and %s',
            self.__class__.__name__,
            where_clause,
            kwargs
        )
        if where_clause:
            if kwargs:
                self._session.execute(
                    delete(self.Class)
                    .where(text(where_clause))
                    .filter_by(**kwargs))
            else:
                self._session.execute(
                    delete(self.Class)
                    .where(text(where_clause)))
        else:
            if kwargs:
                self._session.execute(
                    delete(self.Class)
                    .filter_by(**kwargs))
            else:
                self._session.execute(
                    delete(self.Class))

