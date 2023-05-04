"""
Digikam Albums
"""

import logging
import os
from datetime import date, datetime
from typing import List, Optional, Union

from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import MultipleResultsFound

from .table import DigikamTable
from .exceptions import DigikamDataIntegrityError, DigikamVersionError


log = logging.getLogger(__name__)


def _album_class(dk: 'Digikam') -> type:                    # noqa: F821
    """
    Defines the Album class
    """
    
    if not dk.is_mysql:
        from sqlalchemy.dialects import sqlite
    
    class Album(dk.base):
        """
        Represents a row in the table ``Albums``.
        
        See also:
            * Class :class:`~digikamdb.albums.Albums`
        """

        __tablename__ = 'Albums'
        
        if (not dk.is_mysql) and (dk.db_version >= 14):
            _modificationDate = Column(
                'modificationDate',
                sqlite.DATETIME(
                    storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                    regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)')
            )
        
        _root = relationship(
            'AlbumRoot',
            primaryjoin = 'foreign(Album._albumRoot) == AlbumRoot._id',
            back_populates = '_albums')
        _iconObj = relationship(
            'Image',
            primaryjoin = 'foreign(Album._icon) == Image._id',
            viewonly = True,
            uselist = False)
        _images = relationship(
            'Image',
            primaryjoin = 'foreign(Image._album) == Album._id',
            back_populates = '_albumObj',
            lazy = 'dynamic')
        
        # Relationship to AlbumRoot
        
        @property
        def root(self) -> 'AlbumRoot':                      # noqa: F821
            """The album collection's root object (no setter)"""
            return self._root
        
        # Relationships to Images
        
        @property
        def icon(self) -> Optional['Image']:                # noqa: F821
            """The album's icon, if set"""
            return self._iconObj
        
        @icon.setter
        def icon(self, value: Union['Image', int]):         # noqa: F821
            if isinstance(value, int):
                value = self.digikam.images[value]
            self._iconObj = value
        
        @property
        def images(self) -> List['Image']:                  # noqa: F821
            """The album's images (no setter)"""
            return self._images
        
        # column properties
        
        @property
        def id(self) -> int:
            """The album's id (read-only)"""
            return self._id
        
        @property
        def relativePath(self) -> str:
            """The album's path relative to the root (read-only)"""
            return self._relativePath
        
        @property
        def date(self) -> date:
            """
            The album's date (read-only)
            
            The date can be set in Digikam
            """
            return self._date
        
        @property
        def caption(self) -> str:
            """The album's caption (description)"""
            return self._caption
        
        @caption.setter
        def caption(self, value):
            self._caption = value
        
        @property
        def collection(self) -> str:
            """
            The album's collection
            
            This property is named *Category* in Digikam.
            """
            return self._collection
        
        @collection.setter
        def collection(self, value):
            self._collection = value
        
        @property
        def modificationDate(self) -> datetime:
            """
            The album's modification date (read-only)
            
            Raises:
                DigikamVersionError:    If DBVersion < 14
            
            .. versionadded:: 0.2.2
            """
            if self.digikam.db_version < 14:
                raise DigikamVersionError(
                    'modificationDate is present in DBVersion >= 14'
                )
            return self._modificationDate
        
        # Other properties and methods
        
        @property
        def abspath(self) -> str:
            """The album folder's absolute path (read-only)"""
            if self.relativePath == '/':
                return self.root.abspath
            return os.path.abspath(os.path.join(
                self.root.abspath,
                self.relativePath.lstrip('/')))
        
    return Album
    
    
class Albums(DigikamTable):
    """
    Offers access to the albums in the Digikam instance.
    
    ``Albums`` represents all albums present in the Digikam database. It is
    usually accessed through the :class:`~digikamdb.connection.Digikam`
    property :attr:`~digikamdb.connection.Digikam.albums`.
    
    Usage:
    
    .. code-block:: python
        
        dk = Digikam(...)
        myalbum = dk.albums[42]                             # by id
        for album in dk.albums:                             # iterate
            print(album.relativePath)
    
    Parameters:
        digikam:    Digikam object for access to database and other classes.
    
    See also:
        * Class :class:`~_sqla.Album`
    """
    
    _class_function = _album_class
    
    def __init__(self, digikam: 'Digikam'):                 # noqa: F821
        super().__init__(digikam)
    
    def find(                                               # noqa: C901
        self,
        path: Union[str, bytes, os.PathLike],
        exact: bool = False,
    ) -> Union['Album', List['Album']]:                     # noqa: F821
        """
        Finds albums by path name.
        
        Args:
            path:   Path to album(s). Can be given as any type that the
                    :mod:`os.path` functions understand.
            exact:  If true, look for exactly one album. If false, and ``path``
                    contains subdirectories, these are also returned.
        Returns:
            The found albums. If ``exact == True``, the album object is
            returned, or ``None`` if it was not found. If ``exact == False``,
            returns a list with the found albums.
        Raises:
            DigikamDataIntegrityError: Database contains overlapping roots.
        """
        log.debug(
            'Albums: searching for %s%s',
            path,
            ' (exact)' if exact else ''
        )
        abspath = os.path.abspath(path)
        roots_over = []
        roots_under = []
        for r in self.digikam.albumRoots:
            if os.path.commonpath([r.abspath, abspath]) == r.abspath:
                log.debug('Root %d (%s) is a parent dir', r.id, r.abspath)
                roots_over.append(r)
            if (
                os.path.commonpath([r.abspath, abspath]) == abspath
                and r.abspath != abspath
            ):
                log.debug('Root %d (%s) is a subdir', r.id, r.abspath)
                roots_under.append(r)
        
        # In these cases, the same album can exist in multiple roots.
        # Giving up...
        if (roots_over and roots_under) or (len(roots_over) > 1):
            raise DigikamDataIntegrityError(
                'Database contains overlapping album roots'
            )
        
        # Exact matches are not possible in these cases:
        if exact:
            if not roots_over:
                return None
            if roots_under:
                return None

        res = []
        
        if roots_over:
            root = roots_over[0]
            rpath = '/' + os.path.relpath(abspath, root.abspath).rstrip('.')
            
            if exact:
                try:
                    log.debug('Looging for album %s in root %d', rpath, root.id)
                    return root.albums.filter_by(_relativePath = rpath).one_or_none()
                # Multiple results should not occur...
                except MultipleResultsFound:                # pragma: no cover
                    raise DigikamDataIntegrityError(
                        'Database contains overlapping album roots'
                    )
            
            # Look for matching directories:
            log.debug('Searching for %s in root %d', rpath+'%', root.id)
            for al in self._select(_albumRoot = root.id).where(
                self.Class._relativePath.like(rpath + '%')
            ):
                if os.path.commonpath([al.abspath, abspath]) == abspath:
                    res.append(al)
        
        if roots_under:
            for r in roots_under:
                log.debug('Adding albums from root %d', r.id)
                res.extend(r.albums)
        
        return res


