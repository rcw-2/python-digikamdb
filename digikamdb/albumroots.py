"""
Provides access to Digikam album roots
"""

import os
import re
from typing import List, Mapping, Optional

from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .exceptions import DigikamError


def _albumroot_class(dk: 'Digikam') -> type:                # noqa: F821, C901
    """
    Defines the :class:`~digikamdb._sqla.AlbumRoot` class
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
        
        The location can be accessed with :attr:`abspath`.
        
        See also:
            * Class :class:`~digikamdb.albumroots.AlbumRoots`
        """

        __tablename__ = 'AlbumRoots'
        _albums = relationship(
            'Album',
            primaryjoin = 'foreign(Album.albumRoot) == AlbumRoot.id',
            back_populates = '_root')
        
        # Relationship to Albums
        
        @property
        def albums(self) -> List['Album']:                  # noqa: F821
            """Returns the albums belonging to this root."""
            return self._albums
        
        # Other properties and methods
        
        @validates('identifier')
        def _val_identifier(self, key: str, value: str):
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
                    for line in mt.readlines():
                        mdev, mdir, moptions = line.strip().split(maxsplit=2)
                        if mdev == 'UUID=' + uuid or mdev == dev:
                            path = mdir
                            break
                        if mdev == '/dev/root':
                            st1 = os.stat(mdev)
                            with os.scandir('/dev') as sc:
                                for f in sc:
                                    if not re.match(r'sd', f.name):
                                        continue
                                    st2 = f.stat()
                                    if st1.st_dev != st2.st_dev:
                                        continue
                                    if f.path == dev:
                                        path = mdir
                                        break
                        
            if os.path.isdir(path):
                self._mountpoint = path
                return path
            
            raise DigikamError(
                'No path found for {0}, candidate {1}'.format(vid, path)
            )
                        
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
        parent:     :class:`~digikamdb.conn.Digikam` object
        override:   Dict containing override information
    
    See also:
        * Class :class:`~_sqla.AlbumRoot`
    """
    
    _class_function = _albumroot_class
    
    def __init__(
        self,
        parent: 'Digikam',                                  # noqa: F821
        override: Optional[Mapping] = None
    ):
        super().__init__(parent)
        self.Class.override = override


