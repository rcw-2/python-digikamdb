Tutorial
=========

This document assumes that you are reasonably familiar with Digikam. If using
MySQL, some knowledge about MySQL database setup and user management is
helpful. You need not be an expert - if you managed to set up the database for
Digikam, you should be fine. While Digikam-DB tries to encapsulate most of the
internal database structure, a basic understanding of relational databases and
the :doc:`SQLAlchemy ORM <sqla:orm/quickstart>` is also helpful.


Accessing Digikam Databases
----------------------------

Digikam uses a SQLite or MySQL database to store its metadata. Access to the
database is provided by the :class:`~digikamdb.conn.Digikam` class. There are
several ways to specify the Digikam database:

#.  Digikam-DB can use the Digikam configuration:
    
    .. code-block:: python
        
        from digikamdb import Digikam
        dk = Digikam('digikamrc')
    
#.  Use a database URL suitable for SQLAlchemy's :func:`~sqlalchemy.create_engine`
    function. For example, the default location (SQLite database) can be accessed
    with
    
    .. code-block:: python
        
        import os
        from digikamdb import Digikam
        dk = Digikam('sqlite:///' + os.path.expanduser('~/Pictures/digikam4.db'))
    
    A MySQL database on a DB server can be accessed with
    
    .. code-block:: python
        
        from digikamdb import Digikam
        dk = Digikam('mysql+pymysql://user:passwd@mysql.mydomain.org/mydatabase')
    
    For specification of the database, use the values you entered in the
    Digikam database configuration. With MySQL, you can also use a different
    user with reduced rights (e.g. only ``SELECT`` and ``SHOW VIEW``) to keep
    your database safe. 
    
#.  You can also use a previously created SQLAlchemy :class:`~sqlalchemy.engine.Engine`
    object. This example uses the same database as the previous one:
    
    .. code-block:: python
        
        from sqlalchemy import create_engine
        from digikamdb import Digikam
        engine = create_engine('mysql+pymysql://user:passwd@mysql.mydomain.org/mydatabase')
        dk = Digikam(engine)

.. seealso::
    
    * `Digikam Database Settings <https://docs.kde.org/trunk5/en/digikam-doc/digikam/using-setup.html#using-setup-database>`_
    * :class:`~digikamdb.conn.Digikam` Class Reference


General API Structure
----------------------

Data stored in the database can be accessed through properties of the Digikam
class, as described in the following chapters. The properties are

* :attr:`~digikamdb.conn.Digikam.images`
* :attr:`~digikamdb.conn.Digikam.albums`
* :attr:`~digikamdb.conn.Digikam.albumRoots`
* :attr:`~digikamdb.conn.Digikam.tags`
* :attr:`~digikamdb.conn.Digikam.settings`

With the exception of ``settings``, these properties behave alike:

* The properties are iterable, yielding objects of the respective type
  (:class:`~_sqla.Image`, :class:`~_sqla.Album`, :class:`_sqla.AlbumRoot`
  or :class:`~_sqla.Tag`). These classes are mapped to the respective database
  tabley by SQLAlchemy.
* Individual objects can be accessed by their id via the ``[]`` operator. Some
  classes allow additional values for ``[]`` or offer methods to find objects
  with certain values.
* Related objects can be accessed through properties of the original object,
  e.g. an image's tags are stored in ``image.tags``. These properties are
  lists or SQLAlchemy :class:`~sqlalchemy.orm.Query` objects. The latter are
  iterable, but can be further refined (see below).
* If you need access to the mapped class for an object type, it is stored in
  the ``property.Class`` of the appropriate ``Digikam`` property.

See the API documentation for details.

SQLAlchemy Query Objects
~~~~~~~~~~~~~~~~~~~~~~~~~

SQLAlchemy :class:`~sqlalchemy.orm.Query` objects contain a database query
that has not yet been executed, so the query can be modified by adding method
calls to adjust the result to require less post-processing by code. The
available methods include:

:`~sqlalchemy.orm.Query.filter`:meth::      Sets a ``WHERE`` clause
:`~sqlalchemy.orm.Query.filter_by`:meth::   Filters by attributes
:`~sqlalchemy.orm.Query.order_by`:meth::    Sorts the result
:`~sqlalchemy.orm.Query.first`:meth::       Returns the first result
:`~sqlalchemy.orm.Query.one`:meth::         Returns exactly one object
:`~sqlalchemy.orm.Query.one_or_none`:meth:: Returns one object, or ``None``
:`~sqlalchemy.orm.Query.all`:meth::         Returns the whole result as a list.

See the :class:`~sqlalchemy.orm.Query` documentation for more information.


Working with Images
--------------------

.. note::
    Digikam-DB does not directly support creating new images, or deleting
    existing ones.

Retrieving Images
~~~~~~~~~~~~~~~~~~

Images can be accessed through the :attr:`~digikamdb.conn.Digikam.images`
property of the ``Digikam`` class in different ways (``dk`` is a ``Digikam``
object, see above):

#. Iterating over all images:
    
    .. code-block:: python
        
        for image in dk.images:
            print(image.id, image.name, image.abspath)

#. Via the ``[]`` operator:
    
    .. code-block:: python
        
        image = dk.images[23]               # id == 23
    
    To access images by name, use the ``find`` method.

#. Via the :meth:`~digikamdb.tags.Images.find` method:
    
    .. code-block:: python
        
        for image in dk.images.find('/path/to/dir/with/images'):
            print(image.id, image.name, image.abspath)
    
    ``find`` searches a path (which can be a directory or a file) and returns
    a list of all matching images.

#. Via a the :meth:`~digikamdb.images.images.select` method:
    
    .. code-block:: python
        
        # Find all images named 'my_image.jpg'
        imglist = dk.images.select(name = 'my_image.jpg')
        
        # Find all images larger than 3MB:
        imglist = dk.images.select('fileSize > 3000000')
        
        # Find all images modified in 2020 or later:
        imglist = dk.images.select("modificationDate >= '2020-01-01 00:00:00'")
    
    :meth:`~digikamdb.images.images.select` supports the following attributes:
    
    * :attr:`~_sqla.Image.id`
    * :attr:`~_sqla.Image.album` (numeric field containing the album id)
    * :attr:`~_sqla.Image.name`
    * :attr:`~_sqla.Image.status`
    * :attr:`~_sqla.Image.category`
    * :attr:`~_sqla.Image.modificationDate`
    * :attr:`~_sqla.Image.fileSize`
    * :attr:`~_sqla.Image.uniqueHash`
    * :attr:`~_sqla.Image.manualOrder`

.. todo:: Describe modifying images


Working with Albums
---------------------

Albums in Digikam are actually directories in the file system. They are shown
as a tree in digikam, but the database does not reflect that.

.. note::
    Digikam-DB does not directly support creating new albums, or deleting
    existing ones.

.. todo:: Albums Tutorial


Working with Tags
-----------------------------

Digikam keeps a table of all defined tags with their properties, and another
table containing the assignment of tags to images (or vice versa). Thus tags
can be accessed globally or as tags assigned to an image.

Accessing Globally Defined Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tags can be accessed through the :attr:`~digikamdb.conn.Digikam.tags` property
of the ``Digikam`` class in different ways (``dk`` is a ``Digikam`` object,
see above):

#. Iterating over all tags:
    
    .. code-block:: python
        
        for tag in dk.tags:
            print(tag.id, ':', tag.name)

#. Via the ``[]`` operator:
    
    .. code-block:: python
        
        tag = dk.tags[23]               # by id
        tag = dk.tags['My Tag']         # by name
        tag = dk.tags['parent/child']   # by hierarchical name
    
    To access a tag by name this way, the name has to be unique, or an
    exception is raised. To access tags by a non-unique name, use the
    ``find`` method.
    
    If no matching tag is found, an Exception is raised.

#. Via a SELECT with certain attributes:
    
    .. code-block:: python
        
        for tag in dk.tags.select(name = 'My Tag'):
            print(tag.hierarchicalname())

New tags can be created with the :meth:`~digikamdb.tags.Tags.add` method:

.. code-block:: python
    
    # Tag at top level without an icon
    my_tag = dk.tags.add('My Tag', 0)
    
    # Tag with parent Friends and KDE icon tag-people
    chris = dk.tags.add('Chris', dk.tags['Friends'], 'tag-people')

The optional third argument specifies the tag's icon. It can be an ``Image``
obect, an ``int`` or a ``str``. When given as a ``str``, the icon is assumed
to be a KDE icon specifier. Otherwise, it should be an image from the
database.

Accessing an Image's Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~

The tags of an image are stored in its :attr:`~_sqla.Image.tags` property
(``img`` is an ``Image`` object, see above):

.. code-block:: python
    
    for tag in img.tags:
        print(tag.name)

The ``tags`` property is actually a :class:`~sqlalchemy.orm.Query` object, so
you can refine it further:

.. code-block:: python
    
    # Iterate over all tags that have the KDE icon tag-people
    for tag in img.tags.filter_by(iconkde = 'tag-people'):
        print('Tag', tag.name, 'has icon <tag-people>')
    
    # Get the tag with id 42, or None if the image has no such tag
    forty_two = img.tags.filter_by(_id = 42).one_or_none()

A :class:`~_sqla.Tag` object also has an :attr:`~_sqla.Tag.images` property
containing all Images that have the tag set:

.. code-block:: python
    
    #
    for img in dk.tags['My Tag'].images.filter_by(_album = 42):
        print('Image', img.name, 'has tag <My Tag>')

.. todo:: Describe modifying tags

.. seealso::
    
    * `Digikam: Managing Tags <https://docs.kde.org/trunk5/en/digikam-doc/digikam/using-digikam.html#using-mainwindow-tagsview>`_
    * :class:`~digikamdb.tags.Tags` Class Reference
    * :class:`~_sqla.Tag` (mapped table) Class Reference


Managing Settings
------------------

.. todo:: Settings tutorial

