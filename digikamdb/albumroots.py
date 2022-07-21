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
from .exceptions import DigikamFileError


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
        
        .. todo:: What do the status and type columns mean?
        
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
            
            raise DigikamFileError(
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
    
    @classmethod
    def _get_mountpoints(cls) -> Mapping[str, str]:
        if hasattr(cls, '_mountpoints'):
            return cls._mountpoints
        
        mountpoints = {}
        with open('/proc/mounts', 'r') as mt:
            for line in mt.readlines():
                dev, dir, fstype, options = line.strip().split(maxsplit=3)
                # Resolve /dev/root for some installations
                if dev == '/dev/root':
                    from digikamdb.albumroots import _substitute_device
                    dev = _substitute_device(dev)
                mountpoints[dir] = dev
        
        cls._mountpoints = mountpoints
        return mountpoints
    
    @classmethod
    def _get_uuids(cls) -> Mapping[str, str]:
        if hasattr(cls, '_uuids'):
            return cls._uuids
        
        uuids = {}
        for f in os.scandir('/dev/disk/by-uuid'):
            if f.is_symlink():
                uuids[os.path.realpath(f.path)] = f.name
        
        cls._uuids = uuids
        return uuids
        
    def add(
        self,
        path: str,
        label: Optional[str] = None,
        status: int = 0,
        type_: int = 1,
        check_dir: bool = True,
        use_uuid: bool = True
    ) -> 'AlbumRoot':                                       # noqa: F821
        """
        Adds a new album root.
        
        If check_dir is False, the identifier will be path.
        
        Args:
            path:       Path to new album root.
            check_dir:  Check if the directory exists and is not a subdir
                        of another album root or vice versa.
            status:     The new root's status.
            use_uuid:   Use UUID of filesystem as identifier.
        Returns:
            The newly created AlbumRoot object.
        """
        if check_dir:
            if not os.path.isdir(path):
                raise DigikamFileError('Directory %s not found' % path)
            
            for r in self:
                if os.path.commonpath(path, r.abspath) == r.abspath:
                    raise DigikamFileError(
                        '%s is a subdir of %s (albumroot %s)' % (
                            path, r.abspath, r.label
                        )
                    )
                if os.path.commonpath(path, r.abspath) == path:
                    raise DigikamFileError(
                        '%s (albumroot %s) is a subdir of %s' % (
                            r.abspath, r.label, path
                        )
                    )
                        
        
        if use_uuid:
            mountpoints = self._get_mountpoints()
            uuids = self._get_uuids()
            
            mpt = os.path.realpath(path)
            while True:
                while not os.path.ismount(mpt):
                    mpt = os.path.dirname(mpt)
                if mpt in mountpoints:
                    dev = mountpoints[mpt]
                    if dev in uuids:
                        ident = 'volumeid:?uuid=' + uuids[dev]
                        spath = '/' + os.path.relpath(path, mpt).rstrip('.')
                        break
                if mpt == '/':
                    raise DigikamFileError('No mountpoint found for ' + path)
        
        else:
            ident = 'volumeid:?path=' + path
            spath = '/'
        
        return self._insert(
            label = label,
            status = 0,
            type = 1,
            identifier = ident,
            specificPath = spath
        )
            

_device_regex = re.compile(r'(sd[a-z](\n+)?|nvme\d+n\d+(p\d+)?)')


# Substitutes the standard device in /dev for the given device
def _substitute_device(dev: str) -> str:
    dev = os.path.realpath(dev)
    st1 = os.stat(dev)
    if not stat.S_ISBLK(st1.st_mode):
        log.warning('%s is not a block device', dev)
        return dev

    with os.scandir('/dev') as sc:
        for f in sc:
            if not _device_regex.match(f.name):
#                log.debug('%s does not match disk regex', f.name)
                continue
            st2 = f.stat()
            if not stat.S_ISBLK(st2.st_mode):
                log.debug('%s is not a block device', f.path)
                continue
            if st1.st_rdev != st2.st_rdev:
                log.debug(
                    'Device numbers differ between %s(%d) and %s(%d)',
                    dev,
                    st1.st_rdev,
                    f.path,
                    st2.st_rdev
                )
                continue
            if f.path == dev:
                log.debug('Replacing %s with %s', dev, f.path)
                return f.path
    
    log.warning('No replacement device found for %s', dev)
    return dev


