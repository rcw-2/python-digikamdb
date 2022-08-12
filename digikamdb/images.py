"""
Provides access to Digikam images.

Digikam images can be accessed via the ``Digikam`` property
:attr:`~Digikam.images`, which is an object of class :class:`Images`.
"""

import logging
import os
from datetime import datetime
from itertools import groupby
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from sqlalchemy import Column, Integer, String, delete, text
from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .properties import BasicProperties
from .image_comments import ImageCaptions, ImageTitles
from .image_helpers import ImageCopyright, ImageProperties, define_image_helper_tables
from .types import ImageCategory as Category, ImageStatus as Status


log = logging.getLogger(__name__)


def _image_class(dk: 'Digikam') -> type:                    # noqa: F821, C901
    """
    Returns the Image class.
    """
    if not dk.is_mysql:
        from sqlalchemy.dialects import sqlite
    
    class Image(dk.base):
        """
        Represents a row in the table ``Images``.
        
        The image's album can be accessed by :attr:`album`.
        
        Digikam splits metadata (Exif and own) in several tables. `Image`
        has the corresponding properties:
        
        * :attr:`caption` and :attr:`title`
        * :attr:`copyright`
        * :attr:`imagemeta` (for pictures)
        * :attr:`information`
        * :attr:`position`
        * :attr:`properties`
        * :attr:`tags`
        * :attr:`videometa` (for movies)
        
        See also:
            * Class :class:`~digikamdb.images.Images`
        """
        
        __tablename__ = 'Images'
        
        if not dk.is_mysql:
            _modificationDate = Column(
                'modificationDate',
                sqlite.DATETIME(
                    storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                    regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)')
            )
        
        _albumObj = relationship(
            'Album',
            primaryjoin = 'foreign(Image._album) == Album._id',
            back_populates = '_images')
        _comments = relationship(
            'ImageComment',
            primaryjoin = 'foreign(ImageComment._imageid) == Image._id',
            lazy = 'dynamic')
        _copyright = relationship(
            'ImageCopyrightEntry',
            primaryjoin = 'foreign(ImageCopyrightEntry._imageid) == Image._id',
            lazy = 'dynamic')
        _history = relationship(
            'ImageHistory',
            primaryjoin = 'foreign(ImageHistory._imageid) == Image._id',
            uselist = False)
        _information = relationship(
            'ImageInformation',
            primaryjoin = 'foreign(ImageInformation._imageid) == Image._id',
            uselist = False)
        _metadata = relationship(
            'ImageMetadata',
            primaryjoin = 'foreign(ImageMetadata._imageid) == Image._id',
            uselist = False)
        _position = relationship(
            'ImagePosition',
            primaryjoin = 'foreign(ImagePosition._imageid) == Image._id',
            uselist = False)
        _properties = relationship(
            'ImageProperty',
            primaryjoin = 'foreign(ImageProperty._imageid) == Image._id',
            lazy = 'dynamic')
        _tags = relationship(
            'Tag',
            primaryjoin = 'foreign(ImageTags.c.imageid) == Image._id',
            secondaryjoin = 'foreign(ImageTags.c.tagid) == Tag._id',
            secondary = 'ImageTags')
        _videometadata = relationship(
            'VideoMetadata',
            primaryjoin = 'foreign(VideoMetadata._imageid) == Image._id',
            uselist = False)
        
        # -- Relationship properties -----------------------------------------
        
        # Relationship to Albums
        
        @property
        def album(self) -> 'Album':                      # noqa: F821
            """
            Returns the album (directory) to which the image belongs.
            """
            return self._albumObj
        
        # Relationship to ImageComments
        
        @property
        def captions(self) -> ImageCaptions:
            """
            Returns image's captions object.
            
            See :class:`Captions` for a more detailed description.
            """
            if not hasattr(self, '_captionsObj'):
                self._captionsObj = ImageCaptions(self)
            return self._captionsObj
        
        @property
        def caption(self) -> str:
            """
            Returns or sets the image's default caption.
            
            The default caption has 'x-default' as language and ``None``
            as author. For comments in other languages or from other authors,
            use :attr:`~Image.captions`.
            """
            return self.captions['']
        
        @caption.setter
        def caption(self, val: Optional[str]):
            self.captions[''] = val
        
        @property
        def titles(self) -> ImageTitles:
            """
            Returns the image's titles.
            
            Digikam supports multilingual titles. To access the title in a
            specific language, use the ``[]`` operator:
            
            .. code-block:: python
                
                french = img.titles['fr-FR']
                default = img.titles['x-default']    # default language
            
            ``titles['']`` or ``titles[None]`` will return the default
            language (**x-default**)
            """
            if not hasattr(self, '_titlesObj'):
                self._titlesObj = ImageTitles(self)
            return self._titlesObj
        
        @property
        def title(self) -> str:
            """
            Returns the title in default language ('x-default').
            
            For comments in other languages, use :attr:`~Image.titles`.
            """
            return self.titles['']
        
        @title.setter
        def title(self, val: Optional[str]):
            self.titles[''] = val
        
        # Relationship to ImageCopyright
        
        @property
        def copyright(self) -> ImageCopyright:
            """
            Returns the copyright data.
            
            """
            if not hasattr(self, '_copyrightObj'):
                self._copyrightObj = ImageCopyright(self)
            return self._copyrightObj
        
        # Relationship to ImageHistory
        
        @property
        def history(self) -> 'ImageHistory':                # noqa: F821
            """
            Returns the image's history
            """
            return self._history
        
        # Relationship to ImageInformation

        @property
        def information(self) -> 'ImageInformation':        # noqa: F821
            """
            Returns some of the image's information.
            """
            return self._information
        
        # Relationship to ImageMetadata
        
        @property
        def imagemeta(self) -> 'ImageMetadata':             # noqa: F821
            """
            Returns the image's photographic metadata
            """
            return self._metadata
        
        # Relationship to ImagePositions
        
        @property
        def position(self) -> Optional[Tuple]:
            """
            Returns or sets GPS location data.
            
            The Value is a tuple with latitude, longitude and altitude. When
            setting the property, latitude and longitude can be given as a
            signed float, as a stringified float or as a string containing
            the absolute value followed by ``N``, ``S``, ``W`` or ``E``. The
            altitude can be omitted, in this case it is not changed if already
            present. To remove an existing altitude, give the position as
            ``(latitude, longitude, None)``
            
            When ``position`` is set to ``None``, the row in ImagePositions
            will be deleted.
            """
            
            if self._position:
                return (
                    self._position._latitudeNumber,
                    self._position._longitudeNumber,
                    self._position._altitude)
            return None
        
        @position.setter
        def position(self, pos: Optional[Tuple]):
            log.debug(
                'Setting position of image %d (%s) to %s',
                self.id,
                self.name,
                pos
            )
            if pos is None:
                if self._position:
                    self._session.execute(
                        delete(self._container.ImagePosition)
                        .filter_by(_imageid = self.id))
                return
            
            lat = pos[0]
            lng = pos[1]
            
            if isinstance(lat, str):
                if lat[-1] == 'N':
                    lat = float(lat[:-1])
                elif lat[-1] == 'S':
                    lat = - float(lat[:-1])
                else:
                    lat = float(lat)

            if isinstance(lng, str):
                if lng[-1] == 'E':
                    lng = float(lng[:-1])
                elif lng[-1] == 'W':
                    lng = - float(lng[:-1])
                else:
                    lng = float(lng)
            
            if lat < 0:
                lat2 = -lat
                latstr = '%d,%.8fS' % (int(lat2), (lat2-int(lat2))*60)
            else:
                latstr = '%d,%.8fN' % (int(lat), (lat-int(lat))*60)
            if lng < 0:
                lng2 = -lng
                lngstr = '%d,%.8fW' % (int(lng2), (lng2-int(lng2))*60)
            else:
                lngstr = '%d,%.8fE' % (int(lng), (lng-int(lng))*60)
            
            if self._position:
                self._position._latitude = latstr
                self._position._longitude = lngstr
                self._position._latitudeNumber = lat
                self._position._longitudeNumber = lng
                if len(pos) > 2:
                    self._position._altitude = pos[2]
            else:
                alt = None
                if len(pos) > 2:
                    alt = pos[2]
                newpos = self._container.ImagePosition(
                    _imageid = self.id,
                    _latitude = latstr,
                    _longitude = lngstr,
                    _latitudeNumber = lat,
                    _longitudeNumber = lng,
                    _altitude = alt)
                self._session.add(newpos)
#            self._session.commit()
        
        # Relationship to ImageProperties
        
        @property
        def properties(self) -> ImageProperties:
            """
            Returns the image's properties
            """
            
            if not hasattr(self, '_propertiesObj'):
                self._propertiesObj = ImageProperties(self)
            return self._propertiesObj
        
        # Relationship to Tags
        
        @property
        def tags(self) -> List['Tag']:                      # noqa: F821
            """Returns the image's tags"""
            return self._tags
        
        # Relationship to VideoMetadata
        
        @property
        def videometa(self) -> 'VideoMetadata':             # noqa: F821
            """Returns the metadata for video files"""
            return self._videometadata
        
        # Column properties:
        
        @property
        def id(self) -> int:
            """The image's id (read-only)"""
            return self._id
        
        @property
        def name(self) -> str:
            """The image's file name (read-only)"""
            return self._name
        
        @property
        def status(self) -> Status:
            return Status(self._status)
        
        @property
        def category(self) -> Category:
            return Category(self._category)
        
        @validates('_status', '_category')
        def _convert_to_int(self, key, value):
            return int(value)
        
        @property
        def modificationDate(self) -> datetime:
            return self._modificationDate
        
        @property
        def fileSize(self) -> int:
            return self._fileSize
        
        @property
        def uniqueHash(self) -> str:
            return self._uniqueHash
        
        @property
        def manualOrder(self) -> int:
            return self._manualOrder
        
        # Other properties and members
        
        @property
        def abspath(self) -> str:
            """
            Returns the absolute path of the image file.
            """
            return os.path.abspath(os.path.join(
                self.album.abspath,
                self._name))
        
    return Image
        

class Images(DigikamTable):
    """
    Offers access to the images in the Digikam instance.
    
    ``Images`` represents all images present in the Digikam database. It is
    usually accessed through the :class:`~digikamdb.connection.Digikam`
    property :attr:`~digikamdb.connection.Digikam.images`.
    
    Usage:
    
    .. code-block:: python
        
        dk = Digikam(...)
        myimage = dk.images.find('/path/to/my/image.jpg')   # by name
        myimage = dk.images[42]                             # by id
        for img in dk.images:                               # iterate
            print(img.name)
    
    Parameters:
        digikam:    Digikam object for access to database and other classes.

    See also:
        * Class :class:`~_sqla.Image`
    """
    
    _class_function = _image_class
    
    def __init__(
        self,
        digikam: 'Digikam',                                  # noqa: F821
    ):
        super().__init__(digikam)
        define_image_helper_tables(self)
    
    def find(
        self,
        path: Union[str, bytes, os.PathLike]
    ) -> List['Image']:                                 # noqa: F821
        """
        Finds an Image by name.
        
        Args:
            name:   Path to image file. Can be given as any type that the
                    :mod:`os.path` functions understand.
        """
        log.debug(
            'Images: searching for %s',
            path,
        )
        abspath = os.path.abspath(path)
        
        albums = self.digikam.albums.find(abspath)
        if albums:
            ret = []
            for al in albums:
                log.debug('Adding images from album %s to result', al.abspath)
                ret.extend(al.images.all())
            return ret
        
        # There are no albums on path, so path must 
        # be an image file if it exists.
        base = os.path.basename(abspath)
        dir_ = os.path.dirname(abspath)
        
        album = self.digikam.albums.find(dir_, True)
        if album:
            log.debug('Returning images from album %s', album.abspath)
            return album.images.filter_by(_name = base).all()
        
        log.debug('No files found')
        return []

