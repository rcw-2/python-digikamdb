"""
Helper classes and functions for Digikam images.
"""

import logging
import os
from datetime import datetime
from enum import IntEnum, IntFlag
from itertools import groupby
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from sqlalchemy import Column, Integer, String, delete, text
from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .properties import BasicProperties
from .exceptions import DigikamQueryError, DigikamAssignmentError
from .types import (
    ExifExposureMode as ExposureMode,
    ExifExposureProgram as ExposureProgram,
    ExifFlash as Flash,
    ExifMeteringMode as MeteringMode,
    ExifOrientation as Orientation,
    ExifSubjectDistanceRange as SubjectDistanceRange,
    ExifWhiteBalance as WhiteBalance,
    ImageColorModel as ColorModel
)
    


log = logging.getLogger(__name__)


def _imagecopyrightentry_class(dk: 'Digikam') -> type:      # noqa: F821
    """Returns the ImageCopyrightEntry class."""
    return dk.images.ImageCopyrightEntry


def _imageproperty_class(dk: 'Digikam') -> type:            # noqa: F821
    """Returns the TagProperty class."""
    return dk.images.ImageProperty


class ImageProperties(BasicProperties):
    """
    Image Properties
    
    Objects of this type are normally accessed through an :class:`Image`
    object, see :attr:`~Image.properties`. In general, it is not necessary
    to call the constructor directly.
    
    Individual properties can be retrieved and set dict-like vie the ``[]``
    operator. The method :meth:`~ImageProperties.items` iterates over all
    properties and yields (key, value) tuples.
    
    Args:
        parent:     Image object the properties belong to.
    """
    
    # Funktion returning the table class
    _class_function = _imageproperty_class
    
    #: Parent id column
    _parent_id_col = '_imageid'
    
    #: Key column
    _key_col = '_property'
    
    #: Value column
    _value_col = '_value'


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
    _parent_id_col = '_imageid'
    
    #: Key column
    _key_col = ('_property', '_value', '_extraValue')
    
    #: Value columns
    _value_col = ('_value', '_extraValue')
    
    #: Return ``None`` when select does not find a row
    _raise_on_not_found = False
    
    #: Remove item when set to ``None``
    _remove_on_set_none = True
    
    def __getitem__(
        self,
        prop: Union[str, int, Iterable]
    ) -> Union[str, List, Tuple, None]:
        ret = [
            self._post_process_value(entry)
            for entry in self._select_prop(prop)
        ]
        if len(ret) == 0:
            return None
        if len(ret) == 1:
            return ret[0]
        return ret
    
    def __setitem__(
        self,
        prop: Union[str, int, Iterable],
        value: Union[str, Tuple, Sequence[Tuple], None]
    ):
        log.debug(
            'Setting copyright info %s of image %d (%s)',
            prop,
            self._parent.id,
            self._parent.name
        )
        self.remove(prop)
        
        if value is None:
            log.debug('Setting to None - removing values')
            return
        
        log.debug('Setting values:')
        if isinstance(value, str):
            value = [(value, None)]
        elif isinstance(value, tuple):
            value = [value]
        
        kwargs = self._key_kwargs(prop)
        kwargs.update({self._parent_id_col: self._parent.id})
        for v, ev in value:
            log.debug('- Setting value %s, %s', v, ev)
            kwargs.update(value = v, extraValue = ev)
            self._insert(**kwargs)

    def items(self) -> Iterable:
        for prop, rows in groupby(
            self._select_self().order_by(text('property')),
            lambda x: x._property,
        ):
            value = [self._post_process_value(row) for row in rows]
            if len(value) == 0:
                value = None
            if len(value) == 1:
                value = value[0]
                if value[1] is None:
                    value = value[0]
            yield prop, value
    
    def remove(self, prop: Union[str, int, Iterable]):
        """
        Removes the given property.
        
        Args:
            prop:   Property to remove.
        """
        log.debug(
            'Removing %s[%s] from %d',
            self.__class__.__name__,
            prop,
            self._parent.id,
        )
        for row in self._select_prop(prop):
            self._session.delete(row)
    
    def _key_kwargs(self, prop: Union[str, int, Iterable]):
        """Prepare kwargs for key"""
        kwargs = {}
        for k, v in dict(zip(self._key_col, self._pre_process_key(prop))).items():
            if v is None:
                log.debug('Discarding key %s', k)
            else:
                kwargs[k] = v
        
        if not '_property' in kwargs:
            raise DigikamQueryError('Search term must contain `property`')
        
        return kwargs
        
    def _select_prop(
        self,
        prop: Union[str, int, Iterable, None]
    ) -> '~sqlalchemy.orm.Query':                           # noqa: F821
        """Selects a specific property."""
        return self._select_self().filter_by(**self._key_kwargs(prop))

    def _post_process_value(
        self,
        obj: 'DigikamObject'                                # noqa: F821
    ) -> Union[str, int, Tuple, None]:
        """
        Postprocesses values from [] operations.
        """
        val = super()._post_process_value(obj)
        
        # Only return value if extraValue is None:
        if val[1] is None:
            return val[0]
        
        return val


def define_image_helper_tables(container: 'Images'):        # noqa: F821, C901
    """Defines the classes for helper tables."""
    
    dk = container.digikam
    
    if dk.is_mysql:
        from sqlalchemy.dialects import mysql
    else:
        from sqlalchemy.dialects import sqlite
        
    
    class ImageComment(dk.base):
        """
        Digikam Image Comment
        
        Data in this table should be accessed through the ``Image`` properties
        :attr:`~Image.caption` and :attr:`~Image.title`.
        """
        __tablename__ = 'ImageComments'
    
        if not dk.is_mysql:
            _date = Column('date', sqlite.DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'
            ))
    
    class ImageCopyrightEntry(dk.base):
        """
        Digikam Image Copyright
        """
        __tablename__ = 'ImageCopyright'
    
    class ImageHistory(dk.base):
        """
        Digikam Image History
        """
        __tablename__ = 'ImageHistory'
        
        @property
        def uuid(self) -> str:
            """ImageHistory.uuid (read-only)"""
            return self._uuid
        
        @property
        def history(self) -> str:
            """
            The image's history data (read-only)
            
            If not None, this field contains XML data describing previous
            versions of the image.
            """
            return self._history
    
    class ImageInformation(dk.base):
        """
        Represents a row of the `ImageInformation` table.
        
        This data comes from the image file and should not be changed, with the
        exception of :attr:`~ImageInformation.rating`.
        """
        __tablename__ = 'ImageInformation'
        
        @validates('_rating')
        def _validate_rating(self, key: int, value: int) -> int:
            if value < -1 or value > 5:
                raise DigikamAssignmentError('Image rating must be from -1 to 5')
            return value
        
        if not dk.is_mysql:
            _creationDate = Column(
                'creationDate',
                sqlite.DATETIME(
                    storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                    regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'
                )
            )
            _digitizationDate = Column(
                'digitizationDate',
                sqlite.DATETIME(
                    storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                    regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'
                )
            )
        
        @property
        def rating(self) -> int:
            """The image's rating (from -1 to 5)"""
            return self._rating
        
        @rating.setter
        def rating(self, value: int):
            self._rating = value
        
        @property
        def creationDate(self) -> datetime:
            """The image's creation date (read-only)"""
            return self._creationDate
        
        @property
        def digitizationDate(self) -> datetime:
            """The image's digitization date (read-only)"""
            return self._digitizationDate
        
        @property
        def orientation(self) -> Optional[Orientation]:
            """The image's orientation (read-only)"""
            if self._orientation:
                return Orientation(self._orientation)
            else:
                return None
        
        @property
        def width(self) -> int:
            """The image's width (read-only)"""
            return self._width
        
        @property
        def height(self) -> int:
            """The image's height (read-only)"""
            return self._height
        
        @property
        def format(self) -> str:
            """The image's file format (read-only)"""
            return self._format
        
        @property
        def colorDepth(self) -> int:
            """The image's color depth (read-only)"""
            return self._colorDepth
        
        @property
        def colorModel(self) -> Optional[ColorModel]:
            """The image's color model (read-only)"""
            if self._colorModel is None:
                return None
            else:
                return ColorModel(self._colorModel)
        
        @validates('_orientation', '_colorModel')
        def _convert_to_int(self, key, value):
            return int(value)
    
    class ImageMetadata(dk.base):
        """
        Represents a row of the ``ImageMetadata`` table.
        
        This object contains Exif information of the corresponding image.
        """
        __tablename__ = 'ImageMetadata'
        
        # Retrieve double as float
        if dk.is_mysql:
            _aperture = Column('aperture', mysql.DOUBLE(asdecimal = False))
            _focalLength = Column('focalLength', mysql.DOUBLE(asdecimal = False))
            _focalLength35 = Column('focalLength35', mysql.DOUBLE(asdecimal = False))
            _exposureTime = Column('exposureTime', mysql.DOUBLE(asdecimal = False))
            _subjectDistance = Column('subjectDistance', mysql.DOUBLE(asdecimal = False))
        
        @property
        def make(self) -> Optional[str]:
            """Camera's manufacturer"""
            return self._make
        
        @property
        def model(self) -> Optional[str]:
            """Camera model"""
            return self._model
        
        @property
        def lens(self) -> Optional[str]:
            """Lens model"""
            return self._lens
        
        @property
        def aperture(self) -> Optional[float]:
            """The image's aperture value/f-number (read-only)"""
            return self._aperture
        
        @property
        def focalLength(self) -> Optional[float]:
            """The image's focal length (read-only)"""
            return self._focalLength
        
        @property
        def focalLength35(self) -> Optional[float]:
            """The image's 35mm-equivalent focal length (read-only)"""
            return self._focalLength35
        
        @property
        def exposureTime(self) -> Optional[float]:
            """The image's exposure time (read-only)"""
            return self._exposureTime
        
        @property
        def exposureProgram(self) -> Optional[ExposureProgram]:
            """The image's exposure program (read-only)"""
            if self._exposureProgram is None:
                return None
            return ExposureProgram(self._exposureProgram)
        
        @property
        def exposureMode(self) -> Optional[ExposureMode]:
            """The image's exposure mode (read-only)"""
            if self._exposureMode is None:
                return None
            return ExposureMode(self._exposureMode)
        
        @property
        def sensitivity(self) -> Optional[int]:
            """Photographic sensitivity (ISO number)"""
            return self._sensitivity
        
        @property
        def flash(self) -> Optional[Flash]:
            """Information about flash usage"""
            if self._flash is None:
                return None
            return Flash(self._flash)
        
        @property
        def whiteBalance(self) -> Optional[WhiteBalance]:
            """White balance mode"""
            if self._whiteBalance is None:
                return None
            return WhiteBalance(self._whiteBalance)
        
        @property
        def whiteBalanceColorTemperature(self) -> Optional[int]:
            """Color temperature for manual white balance"""
            return self._whiteBalanceColorTemperature
        
        @property
        def meteringMode(self) -> Optional[MeteringMode]:
            """The image's metering mode"""
            if self._meteringMode is None:
                return None
            return MeteringMode(self._meteringMode)
        
        @property
        def subjectDistance(self) -> Optional[float]:
            """Distance to subject, as measured by the camera"""
            return self._subjectDistance
        
        @property
        def subjectDistanceCategory(self) -> Optional[SubjectDistanceRange]:
            """Exif SubjectDistanceRange attribute"""
            if self._subjectDistanceCategory is None:
                return None
            return SubjectDistanceRange(self._subjectDistanceCategory)
    
        @validates(
            '_exposureMode', '_exposureProgram',
            '_flash',
            '_meteringMode',
            '_subjectDistanceCategory',
            '_whiteBalance'
        )
        def _convert_to_int(self, key: str, value: int):
            return int(value)
        
    class ImagePosition(dk.base):
        """
        Contains the Image's position.
        
        Should be accessed through :attr:`Image.position`.
        """
        __tablename__ = 'ImagePositions'
        
        # Retrieve double as float
        if dk.is_mysql:
            _latitudeNumber = Column(
                'latitudeNumber',
                mysql.DOUBLE(asdecimal = False)
            )
            _longitudeNumber = Column(
                'longitudeNumber',
                mysql.DOUBLE(asdecimal = False)
            )
            _altitude = Column(
                'altitude',
                mysql.DOUBLE(asdecimal = False)
            )
            _orientation = Column(
                'orientation',
                mysql.DOUBLE(asdecimal = False)
            )
            _tilt = Column(
                'tilt',
                mysql.DOUBLE(asdecimal = False)
            )
            _roll = Column(
                'roll',
                mysql.DOUBLE(asdecimal = False)
            )
            _accuracy = Column(
                'accuracy',
                mysql.DOUBLE(asdecimal = False)
            )
    
    class ImageProperty(dk.base):
        """
        Image Properties
        
        This table should be accessed via
        Class :class:`~digikamdb.images.ImageProperties`.
        """
        __tablename__ = 'ImageProperties'
        
        _imageid = Column('imageid', Integer, primary_key = True)
        _property = Column('property', String, primary_key = True)
    
    class VideoMetadata(dk.base):
        """
        Digikam Video Metadata
        
        This object contains Video metadata of the corresponding
        :class:`Image` object.
        """
        __tablename__ = 'VideoMetadata'
        
        @property
        def aspectRatio(self) -> str:
            return self._aspectRatio
        
        @property
        def audioBitRate(self) -> str:
            return self._audioBitRate
        
        @property
        def audioChannelType(self) -> str:
            return self._audioChannelType
        
        @property
        def audioCompressor(self) -> str:
            return self._audioCompressor
        
        @property
        def duration(self) -> str:
            return self._duration
        
        @property
        def frameRate(self) -> str:
            return self._frameRate
        
        @property
        def exposureProgram(self) -> int:
            return self._exposureProgram
        
        @property
        def videoCodec(self) -> str:
            return self._videoCodec
    
    # Set the properties:
    container.ImageComment = ImageComment
    container.ImageCopyrightEntry = ImageCopyrightEntry
    container.ImageHistory = ImageHistory
    container.ImageInformation = ImageInformation
    container.ImageMetadata = ImageMetadata
    container.ImagePosition = ImagePosition
    container.ImageProperty = ImageProperty
    container.VideoMetadata = VideoMetadata

