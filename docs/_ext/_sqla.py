"""
This module just exists to generate the documentation for table classes
"""

from sqlalchemy.ext.declarative import declarative_base

from digikamdb.conn import _digikamobject_class
from digikamdb.albumroots import _albumroot_class
from digikamdb.albums import _album_class
from digikamdb.tags import _tag_class
from digikamdb.images import (
    _imagecomment_class,
    _imagecopyright_class,
    _imagehistory_class,
    _imageinformation_class,
    _imagemetadata_class,
    _imageposition_class,
    _videometadata_class,
    _image_class)


class Dummy:
    pass

# Make this an 
DigikamObject = _digikamobject_class(declarative_base())
DigikamObject.__qualname__ = '_sqla.DigikamObject'

# create fake Digikam instance
dk = Dummy()
dk.base = DigikamObject
dk.is_mysql = True
dk.engine = None
dk.session = None

AlbumRoot           = _albumroot_class(dk)
Album               = _album_class(dk)
Tag                 = _tag_class(dk)
ImageComment        = _imagecomment_class(dk)
ImageCopyright      = _imagecopyright_class(dk)
ImageHistory        = _imagehistory_class(dk)
ImageInformation    = _imageinformation_class(dk)
ImageMetadata       = _imagemetadata_class(dk)
ImagePosition       = _imageposition_class(dk)
VideoMetadata       = _videometadata_class(dk)
Image               = _image_class(dk)

