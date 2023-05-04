"""
Defines the ``Digikam`` class for database access.
"""

import logging
import os
import re
from typing import Mapping, Optional, Union

from sqlalchemy import text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.ext.declarative import DeferredReflection

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
        if isinstance(database, Engine):
            log.info(
                'Initializing Digikam object from %s',
                database
            )
            self._engine = database
        elif isinstance(database, str):
            if database == 'digikamrc':
                log.info('Initializing Digikam object from digikamrc')
                self._engine = Digikam.db_from_config(sql_echo = sql_echo)
            else:
                log.info(
                    'Initializing Digikam object from %s',
                    re.sub(r':.*@', ':XXX@', database)
                )
                self._engine = create_engine(
                    database,
                    future = True,
                    echo = sql_echo)
        else:
            raise TypeError('Database specification must be Engine or str')
        
        self._db_version = self._get_db_version()
        
        self._session = Session(self._engine, future = True)

        self._base = self._digikamobject_class(declarative_base())
        
        self._settings  = Settings(self)
        self._tags      = Tags(self)
        self._albumRoots = AlbumRoots(self, override = root_override)
        self._albums    = Albums(self)
        self._images    = Images(self)

        self.base.prepare(self._engine)
        self.tags.setup()
    
    _db_config_keys = dict(
        db_host = 'Database Hostname',
        db_name = 'Database Name',
        db_pass = 'Database Password',
        db_port = 'Database Port',
        db_type = 'Database Type',
        db_user = 'Database Username',
        db_internal = 'Internal Database Server'
    )
    
    def _get_db_version(self) -> int:
        with self._engine.connect() as conn:
            return int(
                conn.execute(text(
                    "SELECT value FROM Settings WHERE keyword = 'DBVersion'"
                )).one().value
            )
    
    @property
    def db_version(self) -> int:
        """
        The Digikam database version
        
        .. versionadded:: 0.2.2
        """
        return self._db_version
    
    @property
    def has_tags_nested_sets(self) -> bool:
        """
        Indicates if the ``Tags`` table has nested sets
        
        .. versionadded:: 0.2.2
        """
        return self.is_mysql and self.db_version <= 10
    
    @property
    def base(self) -> type:
        """Base class for table-mapped classes"""
        return self._base
    
    @classmethod
    def db_from_config(cls, sql_echo = False) -> Engine:    # noqa: C901
        """
        Creates the database connection from :file:`digikamrc`.
        
        Returns:
            Database connection object
        Raises:
            DigikamConfigError:     ~/.config/digikamrc cannot be read
                                    or interpreted.
        """
        try:
            configfile = os.path.join(os.path.expanduser('~'), '.config/digikamrc')
            config = None
            # configparser cannot process digikamrc, so we do it manually...
            with open(configfile, 'r') as cfg:
                for line in cfg.readlines():
                    line = line.strip()
                    
                    if config is None:
                        if line == '[Database Settings]':
                            config = {}
                        continue
                    
                    if line.startswith('['):
                        break
                    
                    if '=' not in line:
                        continue
                    
                    key, value = line.split('=', maxsplit=1)
                    key, value = key.strip(), value.strip()
                    
                    for key1, key2 in cls._db_config_keys.items():
                        if key == key2:
                            config[key1] = value
                            break
        
        except DigikamError:                                # pragma: no cover
            raise
        except Exception as e:
            raise DigikamConfigError('Error reading config file: ' + str(e))
        
        try:
            if config['db_type'] == 'QMYSQL':
                if 'db_internal' in config and config['db_internal'].lower() != 'false':
                    raise DigikamConfigError('Internal Database Server is not supported')
                
                if 'db_port' in config:
                    config['db_host'] = '%s:%s' % (
                        config['db_host'],
                        config['db_port']
                    )
                db_str = 'mysql+pymysql://%s:%s@%s/%s?charset=utf8' % (
                    config['db_user'],
                    config['db_pass'],
                    config['db_host'],
                    config['db_name'],
                )
                log.debug(
                    'Using MySQL database %s',
                    db_str.replace(config['db_pass'], 'XXX')
                )
                return create_engine(db_str, future = True, echo = sql_echo)
                
            elif config['db_type'] == 'QSQLITE':
                log.debug('Using SQLite database in %s', config['db_name'])
                return create_engine(
                    'sqlite:///%s' % (
                        os.path.join(config['db_name'], 'digikam4.db')
                    ),
                    future = True,
                    echo = sql_echo)
            
            else:
                raise DigikamConfigError('Unknown database type ' + config['db_type'])
        
        except DigikamError:
            raise
        except KeyError as e:                               # pragma: no cover
            if e.args[0] in cls._db_config_keys:
                raise DigikamConfigError(
                    'Configuration not found: ' + cls._db_config_keys[e.args[0]]
                )
            else:
                raise
        
        raise DigikamConfigError('Unknown Database Type ' + config['db_type'])
    
    def destroy(self):
        """
        Clears the object.
        
        This will call :meth:`~sqlalchemy.orm.Session.close` and
        :meth:`~sqlalchemy.engine.Engine.dispose` for the session and engine
        objects.
        """
        log.info('Scrapping Digikam object')
        self._settings = None
        self._tags = None
        self._albumRoots = None
        self._albums = None
        self._images = None
        self.session.close()
        self._session = None
        self._engine.dispose()
        self._engine = None
    
    @property
    def settings(self) -> Settings:
        """The :class:`~digikamdb.settings.Settings` object"""
        return self._settings
    
    @property
    def tags(self) -> Tags:
        """The :class:`~digikamdb.tags.Tags` object"""
        return self._tags
    
    @property
    def albumRoots(self) -> AlbumRoots:
        """The :class:`~digikamdb.albumroots.AlbumRoots` object"""
        return self._albumRoots
    
    @property
    def albums(self) -> Albums:
        """The :class:`~digikamdb.albums.Albums` object"""
        return self._albums
    
    @property
    def images(self) -> Images:
        """The :class:`~digikamdb.images.Images` object"""
        return self._images
    
    @property
    def session(self) -> Session:
        """The SQLAlchemy ORM session"""
        return self._session
    
    @property
    def is_mysql(self) -> bool:
        """
        ``True`` if database is MySQL
        """
        return (self._engine.dialect.name == 'mysql')
    
    def _digikamobject_class(self, base: type) -> type:
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
            __mapper_args__ = {
                'column_prefix':    '_',
            }
            
            _digikam = self
            
            @property
            def digikam(self) -> Digikam:
                """The ``Digikam`` object"""
                return self._digikam
        
        return DigikamObject



