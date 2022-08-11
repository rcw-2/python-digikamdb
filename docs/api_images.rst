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

.. currentmodule::  digikamdb.images

.. autoclass::  Category
    :members:
    :member-order:  bysource

.. autoclass::  Status
    :members:
    :member-order:  bysource

.. currentmodule::  digikamdb.image_helpers

.. autoclass::  ExposureMode
    :members:
    :member-order:  bysource

.. autoclass::  ExposureProgram
    :members:
    :member-order:  bysource

.. autoclass::  Flash
    :members:
    :member-order:  bysource

.. autoclass::  FlashMode
    :members:
    :member-order:  bysource

.. autoclass::  FlashReturn
    :members:
    :member-order:  bysource

.. autoclass::  Orientation
    :members:
    :member-order:  bysource

.. autoclass::  WhiteBalance
    :members:
    :member-order:  bysource




