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
    * :class:`Digikam Class Reference <digikamdb.conn.Digikam>`


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

.. todo:: Images Tutorial


Working with Albums
---------------------

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
        
        tag = dk.tags[23]           # by id
        tag = dk.tags['My Tag']     # by name
    
    To access a tag by name this way, the name has to be unique, or an
    exception is raised. To access tags by a non-unique name, use the
    ``find`` method.

#. Via the :meth:`~digikamdb.tags.Tags.find` method:
    
    .. code-block:: python
        
        for tag in dk.tags.find('My Tag'):
            print(tag.hierarchicalname())
    
    ``find`` searches a tag by name and returns a list of all matching
    objects.

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

The ``tags`` property is actually a :class:`~sqlalchemy.orm.Query`, so you can
refine it further:

.. code-block:: python
    
    # Iterate over all tags that have the KDE icon tag-people
    for tag in img.tags.filter_by(iconkde = 'tag-people'):
        print('Tag', tag.name, 'has icon <tag-people>')
    
    # Get the tag with id 42, or None if the image has no such tag
    forty_two = img.tags.filter_by(id = 42).one_or_none()

.. todo:: Describe modifying tags

.. seealso::
    
    * `Digikam: Managing Tags <https://docs.kde.org/trunk5/en/digikam-doc/digikam/using-digikam.html#using-mainwindow-tagsview>`_
    * :class:`Tags Class Reference <digikamdb.tags.Tags>`
    * :class:`Tag (mapped table) Class Reference <_sqla.Tag>`


Managing Settings
------------------


