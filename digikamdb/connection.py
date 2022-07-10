"""
Defines the Digikam class for database access.
"""

import configparser
import os
from typing import Mapping, Optional, Union

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeferredReflection, declarative_base

from .settings import Settings
from .tags import Tags
from .albumroots import AlbumRoots
from .albums import Albums
from .images import Images


class Digikam:
    """
    Connection to the Digikam database.
    
    This object connects to the Digikam database using the
    :doc:`SQLAlchemy ORM <sqla:orm/quickstart>`. It generates its own set of
    classes so that you can use multiple ``Digikam`` objects to connect to
    different databases.
    
    When initializing a ``Digikam`` object, you have to supply parameters to
    specify the database. This is usually done with the ``database``
    parameter. ``Digikam`` can also use the local Digikam application's
    database configuration in :file:`$HOME/.config/digikamrc`. To use this
    feature, specify ``use_digikam_config = True``.
    
    Access to actual data is mostly done through the properties
    
    * images (:class:`~digikamdb.images.Images`)
    * tags (:class:`~digikamdb.tags.Tags`)
    * albums (:class:`~digikamdb.albums.Albums`)
    * albumroots (:class:`~digikamdb.albumroots.AlbumRoots`)
    * settings (:class:`~digikamdb.settings.Settings`)
    
    Parameters:
        database:   Digikam database. Can be a ``str`` or a SQLAlchemy
                    :class:`~sqlalchemy.engine.Engine` object.
                    With the value ``digikamrc`` the database specification
                    is read from :file:`$HOME/.config/digikamrc`.
        sql_echo:   Sets the ``echo`` option of SQLAlchemy.
        root_override:  Can be used to override the location of album roots
                        in the file system.
    """
    
    def __init__(
        self,
        database: Union[str, Engine],
        root_override: Optional[Mapping] = None,
        sql_echo: bool = False
    ):
        """
        Constructor
        """
        
        if isinstance(database, Engine):
            self._engine = database
        elif isinstance(database, str):
            if database == 'digikamrc':
                self._engine = Digikam.db_from_config(sql_echo = sql_echo)
            else:
                self._engine = create_engine(
                    database,
                    future = True,
                    echo = sql_echo)
        else:
            raise TypeError('Database not specified')
        
        self._session = Session(self.engine)

        self.base = _digikamobject_class(declarative_base())
        
        self._settings = Settings(self)
        self._tags = Tags(self)
        self._albumRoots = AlbumRoots(self, override = root_override)
        self._albums = Albums(self)
        self._images = Images(self)

        self.base.prepare(self.engine)
        self.tags.setup()
    
    @classmethod
    def db_from_config(cls, sql_echo = False) -> Engine:
        """
        Creates the database connection from :file:`digikamrc`.
        
        Returns:
            Database connection object
        """
        configfile = os.path.join(os.path.expanduser('~'), '.config/digikamrc')
        config = configparser.ConfigParser()
        config.read(configfile)
        
        if config['Database Settings']['Database Type'] != 'QMYSQL':
            raise ValueError('Only MySQL is supported')
        
        return create_engine(
            "mysql+pymysql://%s:%s@%s/%s?charset=utf8?port=%d" % (
                config['Database Settings']['Database Username'],
                config['Database Settings']['Database Password'],
                config['Database Settings']['Database Hostname'],
                config['Database Settings']['Database Name'],
                int(config['Database Settings']['Database Port'])),
            future = True,
            echo = sql_echo)
    
    def destroy(self):
        """Clears the object."""
        self._settings = None
        self._tags = None
        self._albumRoots = None
        self._albums = None
        self._images = None
        self.session.close()
        self._session = None
        self.engine.dispose()
        self._engine = None
    
    @property
    def settings(self) -> Settings:
        """Returns the :class:`Settings` object."""
        return self._settings
    
    @property
    def tags(self) -> Tags:
        """Returns the :class:`Tags` object."""
        return self._tags
    
    @property
    def albumRoots(self) -> AlbumRoots:
        """Returns the :class:`AlbumRoots` object."""
        return self._albumRoots
    
    @property
    def albums(self) -> Albums:
        """Returns the :class:`Albums` object."""
        return self._albums
    
    @property
    def images(self) -> Images:
        """Returns the :class:`Images` object."""
        return self._images
    
    @property
    def engine(self) -> Engine:
        """Returns the SQLAlchemy engine"""
        return self._engine
    
    @property
    def session(self) -> Session:
        """Returns the SQLAlchemy ORM session"""
        return self._session
    
    @property
    def is_mysql(self) -> bool:
        """Returns ``True`` if database is MySQL."""
        return (self.engine.dialect.name == 'mysql')
    
    @property
    def albumroot_class(self):
        return self.albumRoots.Class
    
    @property
    def album_class(self):
        return self.albums.Class
    
    @property
    def image_class(self):
        return self.images.Class
    
    @property
    def tag_class(self):
        return self.tags.Class


def _digikamobject_class(base: type) -> type:
    """
    Defines the DigikamObject class
    
    Args:
        base:   parent class (generated with :func:`declarative_base`)
    Returns:
        Class that has the parents :class:`DeferredReflection` and *base*.
    """
    class DigikamObject(DeferredReflection, base):
        """
        Abstract base class for objects stored in database.
        
        Derived from ``DeferredReflection`` and :func:`declarative_base`.
        """
        
        __abstract__ = True
    
    return DigikamObject



