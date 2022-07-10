"""
Digikam Albums
"""

import os
from typing import List

from sqlalchemy.orm import relationship

from .table import DigikamTable

  
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
        
        """

        __tablename__ = 'Albums'
        
        _root = relationship(
            'AlbumRoot',
            primaryjoin = 'foreign(Album.albumRoot) == AlbumRoot.id',
            back_populates = '_albums')
        _icon = relationship(
            'Image',
            primaryjoin = 'foreign(Album.icon) == Image.id')
        _images = relationship(
            'Image',
            primaryjoin = 'foreign(Image.album) == Album.id',
            back_populates = '_album')
        
        # Relationship to AlbumRoot
        
        @property
        def root(self) -> 'AlbumRoot':                      # noqa: F821
            """Returns the album's root"""
            return self._root
        
        # Relationships to Images
        
        @property
        def iconImage(self) -> 'Image':                     # noqa: F821
            """Returns the album's icon"""
            return self._icon
        
        @property
        def images(self) -> List['Image']:                  # noqa: F821
            """Returns the album's images"""
            return self._images
        
        # Other properties and methods
        
        @property
        def abspath(self) -> str:
            """Returns the album folder's absolute path"""
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
    """
    
    class_function = _album_class
    
