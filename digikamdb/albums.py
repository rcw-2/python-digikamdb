"""
Digikam Albums
"""

import logging
import os
from datetime import datetime
from typing import List, Union

from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import MultipleResultsFound

from .table import DigikamTable
from .exceptions import DigikamDataIntegrityError


log = logging.getLogger(__name__)


def _album_class(dk: 'Digikam') -> type:                    # noqa: F821
    """
    Defines the Album class
    """
    
    class Album(dk.base):
        """
        Digikam Album
        
        The following column-related properties can be directly accessed:
        
        * **id** (*int*)
        * **relativePath** (*str*) - Path relative to the album root
          (starts with :file:`/`)
        * **date** (*date*)?
        * **caption** (*str*)
        * **collection** (*str*)
        
        See also:
            * Class :class:`~digikamdb.albums.Albums`
        
        .. todo::
            * Function to sort images in an album
            * __contains__ function (image in album)
        """

        __tablename__ = 'Albums'
        
        _root = relationship(
            'AlbumRoot',
            primaryjoin = 'foreign(Album._albumRoot) == AlbumRoot._id',
            back_populates = '_albums')
        _iconObj = relationship(
            'Image',
            primaryjoin = 'foreign(Album._icon) == Image._id',
            uselist = False)
        _images = relationship(
            'Image',
            primaryjoin = 'foreign(Image._album) == Album._id',
            back_populates = '_albumObj',
            lazy = 'dynamic')
        
        # Relationship to AlbumRoot
        
        @property
        def root(self) -> 'AlbumRoot':                      # noqa: F821
            """Returns the album's root"""
            return self._root
        
        # Relationships to Images
        
        @property
        def icon(self) -> 'Image':                          # noqa: F821
            """Returns the album's icon"""
            return self._iconObj
        
        @property
        def images(self) -> List['Image']:                  # noqa: F821
            """Returns the album's images"""
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
        def date(self) -> datetime:
            """The album's date (read-only)"""
            return self._date
        
        @property
        def caption(self) -> str:
            """The album's caption"""
            return self._caption
        
        @caption.setter
        def caption(self, value):
            self._caption = value
        
        @property
        def collection(self) -> str:
            """The album's collection"""
            return self._collection
        
        @collection.setter
        def collection(self, value):
            self._collection = value
        
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
        parent:     Digikam object for access to database and other classes.
    
    See also:
        * Class :class:`~_sqla.Album`
    """
    
    _class_function = _album_class
    
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
            exact:  If true, look for exactly one album.
        Returns:
            The found albums. If ``exact == True``, the album object is
            returned, or ``None`` if it was not found. If ``exact == False``,
            returns a list with the found albums.
        Raises:
            DigikamDataIntegrityError
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
                except MultipleResultsFound:
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


