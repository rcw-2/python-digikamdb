API for Images
===============


.. module:: digikamdb.images

The Images Class
-----------------

.. autoclass:: Images
   :members:


The Image Class (mapped)
-------------------------

.. autoclass:: _sqla.Image
   :members:


.. module:: digikamdb.image_comments

Image Comments
-----------------

.. autoclass:: ImageComments
    :no-show-inheritance:
    :members:

.. autoclass:: ImageTitles
    :members:

.. autoclass:: ImageCaptions
    :members:

.. ifconfig::   include_private_content
    
    .. autoclass::  _sqla.ImageComment
        :members:


.. module:: digikamdb.image_helpers

Image Properties
-----------------

.. autoclass:: ImageProperties
    :members:

.. ifconfig::   include_private_content
    
    .. autoclass::  _sqla.ImageProperty
        :members:


Copyright
----------

.. autoclass:: ImageCopyright
    :members:

.. ifconfig::   include_private_content
    
    .. autoclass:: _sqla.ImageCopyrightEntry
        :members:


Other Metadata (mapped)
------------------------

.. currentmodule::     _sqla

.. autoclass::  ImageHistory
    :members:

.. autoclass::  ImageInformation
    :members:

.. autoclass::  ImageMetadata
    :members:

.. ifconfig::   include_private_content
    
    .. autoclass::  ImagePosition
        :members:

.. autoclass::  VideoMetadata
    :members:


Types of special properties
----------------------------

.. currentmodule::  digikamdb.types

.. autoclass::  ImageCategory
    :members:
    :member-order:  bysource

.. autoclass::  ImageStatus
    :members:
    :member-order:  bysource

.. autoclass::  ImageColorModel
    :members:
    :member-order:  bysource

.. autoclass::  ExifExposureMode
    :members:
    :member-order:  bysource

.. autoclass::  ExifExposureProgram
    :members:
    :member-order:  bysource

.. autoclass::  ExifFlash
    :members:
    :member-order:  bysource

.. autoclass::  ExifFlashMode
    :members:
    :member-order:  bysource

.. autoclass::  ExifFlashReturn
    :members:
    :member-order:  bysource

.. autoclass::  ExifMeteringMode
    :members:
    :member-order:  bysource

.. autoclass::  ExifOrientation
    :members:
    :member-order:  bysource

.. autoclass::  ExifWhiteBalance
    :members:
    :member-order:  bysource




