"""
Digikam Images
"""

import os
from typing import Any, Iterable, List, Optional, Tuple, Union

from sqlalchemy import Column, MetaData, Table, select
from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .properties import BasicProperties

class ImageProperties(BasicProperties):
    """
    Image Properties
    """
    
    # Parent id column
    _parent_id_col = 'imageid'
    
    # Key column
    _key_col = 'property'    
    
    #! Value column
    _value_col = 'value'

class Copyright:
    """Encapsulates ImageCopyright."""
    
    def __init__(self, parent: 'Image'):
        self.parent = parent
    
    def __contains__(self, key: str) -> bool:
        if self.parent._copyright.filter(property = key).fetchone():
            return True
        else:
            return False
    
    def __getitem__(self, key: str) -> Union[str,Tuple]:
        row = self.parent._copyright.filter(property = key).one_or_none()
        if not row:
            return None
        if row.extraValue is None:
            return row.value
        else:
            return row.value, row.extraValue
    
    def __setitem__(self, key: str, value: Any):
        if isistance(value, (list, tuple)):
            extravalue = value[1]
            value = value[0]
        else:
            extravalue = None
        if key in self:
            row = self.parent._copyright.filter(property = key).one()
            row.value = value
            row.extraValue = extravalue
        else:
            row = parent.ImageCopyright(
                imageid = parent.id,
                property = key,
                value = value,
                extraValue = extravalue)
            self.parent.session.add(row)
        self.parent.session.commit()


def _imagecomment_class(dk: 'Digikam') -> type:
    """
    Defines the ImageComment class
    """
    
    class ImageComment(dk.base):
        """
        Digikam Image Comment
        """
        __tablename__ = 'ImageComments'
    
    return ImageComment

def _imagecopyright_class(dk: 'Digikam') -> type:
    """
    Defines the ImageCopyright class
    """
    
    class ImageCopyright(dk.base):
        """
        Digikam Image Copyright
        """
        __tablename__ = 'ImageCopyright'
    
    return ImageCopyright

def _imagehistory_class(dk: 'Digikam') -> type:
    """
    Defines the ImageHistory class
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

def _imageinformation_class(dk: 'Digikam') -> type:
    """
    Defines the ImageInformation class
    """
    
    class ImageInformation(dk.base):
        """
        Represents a row of the `ImageInformation` table
        
        The following column-related properties can be directly accessed:
        
        * **imageid** (*int*)
        * **rating** (*int*) - The image's rating, must be from -1 to 5.
        * **creationDate** (*datetime*)
        * **digitizationDate** (*datetime*)
        * **orientation** (*int*)
        """
        __tablename__ = 'ImageInformation'
        
        if not dk.is_mysql:
            from sqlalchemy.dialects.sqlite import DATETIME
            creationDate = Column(DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
            digitizationDate = Column(DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
        
        @validates('rating')
        def validate_rating(self, key: int, value: int) -> int:
            if value < -1 or value > 5:
                raise ValueError('Image rating must be from -1 to 5')
            return value
    
    return ImageInformation

def _imagemetadata_class(dk: 'Digikam') -> type:
    """
    Defines the ImageMetadata class
    """
    
    class ImageMetadata(dk.base):
        """
        Digikam Image Metadata
        """
        __tablename__ = 'ImageMetadata'
    
    return ImageMetadata

def _imageposition_class(dk: 'Digikam') -> type:
    """
    Defines the ImagePosition class
    """
    
    class ImagePosition(dk.base):
        """
        Digikam Image Position
        """
        __tablename__ = 'ImagePositions'
    
    return ImagePosition

def _videometadata_class(dk: 'Digikam') -> type:
    """
    Defines the VideoMetadata class
    """
    
    class VideoMetadata(dk.base):
        """
        Digikam Video Metadata
        """
        __tablename__ = 'VideoMetadata'
    
    return VideoMetadata

def _image_class(dk: 'Digikam') -> type:
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
        
        Digikam splits metadata (Exif and own) in several tables. `Image`
        has the corresponding properties:
        
        * :attr:`caption` and :attr:`title`
        * :attr:`information`
        * :attr:`imagemeta` (for pictures)
        * :attr:`position`
        * :attr:`properties`
        * :attr:`tags`
        * :attr:`videometa` (for movies)
        
        .. todo::   Interface to ImageCopyright table
        """
        
        __tablename__ = 'Images'
        
        if not dk.is_mysql:
            from sqlalchemy.dialects.sqlite import DATETIME
            modificationDate = Column(DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
        
        _album = relationship(
            'Album',
            primaryjoin = 'foreign(Image.album) == Album.id',
            back_populates = '_images')
        _comments = relationship(
            'ImageComment',
            primaryjoin = 'foreign(ImageComment.imageid) == Image.id')
        _copyright = relationship(
            'ImageCopyright',
            primaryjoin = 'foreign(ImageCopyright.imageid) == Image.id')
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
        
        
        
        ### Relationship properties
        
        # Relationship to Albums
        
        @property
        def albumObj(self) -> 'Album':
            """
            Returns the album (directory) to which the image belongs.
            
            This cannot be named "album" as this is the column containing
            the image's album id.
            """
            return self._album
        
        # Relationship to ImageComments
        
        def _get_comment(self, type_: int, as_object: bool = False) -> Optional[str]:
            """
            Retrieves a comment
            
            .. todo:: Handle languages
            
            Args:
                type\_:     The comment type (1 for caption, 3 for title)
                as_object:  Return comment as object or as value
            """
            for c in self._comments:
                if c.type == type_:
                    if as_object:
                        return c
                    else:
                        return c.comment
            return None
        
        def _set_comment(self, type_: int, val: Optional[str]):
            """
            Sets a comment
            
            .. todo:: Handle languages
            
            Args:
                type\_:     The comment type (1 for caption, 3 for title)
                val:        New value for comment. If set to None, the
                            row in ImageComments will be deleted.
            """
            oldval = self._get_comment(type_, as_object = True)
            if oldval is None:
                if val:
                    newcomment = self.ImageComment(
                        imageid     = self.id,
                        type        = type_,
                        language    = 'x-default',
                        comment     = val)
                    self.session.add(newcomment)
                    #self.session.commit()
            else:
                if val is None:
                    self.session.execute(
                        delete(self.ImageComment)
                            .filter_by(imageid = self.id)
                            .filter_by(type = type_))
                    self.session.commit()
                else:
                    oldval.comment = val
                    #self.session.commit()
                    
        @property
        def caption(self) -> Optional[str]:
            """
            Returns or sets the image's caption.
            
            Setting this to ``None`` will delete the corresponding row in
            ImageComments.
            """
            
            return self._get_comment(1)
        
        @caption.setter
        def caption(self, val: Optional[str]):
            self._set_comment(1, val)                
        
        @property
        def title(self) -> Optional[str]:
            """
            Returns or sets the image's title.
            
            Setting this to ``None`` will delete the corresponding row in
            ImageComments.
            """
            return self._get_comment(3)
        
        @title.setter
        def title(self, val: Optional[str]):
            self._set_comment(3, val)
        
        # Relationship to ImageCopyright
        
        @property
        def copyright(self) -> Copyright:
            if not hasattr(self, '_copyrightObj'):
                self._copyrightObj = Copyright(self)
            return self._copyrightObj
        
        # Relationship to ImageHistory
        
        @property
        def history(self) -> 'ImageHistory':
            """
            Returns the image's history
            """
            return self._history
        
        # Relationship to ImageInformation

        @property
        def information(self) -> 'ImageInformation':
            """
            Returns some of the image's information.
            """
            return self._information
        
        # Relationship to ImageMetadata
        
        @property
        def imagemeta(self) -> 'ImageMetadata':
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
            if pos is None:
                if self._position:
                    self.session.execute(
                        delete(self.ImagePosition)
                            .filter_by(imageid = self.id))
                    self.session.commit()
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
            self.session.commit()
        
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
        def tags(self) -> List['Tag']:
            """Returns the image's tags"""
            return self._tags
        
        # Relationship to VideoMetadata
        
        @property
        def videometa(self) -> 'VideoMetadata':
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
    """
    
    class_function = _image_class
    
    def __init__(
        self,
        parent: 'Digikam',
    ):
        super().__init__(parent)
        self.Class.ImageComment = _imagecomment_class(self.parent),
        self.Class.ImageCopyright = _imagecopyright_class(self.parent),
        self.Class.ImageHistory = _imagehistory_class(self.parent),
        self.Class.ImageInformation = _imageinformation_class(self.parent),
        self.Class.ImageMetadata = _imagemetadata_class(self.parent),
        self.Class.ImagePosition = _imageposition_class(self.parent),
        self.Class.VideoMetadata = _videometadata_class(self.parent)
        self.Class.properties_table = Table(
            'ImageProperties',
            parent.base.metadata,
            autoload_with = self.engine)
    
    def find(self, name: os.PathLike) -> Optional['Image']:
        """
        Finds an Image by name.
        
        Args:
            name:   filename of the image
        """
        
        # 
        base = os.path.basename(name)
        path = os.path.abspath(name)
        
        # Seleft images with correct name:
        found = self.select(name = base)
        
        # Look for image that is the same file as path:
        if os.path.isfile(path):
            for img in found:
                # Return image if it is the same file
                if (
                    os.path.isfile(img.abspath) and
                    os.path.samefile(img.abspath, path)
                ):
                    return img
        
        # Look for path:
        for img in found:
            if (img.abspath == path):
                return img
        
        # If nothing was found, return None
        return None
