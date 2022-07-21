"""
Defines the ``Digikam`` class for database access.
"""

import configparser
import logging
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
from .exceptions import DigikamError, DigikamConfigError


log = logging.getLogger(__name__)


class Digikam:
    """
    Connection to the Digikam database.
    
    This object connects to the Digikam database using the
    :doc:`SQLAlchemy ORM <sqla:orm/quickstart>`. It generates its own set of
    classes so that you can use multiple ``Digikam`` objects to connect to
    different databases.
    
    When initializing a ``Digikam`` object, you have to supply parameters to
    specify the database. This is usually done with the ``database``
    parameter. It can be one of the following:
    
    The string **"digikamrc"**:
        Use the local Digikam application's database configuration in
        :file:`$HOME/.config/digikamrc`.
    Any other :class:`str`:
        Use the string as database URL in :func:`~sqlalchemy.create_engine`.
    A SQLAlchemy :class:`~sqlalchemy.engine.Engine` object:
        Use this object as the database engine
    
    Access to actual data is mostly done through the following properties:
    
    * images (class :class:`~digikamdb.images.Images`)
    * tags (class :class:`~digikamdb.tags.Tags`)
    * albums (class :class:`~digikamdb.albums.Albums`)
    * albumroots (class :class:`~digikamdb.albumroots.AlbumRoots`)
    * settings (class :class:`~digikamdb.settings.Settings`)
    
    Parameters:
        database:   Digikam database.
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
        log.info(
            'Initializing Digikam object from %s',
            database
        )
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
            raise TypeError('Database specification must be Engine or str')
        
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
        Raises:
            DigikamConfigError:     ~/.config/digikamrc cannot be read
                                    or interpreted.
        """
        configfile = os.path.join(os.path.expanduser('~'), '.config/digikamrc')
        config = configparser.ConfigParser()
        config.read(configfile)
        try:
            dbtype = config['Database Settings']['Database Type']
        except KeyError as e:
            raise DigikamConfigError('Database Type not specified: ' + e)
        
        if dbtype == 'QMYSQL':
            try:
                if config['Database Settings']['Internal Database Server']:
                    raise DigikamConfigError('Internal MySQL server is not supported')
                
                return create_engine(
                    'mysql+pymysql://%s:%s@%s/%s?charset=utf8?port=%d' % (
                        config['Database Settings']['Database Username'],
                        config['Database Settings']['Database Password'],
                        config['Database Settings']['Database Hostname'],
                        config['Database Settings']['Database Name'],
                        int(config['Database Settings']['Database Port'])
                    ),
                    future = True,
                    echo = sql_echo)
            except DigikamError:
                raise
            except KeyError as e:
                raise DigikamConfigError('Configuration not found: ' + e)
        
        if dbtype == 'QSQLITE':
            try:
                return create_engine(
                    'sqlite:///%s' % (
                        config['Database Settings']['Database Name']
                    ),
                    future = True,
                    echo = sql_echo)
            except KeyError as e:
                raise DigikamConfigError('Configuration not found: ' + e)
        
        raise DigikamConfigError('Unknown database type ' + dbtype)
    
    def destroy(self):
        """Clears the object."""
        log.info('Tearing down Digikam object')
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
    def albumroot_class(self) -> type:
        """Returns the :class:`~_sqla.AlbumRoot` class"""
        return self.albumRoots.Class
    
    @property
    def album_class(self) -> type:
        """Returns the :class:`~_sqla.Album` class"""
        return self.albums.Class
    
    @property
    def image_class(self) -> type:
        """Returns the :class:`~_sqla.Image` class"""
        return self.images.Class
    
    @property
    def tag_class(self) -> type:
        """Returns the :class:`~_sqla.Tag` class"""
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
        Derived from :class:`~sqlalchemy.ext.declarative.DeferredReflection`
        and :func:`~sqlalchemy.orm.declarative_base`.
        """
        
        __abstract__ = True
    
    return DigikamObject



