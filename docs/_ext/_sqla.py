"""
This module just exists to generate the documentation for table classes
"""

import os
from digikamdb import Digikam

# create Digikam instance with mostly empty database
dk = Digikam(
    'sqlite:///'
    + os.path.abspath(os.path.join(os.path.dirname(__file__), 'digikam4.db'))
)

DigikamObject       = dk.base
AlbumRoot           = dk.albumRoots.Class
Album               = dk.albums.Class
Tag                 = dk.tags.Class
TagProperty         = dk.tags.TagProperty
Setting             = dk.settings.Class
Image               = dk.images.Class
ImageComment        = dk.images.ImageComment
ImageCopyrightEntry = dk.images.ImageCopyrightEntry
ImageHistory        = dk.images.ImageHistory
ImageInformation    = dk.images.ImageInformation
ImageMetadata       = dk.images.ImageMetadata
ImagePosition       = dk.images.ImagePosition
ImageProperty       = dk.images.ImageProperty
VideoMetadata       = dk.images.VideoMetadata

