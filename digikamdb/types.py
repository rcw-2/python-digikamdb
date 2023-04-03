"""Some auxilliary class definitions"""


from enum import IntEnum
from typing import Any, Mapping, Union


class AlbumRootStatus(IntEnum):
    """Class for :attr:`AlbumRoot.status<_sqla.AlbumRoot.status>`"""
    LocationAvailable   = 0
    LocationUnavailable = 2
    LocationHidden      = 1


class AlbumRootType(IntEnum):
    """Class for :attr:`AlbumRoot.type<_sqla.AlbumRoot.type>`"""
    UndefinedType   = 0
    VolumeHardWired = 1
    VolumeRemovable = 2
    Network         = 3


class ImageCategory(IntEnum):
    """Class for :attr:`Image.category<_sqla.Image.category>`"""
    UndefinedCategory   = 0
    Image               = 1
    Video               = 2
    Audio               = 3
    Other               = 4


class ImageStatus(IntEnum):
    """Class for :attr:`Image.status<_sqla.Image.status>`"""
    UndefinedStatus = 0
    Visible         = 1
    Hidden          = 2
    Trashed         = 3
    Obsolete        = 4


class ImageColorModel(IntEnum):
    """
    Digikam Color Model
    
    Used by :attr:`ImageInformation.colorModel<_sqla.ImageInformation.colorModel>`"""
    COLORMODELUNKNOWN   = 0
    RGB                 = 1
    GRAYSCALE           = 2
    MONOCHROME          = 3
    INDEXED             = 4
    YCBCR               = 5
    CMYK                = 6
    CIELAB              = 7
    COLORMODELRAW       = 8


class ExifOrientation(IntEnum):
    """
    Exif ImageOrientation Tag
    
    The constants describe the position of row 0 and column 0 in the visual
    image, as specified in the Exif documentation. The mirrored orientations
    will usually not show up in digital photos.
    
    Used by :attr:`ImageInformation.orientation<_sqla.ImageInformation.orientation>`
    """
    #: Landscape, camera held upright
    TOP_LEFT        = 1
    #: 1 mirrored
    TOP_RIGHT       = 2
    #: Landscape, camera held upside down
    BOTTOM_RIGHT    = 3
    #: 3 mirrored
    BOTTOM_LEFT     = 4
    #: 6 mirrored
    LEFT_TOP        = 5
    #: Portrait, camera turned right
    RIGHT_TOP       = 6
    #: 8 mirrored
    RIGHT_BOTTOM    = 7
    #: Portrait, camera turned left
    LEFT_BOTTOM     = 8


class ExifExposureMode(IntEnum):
    """
    Exif ExposureMode Tag
    
    Used by :attr:`ImageMetadata.exposureMode<_sqla.ImageMetadata.exposureMode>`
    """
    AUTO_EXPOSURE   = 0
    MANUAL_EXPOSURE = 1
    AUTO_BRACKET    = 2


class ExifExposureProgram(IntEnum):
    """
    Exif ExposureProgram Tag
    
    Used by :attr:`ImageMetadata.exposureProgram<_sqla.ImageMetadata.exposureProgram>`
    """
    NOT_DEFINED         = 0
    MANUAL              = 1
    NORMAL_PROGRAM      = 2
    APERTURE_PRIORITY   = 3
    SHUTTER_PRIORITY    = 4
    CREATIVE_PROGRAM    = 5
    ACTION_PROGRAM      = 6
    PORTRAIT_MODE       = 7
    LANDSCAPE_MODE      = 8


class ExifWhiteBalance(IntEnum):
    """
    Exif WhiteBalance Tag
    
    Used by :attr:`ImageMetadata.whiteBalance<_sqla.ImageMetadata.whiteBalance>`
    """
    AUTO    = 0
    MANUAL  = 1


class ExifMeteringMode(IntEnum):
    """
    Exif MeteringMode Tag
    
    Used by :attr:`ImageMetadata.meteringMode<_sqla.ImageMetadata.meteringMode>`
    """
    UNKNOWN                 = 0
    AVERAGE                 = 1
    CENTER_WEIGHTED_AVERAGE = 2
    SPOT                    = 3
    MULTI_SPOT              = 4
    PATTERN                 = 5
    PARTIAL                 = 6
    OTHER                   = 255


class ExifSubjectDistanceRange(IntEnum):
    """
    Exif SubjectDistanceRange
    
    Used by
    :attr:`ImageMetadata.subjectDistanceCategory<_sqla.ImageMetadata.subjectDistanceCategory>`
    """                                                     # noqa: E501
    UNKNOWN         = 0
    MACRO           = 1
    CLOSE_VIEW      = 2
    DISTANT_VIEW    = 3


class ExifFlashReturn(IntEnum):
    """Exif Flash Return (part of :class:`ExifFlash` Tag)"""
    NO_STROBE_RETURN_DETECTION_FUNCTION = 0
    RESERVED                            = 1
    STROBE_RETURN_LIGHT_DETECTED        = 2
    STROBE_RETURN_LIGHT_NOT_DETECTED    = 3


class ExifFlashMode(IntEnum):
    """Exif Flash Mode (part of :class:`ExifFlash` Tag)"""
    UNKNOWN                         = 0
    COMPULSORY_FLASH_FIRING         = 1
    COMPULSORY_FLASH_SUPPRESSION    = 2
    AUTO_MODE                       = 3


class ExifFlash:
    """
    Exif Flash Tag
    
    Used by :attr:`ImageMetadata.flash<_sqla.ImageMetadata.flash>`
    
    Args:
        value:  The :class:`int` value of flash tag, or a :class:`dict`
                containing the flash information.
    """
    def __init__(
        self,
        value: Union[int, Mapping]
    ):
        if isinstance(value, int):
            self._value = value
        elif isinstance(value, dict):
            self._value = 0
            if 'flash_fired' in value and value['flash_fired']:
                self._value |= 1
            if 'flash_return' in value and value['flash_return']:
                self._value |= (value['flash_return'] << 1)
            if 'flash_mode' in value and value['flash_mode']:
                self._value |= (value['flash_mode'] << 3)
            if 'flash_function' in value and not value['flash_function']:
                self._value |= 32
            if 'red_eye_reduction' in value and value['red_eye_reduction']:
                self._value |= 64
        else:
            raise TypeError('Flash constructor Argument must be int or dict')
    
    def __int__(self):
        return self._value
    
    def __eq__(self, other: Any):
        return other == self._value
    
    @property
    def flash_fired(self) -> bool:
        """Indicates if the flash fired."""
        return bool(self._value & 1)
    
    @property
    def flash_return(self) -> ExifFlashReturn:
        """Status of returned light"""
        return ExifFlashReturn((self._value >> 1) & 3)
    
    @property
    def flash_mode(self) -> ExifFlashMode:
        """Flash mode"""
        return ExifFlashMode((self._value >> 3) & 3)
    
    @property
    def flash_function(self) -> bool:
        """Flash function supported?"""
        return not bool((self._value >> 5) & 1)
    
    @property
    def red_eye_reduction(self) -> bool:
        """Red eye reduction supported?"""
        return bool((self._value >> 6) & 1)


