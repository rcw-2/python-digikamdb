"""
Digikam Images
"""

import os
from typing import Any, Iterable, List, Mapping, Optional, Union

from sqlalchemy import Column, select
from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .exceptions import DigikamError


def _albumroot_class(dk: 'Digikam') -> type:
    """
    Defines the AlbumRoot class
    """
    
    class AlbumRoot(dk.base):
        """
        Digikam Album Root
        
        The following column-related properties can be directly accessed:
        
        * **id** (*int*)
        * **label** (*str*) - Label specified in Digikam
        * **status** (*int*)
        * **type** (*int*)
        * **identifier** (*str*) - Identifies the file system where the root
          is located
        * **specificPath** (*str*) - Relative directory, starts with a :file:`/`
        
        The location can be accessed with :meth:`AlbumRoot.abspath`.
        """

        __tablename__ = 'AlbumRoots'
        _albums = relationship(
            'Album',
            primaryjoin = 'foreign(Album.albumRoot) == AlbumRoot.id',
            back_populates = '_root')
        
        # Relationship to Albums
        
        @property
        def albums(self) -> List['Album']:
            """Returns the albums belonging to this root."""
            return self._albums
        
        # Other properties and methods
        
        @validates('identifier')
        def _val_identifier(self, value):
            """Deletes cached mountpoint."""
            if hasattr(self, '_mountpoint'):
                delattr(self, '_mountpoint')
            return value
        
        @property
        def mountpoint(self) -> str:
            """
            Returns the volume's mount point.
            
            The result can be modified if ``root_override`` is specified
            in the :class:`Digikam` constructor.
            """
            
            if hasattr(self, '_mountpoint'):
                return self._mountpoint
            
            # Check if we have an override option
            if self.override is not None:
                if 'ids' in self.override:
                    if self.id in self.override['ids']:
                        self._mountpoint = self.override['ids'][self.id]
                        return self._mountpoint
                    if self.identifier in self.override['ids']:
                        self._mountpoint = self.override['ids'][self.identifier]
                        return self._mountpoint
            
            vid = self.identifier
            path = '/'
            if vid.startswith('volumeid:?uuid='):
                uuid = vid[15:]
                dev = os.path.realpath(os.path.join('/dev/disk/by-uuid', uuid))
                with open('/proc/mounts', 'r') as mt:
                    for l in mt.readlines():
                        mntinfo = l.strip().split()
                        if mntinfo[0] == 'UUID=' + uuid or mntinfo[0] == dev:
                            path = mntinfo[1]
                            break
            
            if os.path.isdir(os.path.join(
                path,
                self.specificPath.lstrip('/')
            )):
                self._mountpoint = path
                return path
            
            raise DigikamError('No path found for ' + vid)
                        
        @property
        def abspath(self) -> str:
            """
            Returns the album root's absolute path.
            
            The result can be modified if ``root_override`` is specified
            in the :class:`Digikam` constructor.
            """
            
            override = self.override
            if override is not None:
                if 'paths' in override:
                    if self.id in override['paths']:
                        return override['paths'][self.id]
                    path = self.identifier + self.specificPath
                    if path in override['paths']:
                        return override['paths'][path]
                
            return os.path.abspath(os.path.join(
                self.mountpoint,
                self.specificPath.lstrip('/')))
    
    return AlbumRoot


class AlbumRoots(DigikamTable):
    """
    Offers access to the album roots in the Digikam instance.
    
    ``AlbumRoots`` represents all album roots present in the Digikam database.
    It is usually accessed through the :class:`~digikamdb.connection.Digikam`
    property :attr:`~digikamdb.connection.Digikam.albumroots`.
    
    Usage:
    
    .. code-block:: python
        
        dk = Digikam(...)
        myroot = dk.albumroots[2]                           # by id
        for root in dk.albumroots:                          # iterate
            print(root.relativePath)
    
    Parameters:
        parent:     Digikam object for access to database and other classes.
    Digikam albums
    
    Parameters:
        parent:     :class:`Digikam` object
        override:   Dict containing override information
    """
    
    class_function = _albumroot_class
    
    def __init__(
        self,
        parent: 'Digikam',
        override: Optional[Mapping] = None
    ):
        super().__init__(parent)
        self.Class.override = override


