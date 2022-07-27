"""
Helper classes and functions for Digikam images.
"""

import logging
import os
from datetime import datetime
from itertools import groupby
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from sqlalchemy import Column, Integer, String, delete, text
from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .properties import BasicProperties


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
    _parent_id_col = 'imageid'
    
    #: Key column
    _key_col = 'property'
    
    #: Value column
    _value_col = 'value'


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
    _key_col = ('property', 'value', 'extraValue')
    
    #: Value columns
    _value_col = ('value', 'extraValue')
    
    def __getitem__(
        self,
        prop: Union[str, int, Iterable, None]
    ) -> Union[str, List, Tuple, None]:
        ret = []
        ret = [
            self._post_process_value(entry)
            for entry in self._select(**self._key_col_kwargs(prop))
        ]
        if len(ret) == 0:
            return None
        if len(ret) == 1:
            return ret[0]
        return ret
    
    def __setitem__(self, key: Any, value: Optional[Union[str, Sequence[Tuple]]]):
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
        elif isinstance(value, tuple):
            value = [value]
        for v, ev in value:
            kwargs = self._key_col_kwargs(
                key,
                **{'value': v, 'extraValue': ev},
            )
            log.debug('- Setting value %s, %s', v, ev)
            self._insert(**kwargs)

    def items(self) -> Iterable:
        for prop, rows in groupby(
            self._select_self().order_by(text('property')),
            lambda x: x.property,
        ):
            value = [self._post_process_value(row) for row in rows]
            if len(value) == 0:
                value = None
            if len(value) == 1:
                value = value[0]
                if value[1] is None:
                    value = value[0]
            yield prop, value
    
    def _key_col_kwargs(self, prop: Any, **kwargs) -> Mapping[str, Any]:
        # Strip NULL values
        ret = {}
        for k, v in super()._key_col_kwargs(prop).items():
            if v is None:
                log.debug('Discarding key %s', k)
            else:
                ret[k] = v
        ret.update(kwargs)
        if not 'property' in ret:
            raise KeyError('Search term must contain `property`')
        return ret
    
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


def define_image_helper_tables(container: 'Images'):        # noqa: F821
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
            date = Column(sqlite.DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
    
    class ImageCopyrightEntry(dk.base):
        """
        Digikam Image Copyright
        """
        __tablename__ = 'ImageCopyright'
    
    class ImageHistory(dk.base):
        """
        Digikam Image History

        The following column-related properties can be directly accessed:
        
        * **imageid** (*int*)
        * **uuid** (*str*)
        * **history** (*str*)
        """
        __tablename__ = 'ImageHistory'
    
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
        
        @validates('rating')
        def _validate_rating(self, key: int, value: int) -> int:
            if value < -1 or value > 5:
                raise ValueError('Image rating must be from -1 to 5')
            return value
        
        if not dk.is_mysql:
            creationDate = Column(sqlite.DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
            digitizationDate = Column(sqlite.DATETIME(
                storage_format = '%(year)04d-%(month)02d-%(day)02dT%(hour)02d:%(minute)02d:%(second)02d',   # noqa: E501
                regexp = r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)'))
    
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
        
        # Retrieve double as float
        if dk.is_mysql:
            aperture = Column(mysql.DOUBLE(asdecimal = False))
            focalLength = Column(mysql.DOUBLE(asdecimal = False))
            focalLength35 = Column(mysql.DOUBLE(asdecimal = False))
            exposureTime = Column(mysql.DOUBLE(asdecimal = False))
            subjectDistance = Column(mysql.DOUBLE(asdecimal = False))
    
    class ImagePosition(dk.base):
        """
        Contains the Image's position.
        
        Should be accessed through :attr:`Image.position`.
        """
        __tablename__ = 'ImagePositions'
        
        # Retrieve double as float
        if dk.is_mysql:
            latitudeNumber = Column(mysql.DOUBLE(asdecimal = False))
            longitudeNumber = Column(mysql.DOUBLE(asdecimal = False))
            altitude = Column(mysql.DOUBLE(asdecimal = False))
            orientation = Column(mysql.DOUBLE(asdecimal = False))
            tilt = Column(mysql.DOUBLE(asdecimal = False))
            roll = Column(mysql.DOUBLE(asdecimal = False))
            accuracy = Column(mysql.DOUBLE(asdecimal = False))
    
    class ImageProperty(dk.base):
        """
        Image Properties
        
        This table should be accessed via
        Class :class:`~digikamdb.images.ImageProperties`.
        """
        __tablename__ = 'ImageProperties'
        
        imageid = Column(Integer, primary_key = True)
        property = Column(String, primary_key = True)
    
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
    
    # Set the properties:
    container.ImageComment = ImageComment
    container.ImageCopyrightEntry = ImageCopyrightEntry
    container.ImageHistory = ImageHistory
    container.ImageInformation = ImageInformation
    container.ImageMetadata = ImageMetadata
    container.ImagePosition = ImagePosition
    container.ImageProperty = ImageProperty
    container.VideoMetadata = VideoMetadata

