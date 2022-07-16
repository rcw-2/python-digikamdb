SQLAlchemy mapped Classes
===========================

.. module::     docs._sqla

In order for Digikam-DB to be able to access different databases at the same
time, the mapped classes are generated at runtime. To make them available,
the classes ares stored in the ``Digikam`` properties
:attr:`~digikamdb.conn.Digikam.album_class`,
:attr:`~digikamdb.conn.Digikam.albumroot_class`,
:attr:`~digikamdb.conn.Digikam.image_class` and
:attr:`~digikamdb.conn.Digikam.tag_class`.

The classes created at runtime are:

* :class:`Album`
* :class:`AlbumRoot`
* :class:`Image`
* :class:`ImageHistory`
* :class:`ImageInformation`
* :class:`ImageMetadata`
* :class:`VideoMetadata`

Classes
--------

.. autoclass::  Album

.. autoclass::  AlbumRoot

.. autoclass::  DigikamObject

.. autoclass::  Image

.. ifconfig::   include_private_content
    
    .. autoclass::  ImageComment
    
    .. autoclass::  ImageCopyright
    
.. autoclass::  ImageHistory

.. autoclass::  ImageInformation

.. autoclass::  ImageMetadata

.. ifconfig::   include_private_content
    
    .. autoclass::  ImagePosition

.. autoclass::  Tag

.. autoclass::  VideoMetadata


