"""
Provides access to Digikam album roots
"""

import logging
import os
import re
import stat
import sys
from warnings import warn
from typing import Dict, Iterable, Mapping, Optional

from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .exceptions import DigikamFileError, DigikamVersionError
from .types import AlbumRootStatus as Status, AlbumRootType as Type


log = logging.getLogger(__name__)


def _albumroot_class(dk: 'Digikam') -> type:                # noqa: F821, C901
    """
    Defines the :class:`~digikamdb._sqla.AlbumRoot` class
    """
    
    class AlbumRoot(dk.base):
        """
        Digikam Album Root
        
        The location can be accessed with :attr:`abspath`.
        
        .. versionchanged:: 0.3.5
            *   ``path in root`` checks if a path is a subdirectory (and thus a
                Digikam album) of the album root. The reverse is checked by
                :meth:`issubdir`.
        
        See also:
            * Class :class:`~digikamdb.albumroots.AlbumRoots`
        """

        __tablename__ = 'AlbumRoots'
        _albums = relationship(
            'Album',
            primaryjoin = 'foreign(Album._albumRoot) == AlbumRoot._id',
            back_populates = '_root',
            lazy = 'dynamic')
        
        # Relationship to Albums
        
        @property
        def albums(self) -> Iterable['Album']:                  # noqa: F821
            """The albums belonging to this root (no setter)"""
            return self._albums
        
        # column properties
        
        @property
        def id(self) -> int:
            """The album root's id (read-only)"""
            return self._id
        
        @property
        def label(self) -> str:
            """The album root's label"""
            return self._label
        
        @label.setter
        def label(self, value):
            self._label = value
        
        @property
        def status(self) -> Status:
            """
            The album root's status (read-only)
            
            This property is dynamically set by Digikam and only valid when
            Digikam is running.
            """
            return Status(self._status)
        
        @property
        def type(self) -> Type:
            """The album root's type (hardwired, removable or network)"""
            return Type(self._type)
        
        @type.setter
        def type(self, value):
            self._type = value
        
        @validates('_status', '_type')
        def _convert_to_int(self, key, value):
            return int(value)
        
        @property
        def identifier(self) -> str:
            """
            The album root's identifier
            
            This often contains the UUID of the file system that containst the
            album root.
            """
            return self._identifier
        
        @identifier.setter
        def identifier(self, value):
            self._identifier = value
        
        @validates('_identifier')
        def _val_identifier(self, key: str, value: str):
            """Deletes cached mountpoint."""
            if hasattr(self, '_mountpoint'):
                delattr(self, '_mountpoint')
            if hasattr(self, '_parsed_identifier_data'):
                delattr(self, '_parsed_identifier_data')
            return value

        @property
        def specificPath(self) -> str:
            """
            The album root's path relative to :attr:`~AlbumRoot.identifier`,
            starting with ``/``
            """
            return self._specificPath
        
        @specificPath.setter
        def specificPath(self, value):
            self._specificPath = value
        
        @property
        def caseSensitivity(self) -> bool:
            """
            Indicates if this album root is case sensitive.
            
            Raises:
                DigikamVersionError:    If DBVersion < 16
            
            .. versionadded:: 0.2.2
            
            .. todo:: Take ``caseSensitivity`` into account when accessing images.
            """
            if sys.platform == 'win32':
                return False
            if self.digikam.db_version < 16:
                return True
            return self._caseSensitivity != 0

        # Other properties and methods
        
        def __contains__(self, path: str) -> bool:
            path = os.path.abspath(path)
            abspath = self._cmppath
            
            if sys.platform == 'win32':
                # case-insensitive compare
                path = path.lower()
                return os.path.commonpath([abspath, path]) == abspath
            
            if self.caseSensitivity:
                return os.path.commonpath([abspath, path]) == abspath
            
            # OS case-sensitive, filesystem case-insensitive:
            # Mountpoint needs exact match, rest case-insensitive
            
            if os.path.commonpath([self.mountpoint, path]) != self.mountpoint:
                # path not inside mountpoint
                return False
            
            path = os.path.join(
                self.mountpoint,
                os.path.relpath([path, self.mountpoint]).lower()
            )
            return os.path.commonpath([abspath, path]) == abspath
        
        def issubdir(self, path: str) -> bool:
            """
            Checks if album root is a subdir of `path`.
            
            .. versionadded:: 0.3.5
            """
            path = os.path.abspath(path)
            abspath = self._cmppath
            
            if sys.platform == 'win32':
                path = path.lower()
                return os.path.commonpath(abspath, path) == path
            
            if self.caseSensitivity:
                return os.path.commonpath([abspath, path]) == path
            
            common = os.path.commonpath([path, self.mountpoint])
            if common == path:
                return True
            if common != self.mountpoint:
                return False
            
            path = os.path.join(
                self.mountpoint,
                os.path.relpath(path, self.mountpoint).lower()
            )
            return os.path.commonpath([abspath, path]) == path
        
        @property
        def _cmppath(self) -> str:
            """:attr:`abspath` converted to lowercase as needed by system"""
            if sys.platform == 'win32':
                return self.abspath.lower()
            
            if not self.caseSensitivity:
                return os.path.join(
                    self.mountpoint,
                    self.specificPath.lstrip('/').lower()
                )
            
            return self.abspath
        
        @property
        def _parsed_identifier(self) -> Dict[str, str]:
            """Returns a parsed version of the identifier"""
            if not hasattr(self, '_parsed_identifier_data'):
                schema, params = self.identifier.split(':?', 1)
                data = {'schema': schema}
                for param in params.split('&'):
                    key, value = param.split('=', 1)
                    data[key] = value
                self._parsed_identifier_data = data
            return self._parsed_identifier_data
        
        @property
        def mountpoint(self) -> str:
            """
            The volume's mount point (read-only)
            
            The result can be modified if ``root_override`` is specified
            in the :class:`Digikam` constructor.
            
            .. versionchanged:: 0.3.4
                * Works if :attr:`identifier` contains multiple parameters.
                * Process ``mountpath`` parameter.
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
            
            if sys.platform != 'linux':
                warn(
                    "Mountpoint detection has only been tested on Linux and will "
                    "probably not work on other operating systems. You can avoid "
                    "related errors by passing a 'root_override' parameter to "
                    "Digikam()",
                    RuntimeWarning
                )
            
            path = None
            
            # Determine path by 
            if 'uuid' in self._parsed_identifier:
                dev = os.path.realpath(os.path.join(
                    '/dev/disk/by-uuid',
                    self._parsed_identifier['uuid']
                ))
                with open('/proc/mounts', 'r') as mt:
                    for line in mt.readlines():
                        mdev, mdir, moptions = line.strip().split(maxsplit=2)
                        
                        if mdev == '/dev/root':
                            mdev = _substitute_device(mdev)
                        
                        if (
                            mdev == 'UUID=' + self._parsed_identifier['uuid'] or
                            mdev == dev
                        ):
                            path = mdir
                            break
            
            if path is None:
                path = self._parsed_identifier.get('path')
            
            if path is None:
                path = self._parsed_identifier.get('mountpath')
            
            if path is not None and os.path.isdir(path):
                self._mountpoint = path
                log.debug(
                    'Setting mountpoint for %s to %s',
                    self.identifier,
                    self._mountpoint
                )
                return path
            
            raise DigikamFileError(
                'No path found for {0}, candidate {1}'.format(self.identifier, path)
            )
                        
        @property
        def abspath(self) -> str:
            """
            The album root's absolute path (read-only)
            
            The result can be modified if ``root_override`` is specified
            in the :class:`Digikam` constructor.
            
            versionchanged:: 0.3.5
                Converted to lowercase for case-insensitive roots (except mountpoint).
            """
            
            override = self.override
            if override is not None:
                if 'paths' in override:
                    if self.id in override['paths']:
                        log.debug('Overriding path')
                        return override['paths'][self.id]
                    path = (self.identifier + self.specificPath).rstrip('/')
                    if path in override['paths']:
                        log.debug('Overriding path')
                        return override['paths'][path]
            
            if self.caseSensitivity:
                relpath = self.specificPath.lstrip('/')
            else:
                relpath = self.specificPath.lstrip('/').lower()
            return os.path.abspath(os.path.join(self.mountpoint, relpath))
        
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
        digikam:    :class:`~digikamdb.conn.Digikam` object
        override:   Dict containing override information
                    (:class:`~digikamdb.conn.Digikam` passes its parameter
                    ``root_override`` here)
    
    See also:
        * Class :class:`~_sqla.AlbumRoot`
    """
    
    _class_function = _albumroot_class
    
    def __init__(
        self,
        digikam: 'Digikam',                                  # noqa: F821
        override: Optional[Mapping] = None
    ):
        super().__init__(digikam)
        self.Class.override = override
        if override is not None:
            log.debug('Root override specified')
    
    @classmethod
    def _get_mountpoints(cls) -> Mapping[str, str]:
        if hasattr(cls, '_mountpoints'):
            return cls._mountpoints
        
        log.debug('Reading mountpoints')
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
        
        log.debug('Reading disk UUIDs')
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
        status: Status = Status.LocationAvailable,
        type_: Type = Type.UndefinedType,
        check_dir: bool = True,
        use_uuid: bool = True
    ) -> 'AlbumRoot':                                       # noqa: F821
        """
        Adds a new album root.
        
        If check_dir is False, the identifier will be of ``path=`` type, and
        ``use_uuid`` is ignored. The :attr:`~AlbumRoot.identifier` and 
        :attr:`~AlbumRoot.relativePath` are derifed from ``path``.
        
        To add albums and images in the new album root, start Digikam and scand
        for new objects.
        
        Args:
            path:       Path to new album root.
            label:      Label of the new album root.
            check_dir:  Check if the directory exists and is not a subdir
                        of another album root or vice versa.
            status:     The new root's status.
            use_uuid:   Use UUID of filesystem as identifier. If false, the
                        is used as identifier.
        Returns:
            The newly created AlbumRoot object.
        
        .. note::
            The :class:`~digikamdb.conn.Digikam` parameter ``root_override``
            is ignored by this method.
        """
        log.debug('Adding album root for dir %s (%s)', path, label)
        
        if check_dir:
            if not os.path.isdir(path):
                raise DigikamFileError('Directory %s not found' % path)
            
            for r in self:
                log.debug('Checking overlap with root %d (%s)', r.id, r.label)
                if os.path.commonpath([path, r.abspath]) == r.abspath:
                    raise DigikamFileError(
                        '%s is a subdir of %s (albumroot %s)' % (
                            path, r.abspath, r.label
                        )
                    )
                if os.path.commonpath([path, r.abspath]) == path:
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
                    log.debug('%s is not a mountpoint', mpt)
                    mpt = os.path.dirname(mpt)
                if mpt in mountpoints:
                    dev = mountpoints[mpt]
                    if dev in uuids:
                        ident = 'volumeid:?uuid=' + uuids[dev]
                        spath = '/' + os.path.relpath(path, mpt).rstrip('.')
                        break
                if mpt == '/':                              # pragma: no cover
                    raise DigikamFileError('No mountpoint found for ' + path)
        
        else:
            ident = 'volumeid:?path=' + path
            spath = '/'
        
        log.debug('Creating mountpoint with ident=%s and spath=%s', ident, spath)
        return self._insert(
            _label = label,
            _status = Status.LocationAvailable,
            _type = 1,
            _identifier = ident,
            _specificPath = spath
        )
            

_device_regex = re.compile(r'(sd[a-z]\d*|nvme\d+n\d+(p\d+)?)')


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
                # log.debug('%s does not match disk regex', f.name)
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
            log.debug('Replacing %s with %s', dev, f.path)
            return f.path
    
    log.warning('No replacement device found for %s', dev)
    return dev


