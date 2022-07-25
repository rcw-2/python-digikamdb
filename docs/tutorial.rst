Tutorial
=========

Accessing Digikam Databases
----------------------------

Digikam uses a SQLite or MySQL database to store its metadata. Access to the
database is provided by the :class:`~digikamdb.conn.Digikam` class. There are
several ways to specify the Digikam database:

#.  Digikam-DB can use the Digikam configuration:
    
    .. code-block:: python
        
        import os
        from digikamdb import Digikam
        dk = Digikam('digikamrc')
    
#.  Us a database URL suitable for SQLAlchemy's :func:`~sqlalchemy.create_engine`
    function. For example, the default location (SQLite database) can be accessed
    with
    
    .. code-block:: python
        
        from digikamdb import Digikam
        dk = Digikam('sqlite:///' + os.path.expanduser('~/Pictures/digikam4.db'))
    
    A MySQL database on a DB server can be accessed with
    
    .. code-block:: python
        
        from digikamdb import Digikam
        dk = Digikam('mysql+pymysql://user:passwd@mysql.mydomain.org/mydatabase')
    
#.  You can also use a previously created SQLAlchemy :class:`~sqlalchemy.engine.Engine`
    object. This example uses the same database as the previous one:
    
    .. code-block:: python
        
        import os
        from sqlalchemy import create_engine
        from digikamdb import Digikam
        engine = create_engine('mysql+pymysql://user:passwd@mysql.mydomain.org/mydatabase')
        dk = Digikam(engine)

The data stored in the database can be accessed through the Digikam class,
as described in the following chapters.

.. seealso::
    
    * `Digikam Database Settings <https://docs.kde.org/trunk5/en/digikam-doc/digikam/using-setup.html#using-setup-database>`_
    * :class:`Digikam Class Reference <digikamdb.conn.Digikam>`

Working with Images
--------------------

.. todo:: Images Tutorial

Working with Albums
---------------------

.. todo:: Albums Tutorial

Defining and Assigning Tags
-----------------------------

.. todo:: Tags Tutorial


