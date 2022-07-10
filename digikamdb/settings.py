"""
Digikam Settings
"""

from typing import Any, Iterable, Optional

from sqlalchemy import MetaData, Table, select

class Settings:
    """
    Digikam settings class
    
    The database settings can be accessed like a dict:
    
    .. code-block:: python
        
        dk = digikamdb.Digikam()
        db_version = dk.settings['DBVersion']               # Get DB version
        dk.settings['databaseUserImageFormats'] = '-xcf'    # Exclude GIMP files
    
    You can alter existing settings this way, but not add new ones.
    
    Args:
        parent:     Digikam object
    """
    
    def __init__(self, parent: 'Digikam'):
        self.parent = parent
        self.table = Table('Settings', MetaData(), autoload_with = self.parent.engine)
        #self.session = parentsession
        #Setting.session = session
    
    def __getitem__(self, key: str) -> str:
        with self.parent.session.connection() as conn:
            row = conn.execute(
                select(self.table).where(self.table.c.keyword == key)
            ).one()
        return row.value
    
    def __setitem__(self, key: str, value: str):
        with self.parent.session.connection() as conn:
            row = conn.execute(
                select(self.table).where(self.table.c.keyword == key)
            ).one()
            row.value = value
    
    def items(self) -> Iterable:
        """Returns an iterable with (key, value) pairs."""
        with self.parent.session.connection() as conn:
            for row in conn.execute(select(self.table)):
                yield row.keyword, row.value


