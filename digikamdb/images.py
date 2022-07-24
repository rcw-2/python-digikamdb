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


log = logging.getLogger(__name__)


def _imagecopyrightentry_class(dk: 'Digikam') -> type:      # noqa: F821
    """Returns the ImageCopyrightEntry class."""
    return dk.images.Class.ImageCopyrightEntry


def _imageproperty_class(dk: 'Digikam') -> type:            # noqa: F821
    """Returns the TagProperty class."""
    return dk.images.Class.ImageProperty


class ImageProperties(BasicProperties):
    """
    Image Properties
    
    Args:
        digikam:    The Digikam object
        parent:     The corresponding ``Image`` object.
    """
    
    # Funktion returning the table class
    _class_function = _imageproperty_class
    
    #: Parent id column
    _parent_id_col = 'imageid'
    
    #: Key column
    _key_col = 'property'
    
    #: Value column
    _value_col = 'value'


class Comment:
    """
    Encapsulates ImageComments (caption and title).
    
    Args:
        parent:     Corresponding Image object
        type:       Comment type (1 for caption, 3 for title)
    """
    def __init__(self, parent: 'Image', type_: int):       # noqa: F821
        self._parent = parent
        self._type = type_
    
    def __repr__(self) -> str:
        return self.get().__repr__()
    
    def get(
        self,
        language: str = 'x-default',
        author: Optional[str] = None
    ) -> Optional[str]:
        """
        Returns the comment value.
        
        Args:
            language:   The comment's, defaults to 'x-default'
            author:     The comment's author
        Returns:
            The specified comment or ``None`` if
            no matching comment was found
        """
        
        row = self._parent._comments.filter_by(
            type = self._type,
            language = language,
            author = author,
        ).one_or_none()
        
        if not row:
            return None

        return row.comment

    def get_date(
        self,
        language: str = 'x-default',
        author: Optional[str] = None
    ) -> Optional[datetime]:
        """
        Returns the comment date.
        
        Args:
            language:   The comment's, defaults to 'x-default'
            author:     The comment's author
        Returns:
            The specified comment's date or ``None`` if
            no matching comment was found
        """
        
        row = self._parent._comments.filter_by(
            type = self._type,
            language = language,
            author = author,
        ).one_or_none()
        
        if not row:
            return None
        
        return row.date
    
    def set(
        self,
        value: str,
        language: str = 'x-default',
        author: Optional[str] = None,
        date: Optional[datetime] = None
    ):
        """
        Sets the comment.
        
        Database-wise, this means updating the corresponding row in ``ImageComments``
        or inserting a new one.
        
        Args:
            value:      New value for comment
            language:   The comment's, defaults to 'x-default'
            author:     The comment's author, defaults to ``None``
            date:       New date value for comment, defaults to ``None``
        """
        log.debug(
            'Setting comment(%d,%s,%s) of image %d (%s) to %s',
            self._type,
            language,
            author,
            self._parent.id,
            self._parent.name,
            value
        )
        row = self._parent._comments.filter_by(
            type = self._type,
            language = language,
            author = author,
        ).one_or_none()
        
        if row:
            row.comment = value
        else:
            row = self._parent.ImageComment(
                imageid = self._parent.id,
                type = self._type,
                language = language,
                author = author,
                comment = value
            )
            self._parent._session.add(row)
        
        if date is not None:
            row.date = date
    
    def delete(
        self,
        language: str = 'x-default',
        author: Optional[str] = None,
    ):
        """
        Deletes the comment.
        
        Args:
            language:   The comment's, defaults to 'x-default'
            author:     The comment's author, defaults to ``None``
        """
        log.debug(
            'Deleting comment(%d,%s,%s) of image %d (%s)',
            self._type,
            language,
            author,
            self._parent.id,
            self._parent.name,
        )
        row = self._parent._comments.filter_by(
            type = self._type,
            language = language,
            author = author,
        ).one_or_none()
        
        if row:
            self._parent._session.delete(row)
        

class Title(Comment):
    """
    Enables access to multilingual image titles.
    
    
    
    Args:
        parent:     Image object the title belongs to
    """
    
    def __init__(self, parent: 'Image'):                    # noqa: F821
        super().__init__(parent, 3)
    
    def get(
        self,
        language: str = 'x-default'
    ) -> str:
        """
        Returns the title value.
        
        Args:
            language:   The comment's, defaults to 'x-default'
        Returns:
            The specified comment or ``None`` if
            no matching comment was found
        """
        return super().get(language, None)

    def get_date(
        self,
        language: str = 'x-default'
    ) -> 'datetime.datetime':
        """
        Returns NotImplemented since titles do't appear to have dates.
        """
        log.warning('get_date is not implemented for title')
        return NotImplemented
    
    def set(
        self,
        value: str,
        language: str = 'x-default'
    ):
        """
        Sets the title

        Args:
            value:      New value for comment
            language:   The comment's, defaults to 'x-default'
        """
        super().set(value, language, None, None)

    def delete(
        self,
        language: str = 'x-default',
        author: Optional[str] = None,
    ):
        """
        Deletes the comment.
        
        Args:
            language:   The comment's, defaults to 'x-default'
        """
        super().delete(language, None)


class Caption(Comment):
    def __init__(self, parent: 'Image'):                    # noqa: F821
        super().__init__(parent, 1)


class ImageCopyright(BasicProperties):
    """
    Encapsulates ImageCopyright.
    
    Individual copyright entries can be accessed similar to a :class:`dict`.
    Values can be:
    
    * A string that is copied to the value column, the extravalue column
      will be None in this case.
    * A sequence of (value, extravalue) pairs.
    
    If extraValue is set, a tuple is returned, else a str. If no row with a
    given key exists, ``None`` is returned.
    
    Args:
        parent:     The corresponding ``Image`` object.
    """
    
    # Mapped class
    _class_function = _imagecopyrightentry_class
    
    #: Parent id column
    _parent_id_col = 'imageid'
    
    #: Key column
    _key_col = 'property'
    
    def __getitem__(self, key: str) -> Union[str, Tuple]:
        ret = []
        kwargs = { self._parent_id_col: self._parent.id, self._key_col: key }
        ret = [
            (entry.value, entry.extraValue)
            for entry in self._select(**kwargs)
        ]
        if len(ret) == 1 and ret[0][1] is None:
            return ret[0][0]
        return ret
    
    def __setitem__(self, key: str, value: Optional[Union[str, Sequence[Tuple]]]):
        log.debug(
            'Setting copyright info %s of image %d (%s)',
            key,
            self._parent.id,
            self._parent.name
        )
        self.remove(key)
        
        if value is None:
            log.debug('Setting None')
            return
        
        log.debug('Setting values:')
        if isinstance(value, str):
            value = [(value, None)]
        for v, ev in value:
            kwargs = {
                self._parent_id_col:    self.parent.id,
                self._key_col:          key,
                'value':                v,
                'extraValue':           ev,
            }
            log.debug('- Setting value %s, %s', v, ev)
            self._insert(**kwargs)
    
    def items(self) -> Iterable:
        kwargs = { self._parent_id_col: self._parent.id }
        for prop, rows in groupby(
            self._select(**kwargs).order_by(text(self._key_col)),
            lambda x: getattr(x, self._key_col),
        ):
            value = [(row.value, row.extraValue) for row in rows]
            if len(value) == 1 and value[0][1] is None:
                value = value[0][0]
            yield prop, value


def _image_class(dk: 'Digikam') -> type:                    # noqa: F821, C901
    """
    Returns the Image class.
    """
    
    class Image(dk.base):
        """
        Represents a row in the table ``Images``.
        
        The following column-related properties can be directly accessed:
        
        * **id** (*int*)
        * **name** (*str*) - The image's file name.
        * **status** (*int*)
        * **category** (*int*)
        * **modificationDate** (*datetime*)
        * **fileSize** (*int*)
        * **uniqueHash** (*str*)
        * **manualOrder** (*int*)
        
        The image's album can be accessed by :attr:`albumObj`.
        
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
            from sqlalchemy.dialects.sqlite import DATETIME
            modificationDate = Column(DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
        
        _album = relationship(
            'Album',
            primaryjoin = 'foreign(Image.album) == Album.id',
            back_populates = '_images')
        _comments = relationship(
            'ImageComment',
            primaryjoin = 'foreign(ImageComment.imageid) == Image.id',
            lazy = 'dynamic')
        _copyright = relationship(
            'ImageCopyrightEntry',
            primaryjoin = 'foreign(ImageCopyrightEntry.imageid) == Image.id',
            lazy = 'dynamic')
        _history = relationship(
            'ImageHistory',
            primaryjoin = 'foreign(ImageHistory.imageid) == Image.id',
            uselist = False)
        _information = relationship(
            'ImageInformation',
            primaryjoin = 'foreign(ImageInformation.imageid) == Image.id',
            uselist = False)
        _metadata = relationship(
            'ImageMetadata',
            primaryjoin = 'foreign(ImageMetadata.imageid) == Image.id',
            uselist = False)
        _position = relationship(
            'ImagePosition',
            primaryjoin = 'foreign(ImagePosition.imageid) == Image.id',
            uselist = False)
        _properties = relationship(
            'ImageProperty',
            primaryjoin = 'foreign(ImageProperty.imageid) == Image.id',
            lazy = 'dynamic')
        _tags = relationship(
            'Tag',
            primaryjoin = 'foreign(ImageTags.c.imageid) == Image.id',
            secondaryjoin = 'foreign(ImageTags.c.tagid) == Tag.id',
            secondary = 'ImageTags')
        _videometadata = relationship(
            'VideoMetadata',
            primaryjoin = 'foreign(VideoMetadata.imageid) == Image.id',
            uselist = False)
        
        # -- Relationship properties -----------------------------------------
        
        # Relationship to Albums
        
        @property
        def albumObj(self) -> 'Album':                      # noqa: F821
            """
            Returns the album (directory) to which the image belongs.
            
            This cannot be named "album" as this is the column containing
            the image's album id.
            """
            return self._album
        
        # Relationship to ImageComments
        
        @property
        def caption(self) -> Caption:
            """
            Returns or sets the image's default caption.
            
            The setter will set the caption for ``language = 'x-default'``
            and ``author = None``. For other languages and authors, use the
            :class:`~digikamdb.images.Caption` methods
            :meth:`~digikamdb.images.Caption.get` and
            :meth:`~digikamdb.images.Caption.set`.
            """
            
            if not hasattr(self, '_captionObj'):
                self._captionObj = Caption(self)
            return self._captionObj
        
        @caption.setter
        def caption(self, val: Optional[str]):
            self.caption.set(val)
        
        @property
        def title(self) -> Title:
            """
            Returns or sets the image's title.
            
            The setter will set the caption for ``language = 'x-default'``.
            For other languages, use the :class:`~digikamdb.images.Title`
            methods :meth:`~digikamdb.images.Title.get` and
            :meth:`~digikamdb.images.Title.set`.
            """
            if not hasattr(self, '_titleObj'):
                self._titleObj = Title(self)
            return self._titleObj
        
        @title.setter
        def title(self, val: Optional[str]):
            self.title.set(val)
        
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
                    self._position.latitudeNumber,
                    self._position.longitudeNumber,
                    self._position.altitude)
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
                        delete(self.ImagePosition)
                        .filter_by(imageid = self.id))
#                    self._session.commit()
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
                self._position.latitude = latstr
                self._position.longitude = lngstr
                self._position.latitudeNumber = lat
                self._position.longitudeNumber = lng
                if len(pos) > 2:
                    self._position.altitude = pos[2]
            else:
                alt = None
                if len(pos) > 2:
                    alt = pos[2]
                newpos = self.ImagePosition(
                    imageid = self.id,
                    latitude = latstr,
                    longitude = lngstr,
                    latitudeNumber = lat,
                    longitudeNumber = lng,
                    altitude = alt)
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
        
        # Other properties and members
        
        @property
        def abspath(self) -> str:
            """
            Returns the absolute path of the image file.
            """
            return os.path.abspath(os.path.join(
                self.albumObj.abspath,
                self.name))

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
        self._define_helper_tables()
    
    def _define_helper_tables(self):
        """Defines the classes for helper tables."""
        
        class ImageComment(self.digikam.base):
            """
            Digikam Image Comment
            
            Data in this table should be accessed through the ``Image`` properties
            :attr:`~Image.caption` and :attr:`~Image.title`.
            """
            __tablename__ = 'ImageComments'
            if not self.is_mysql:
                from sqlalchemy.dialects.sqlite import DATETIME
                date = Column(DATETIME(
                    storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                    regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
        
        class ImageCopyrightEntry(self.digikam.base):
            """
            Digikam Image Copyright
            """
            __tablename__ = 'ImageCopyright'
        
        class ImageHistory(self.digikam.base):
            """
            Digikam Image History

            The following column-related properties can be directly accessed:
            
            * **imageid** (*int*)
            * **uuid** (*str*)
            * **history** (*str*)
            """
            __tablename__ = 'ImageHistory'
        
        class ImageInformation(self.digikam.base):
            """
            Represents a row of the `ImageInformation` table
            
            The following column-related properties can be directly accessed:
            
            * **imageid** (*int*)
            * **rating** (*int*) - The image's rating, must be from -1 to 5.
            * **creationDate** (:class:`~datetime.datetime`)
            * **digitizationDate** (:class:`~datetime.datetime`)
            * **orientation** (*int*)
            """
            __tablename__ = 'ImageInformation'
            
            if not self.is_mysql:
                from sqlalchemy.dialects.sqlite import DATETIME
                creationDate = Column(DATETIME(
                    storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                    regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
                digitizationDate = Column(DATETIME(
                    storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                    regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
            
            @validates('rating')
            def _validate_rating(self, key: int, value: int) -> int:
                if value < -1 or value > 5:
                    raise ValueError('Image rating must be from -1 to 5')
                return value
        
        class ImageMetadata(self.digikam.base):
            """
            Represents a row of the ``ImageMetadata`` table.
            
            This object contains Exif information of the corresponding
            :class:`Image` object. The following column-related properties
            can be directly accessed:
            
            * **make** (*str*)
            * **model** (*str*)
            * **lens** (*str*)
            * **aperture** (*float*)
            * **focalLength** (*float*)
            * **focalLength35** (*float*)
            * **exposureTime** (*float*)
            * **exposureProgram** (*int*)
            * **exposureMode** (*int*)
            * **sensitivity** (*int*)
            * **flash** (*int*)
            * **whiteBalance** (*int*)
            * **whiteBalanceColorTemperature** (*int*)
            * **meteringMode** (*int*)
            * **subjectDistance** (*float*)
            * **subjectDistanceCategory** (*int*)
            """
            __tablename__ = 'ImageMetadata'
            
            # Retrieve double as float
            if self.is_mysql:
                from sqlalchemy.dialects.mysql import DOUBLE
                aperture = Column(DOUBLE(asdecimal = False))
                focalLength = Column(DOUBLE(asdecimal = False))
                focalLength35 = Column(DOUBLE(asdecimal = False))
                exposureTime = Column(DOUBLE(asdecimal = False))
                subjectDistance = Column(DOUBLE(asdecimal = False))
        
        class ImagePosition(self.digikam.base):
            """
            Contains the Image's position.
            
            Should be accessed through :attr:`Image.position`.
            """
            __tablename__ = 'ImagePositions'
            
            # Retrieve double as float
            if self.is_mysql:
                from sqlalchemy.dialects.mysql import DOUBLE
                latitudeNumber = Column(DOUBLE(asdecimal = False))
                longitudeNumber = Column(DOUBLE(asdecimal = False))
                altitude = Column(DOUBLE(asdecimal = False))
                orientation = Column(DOUBLE(asdecimal = False))
                tilt = Column(DOUBLE(asdecimal = False))
                roll = Column(DOUBLE(asdecimal = False))
                accuracy = Column(DOUBLE(asdecimal = False))
        
        class ImageProperty(self.digikam.base):
            """
            Image Properties
            
            This table should be accessed via
            Class :class:`~digikamdb.images.ImageProperties`.
            """
            __tablename__ = 'ImageProperties'
            
            imageid = Column(Integer, primary_key = True)
            property = Column(String, primary_key = True)
        
        class VideoMetadata(self.digikam.base):
            """
            Digikam Video Metadata
            
            This object contains Video metadata of the corresponding
            :class:`Image` object. The following column-related properties can be
            directly accessed:
            
            * **aspectRatio** (*str*)
            * **audioBitRate** (*str*)
            * **audioChannelType** (*str*)
            * **audioCompressor** (*str*)
            * **duration** (*str*)
            * **frameRate** (*str*)
            * **exposureProgram** (*int*)
            * **videoCodec** (*str*)
            """
            __tablename__ = 'VideoMetadata'
        
        self.Class.ImageComment = ImageComment
        self.Class.ImageCopyrightEntry = ImageCopyrightEntry
        self.Class.ImageHistory = ImageHistory
        self.Class.ImageInformation = ImageInformation
        self.Class.ImageMetadata = ImageMetadata
        self.Class.ImagePosition = ImagePosition
        self.Class.ImageProperty = ImageProperty
        self.Class.VideoMetadata = VideoMetadata
    
    def find(
        self,
        name: Union[str, bytes, os.PathLike]
    ) -> Optional['Image']:                                 # noqa: F821
        """
        Finds an Image by name.
        
        Args:
            name:   Path to image file. Can be given as any type that the
                    :mod:`os.path` functions understand.
        """
        base = os.path.basename(name)
        path = os.path.abspath(name)
        
        # Seleft images with correct name:
        found = self._select(name = base)
        
        # Look for image that is the same file as path:
        if os.path.isfile(path):
            for img in found:
                # Return image if it is the same file
                if (
                    os.path.isfile(img.abspath) and
                    os.path.samefile(img.abspath, path)
                ):
                    log.debug(
                        '%s is the same file as image %d (%s)',
                        path,
                        img.id,
                        img.name
                    )
                    return img
        
        # Look for path:
        for img in found:
            if (img.abspath == path):
                log.debug(
                    '%s found in database: %d (%s)',
                    path,
                    img.id,
                    img.name
                )
                return img
        
        # If nothing was found, return None
        return None

