"""
Provides access to Digikam album roots
"""

import logging
import os
import re
import stat
from typing import List, Mapping, Optional

from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .exceptions import DigikamError


log = logging.getLogger(__name__)


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
                        log.debug(
                            'Root override: setting mountpoint of %d to %s',
                            self.id,
                            self._mountpoint
                        )
                        return self._mountpoint
                    if self.identifier in self.override['ids']:
                        self._mountpoint = self.override['ids'][self.identifier]
                        log.debug(
                            'Root override: setting mountpoint for %s to %s',
                            self.identifier,
                            self._mountpoint
                        )
                        return self._mountpoint
            
            vid = self.identifier
            path = '/'
            if vid.startswith('volumeid:?uuid='):
                uuid = vid[15:]
                dev = os.path.realpath(os.path.join('/dev/disk/by-uuid', uuid))
                with open('/proc/mounts', 'r') as mt:
                    for line in mt.readlines():
                        mdev, mdir, moptions = line.strip().split(maxsplit=2)
                        
                        if mdev == '/dev/root':
                            mdev = _substitute_device(mdev)
                        
                        if mdev == 'UUID=' + uuid or mdev == dev:
                            path = mdir
                            break
            
            if vid.startswith('volumeid:?path='):
                path = vid[15:]
            
            if os.path.isdir(path):
                self._mountpoint = path
                log.debug(
                    'Setting mountpoint for %s to %s',
                    self.identifier,
                    self._mountpoint
                )
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
                        log.debug('Overriding path')
                        return override['paths'][self.id]
                    path = self.identifier + self.specificPath
                    if path in override['paths']:
                        log.debug('Overriding path')
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


_device_regex = re.compile(r'(sd[a-z](\n+)?|nvme\d+n\d+(p\d+)?)')


# Substitutes the standard device in /dev for the given device
def _substitute_device(dev: str) -> str:
    dev = os.path.realpath(dev)
    st1 = os.stat(dev)
    if not stat.S_ISBLK(st1.st_mode):
        log.warning('%s is not a device', dev)
        return dev

    with os.scandir('/dev') as sc:
        for f in sc:
            if not _device_regex.match(f.name):
                continue
            st2 = f.stat()
            if not stat.S_ISBLK(st2.st_mode):
                continue
            if st1.st_rdev != st2.st_rdev:
                continue
            if f.path == dev:
                log.debug(
                    'Replacing %s with %s',
                    dev,
                    f.path
                )
                return f.path
    
    log.warning('No replacement device found for %s', dev)
    return dev


