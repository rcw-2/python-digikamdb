"""
Provides access to Digikam images.

Digikam images can be accessed via the ``Digikam`` property
:attr:`~Digikam.images`, which is an object of class :class:`Images`.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Tuple, Union

from sqlalchemy import Column, Table, delete
from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .properties import BasicProperties


log = logging.getLogger(__name__)


class ImageProperties(BasicProperties):
    """
    Image Properties
    
    Args:
        parent(Image): The corresponding ``Image`` object.
    """
    
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
            self._parent.session.add(row)
        
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
            self._parent.session.delete(row)
        

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


class Copyright:
    """
    Encapsulates ImageCopyright.
    
    Individual copyright entries can be accessed similar to a :class:`dict`.
    Values can be:
    
    * :class:`str` - The value column.
    * :class:`tuple` - A tuple with the columns (value, extraValue).
    
    If extraValue is set, a tuple is returned, else a str. If no row with a
    given key exists, ``None`` is returned.
    
    Args:
        parent:     The corresponding ``Image`` object.
    """
    
    def __init__(self, parent: 'Image'):                    # noqa: F821
        self._parent = parent
    
    def __contains__(self, key: str) -> bool:
        if self._parent._copyright.filter(property = key).fetchone():
            return True
        else:
            return False
    
    def __getitem__(self, key: str) -> Union[str, Tuple]:
        row = self._parent._copyright.filter(property = key).one_or_none()
        if not row:
            return None
        if row.extraValue is None:
            return row.value
        else:
            return row.value, row.extraValue
    
    def __setitem__(self, key: str, value: Optional[Union[str, List, Tuple]]):
        log.debug(
            'Setting copyright info %s of image %d (%s) to %s',
            key,
            self._parent.id,
            self._parent.name,
            value
        )
        if isinstance(value, (list, tuple)):
            extravalue = value[1]
            value = value[0]
        else:
            extravalue = None
        if key in self:
            row = self._parent._copyright.filter(property = key).one()
            row.value = value
            row.extraValue = extravalue
        else:
            row = self._parent.ImageCopyright(
                imageid = self.parent.id,
                property = key,
                value = value,
                extraValue = extravalue)
            self._parent.session.add(row)


def _imagecomment_class(dk: 'Digikam') -> type:             # noqa: F821
    """
    Defines the ImageComment class.
    """
    
    class ImageComment(dk.base):
        """
        Digikam Image Comment
        
        Data in this table should be accessed through the ``Image`` properties
        :attr:`~Image.caption` and :attr:`~Image.title`.
        """
        __tablename__ = 'ImageComments'
        if not dk.is_mysql:
            from sqlalchemy.dialects.sqlite import DATETIME
            date = Column(DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
    
    return ImageComment


def _imagecopyright_class(dk: 'Digikam') -> type:           # noqa: F821
    """
    Defines the ImageCopyright class.
    """
    
    class ImageCopyright(dk.base):
        """
        Digikam Image Copyright
        """
        __tablename__ = 'ImageCopyright'
    
    return ImageCopyright


def _imagehistory_class(dk: 'Digikam') -> type:             # noqa: F821
    """
    Defines the ImageHistory class.
    """
    
    class ImageHistory(dk.base):
        """
        Digikam Image History

        The following column-related properties can be directly accessed:
        
        * **imageid** (*int*)
        * **uuid** (*str*)
        * **history** (*str*)
        """
        __tablename__ = 'ImageHistory'
    
    return ImageHistory


def _imageinformation_class(dk: 'Digikam') -> type:         # noqa: F821
    """
    Defines the ImageInformation class
    """
    
    class ImageInformation(dk.base):
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
        
        if not dk.is_mysql:
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
    
    return ImageInformation


def _imagemetadata_class(dk: 'Digikam') -> type:            # noqa: F821
    """
    Defines the ImageMetadata class.
    """
    
    class ImageMetadata(dk.base):
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
    
    return ImageMetadata


def _imageposition_class(dk: 'Digikam') -> type:            # noqa: F821
    """
    Defines the ImagePosition class
    """
    
    class ImagePosition(dk.base):
        """
        Contains the Image's position.
        
        Should be accessed through :attr:`Image.position`.
        """
        __tablename__ = 'ImagePositions'
    
    return ImagePosition


def _videometadata_class(dk: 'Digikam') -> type:            # noqa: F821
    """
    Defines the VideoMetadata class
    """
    
    class VideoMetadata(dk.base):
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
    
    return VideoMetadata


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
            'ImageCopyright',
            primaryjoin = 'foreign(ImageCopyright.imageid) == Image.id',
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
        def copyright(self) -> Copyright:
            """
            Returns the copyright data.
            
            """
            if not hasattr(self, '_copyrightObj'):
                self._copyrightObj = Copyright(self)
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
            altitude can be omitted.
            
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
                    self.session.execute(
                        delete(self.ImagePosition)
                        .filter_by(imageid = self.id))
#                    self.session.commit()
                return
            
            lat = pos[0]
            lng = pos[1]
            alt = None
            if len(pos) > 2:
                alt = pos[2]
            
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
                if alt:
                    self._position.altitude = alt
            else:
                newpos = self.ImagePosition(
                    imageid = self.id,
                    latitude = latstr,
                    longitude = lngstr,
                    latitudeNumber = lat,
                    longitudeNumber = lng,
                    altitude = alt)
                self.session.add(newpos)
#            self.session.commit()
        
        # Relationship to ImageProperties
        
        @property
        def properties(self) -> ImageProperties:
            """
            Returns the image's properties
            """
            
            if not hasattr(self, '_properties'):
                self._properties = ImageProperties(self)
            return self._properties
        
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
        parent:     Digikam object for access to database and other classes.

    See also:
        * Class :class:`~_sqla.Image`
    """
    
    _class_function = _image_class
    
    def __init__(
        self,
        parent: 'Digikam',                                  # noqa: F821
    ):
        super().__init__(parent)
        self.Class.ImageComment = _imagecomment_class(self.parent)
        self.Class.ImageCopyright = _imagecopyright_class(self.parent)
        self.Class.ImageHistory = _imagehistory_class(self.parent)
        self.Class.ImageInformation = _imageinformation_class(self.parent)
        self.Class.ImageMetadata = _imagemetadata_class(self.parent)
        self.Class.ImagePosition = _imageposition_class(self.parent)
        self.Class.VideoMetadata = _videometadata_class(self.parent)
        self.Class.properties_table = Table(
            'ImageProperties',
            parent.base.metadata,
            autoload_with = self.engine)
    
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

