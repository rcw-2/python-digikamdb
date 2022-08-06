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
        log_create:
    """
    
    _class_function = None
    _id_column = 'id'
    
    #: Raise an Exception when ``[]`` does not find a suitable column.
    #: Otherwise, ``None`` is returned.
    _raise_on_not_found = True
    
    def __init__(
        self,
        digikam: 'Digikam',                                 # noqa: F821
        log_create: bool = True
    ):
        if log_create:
            log.debug('Creating %s', self.__class__.__name__)
        self._digikam = digikam
        self._session = self.digikam.session
        self.is_mysql = self.digikam.is_mysql
        self.Class = self.__class__._class_function(self.digikam)
        self.Class._session = self._session
        self.Class.is_mysql = self.is_mysql
        self.Class._container = self
        setattr(self, self.Class.__name__, self.Class)
    
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
        if self._raise_on_not_found:
            return self._select(**kwargs).one()
        else:
            return self._select(**kwargs).one_or_none()
    
    def _select(
        self,
        **kwargs
    ) -> '~sqlalchemy.orm.Query':                           # noqa: F821
        """
        Returns a select result for the table.
        
        Args:
            kwargs:         Keyword arguments are used as arguments for
                            :meth:`~sqlalchemy.orm.Query.filter_by`.
        Returns:
            Iterable query.
        """
        log.debug(
            '%s: Selecting %s objects with %s',
            self.__class__.__name__,
            self.Class.__name__,
            kwargs
        )

        query = self._session.query(self.Class)
        if kwargs:
            query = query.filter_by(**kwargs)
        
        return query
    
    def _insert(self, **kwargs) -> 'DigikamObject':          # noqa: F821
        """
        Inserts a new record.
        
        Args:
            kwargs: The keyword arguments are used as properties for the new record.
        Returns:
            The generated object.
        """
        log.debug(
            '%s: Creating %s object with %s',
            self.__class__.__name__,
            self.Class.__name__,
            kwargs
        )
        new = self.Class(**kwargs)
        self._session.add(new)
        return new
    
    def _delete(self, **kwargs) -> None:
        """
        Deletes rows from the table.
        
        Args:
            kwargs:         Keyword arguments are used as arguments for
                            :meth:`~sqlalchemy.orm.Query.filter_by`.
        """
        log.debug(
            '%s: Deleting %s objects with  %s',
            self.__class__.__name__,
            self.Class.__name__,
            kwargs
        )
        if not kwargs:
            raise ValueError('Objects to delete must be specified')

        self._session.execute(
            delete(self.Class)
            .filter_by(**kwargs))

