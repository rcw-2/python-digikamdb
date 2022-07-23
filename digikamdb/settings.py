"""
Provides access to Digikam settings.
"""

from typing import Generator, Iterable, Tuple               # noqa: F401

from sqlalchemy import MetaData, Table, select


class Settings:
    """
    Digikam settings class
    
    The Digikam settings can be accessed like a dict:
    
    .. code-block:: python
        
        dk = digikamdb.Digikam()
        db_version = dk.settings['DBVersion']               # Get DB version
        dk.settings['databaseUserImageFormats'] = '-xcf'    # Exclude GIMP files
    
    You can alter existing settings this way, but not add new ones.
    
    Args:
        parent:     Digikam object
    """
    
    def __init__(self, parent: 'Digikam'):                  # noqa: F821
        self.parent = parent
        self.table = Table('Settings', MetaData(), autoload_with = self.parent.engine)
    
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
    
    def items(self) -> Iterable[Tuple[str, str]]:
        """
        Returns an iterable with (key, value) pairs.
        
        Yields:
            The settings (key, value) pairs.
        """
        with self.parent.session.connection() as conn:
            for row in conn.execute(select(self.table)):
                yield row.keyword, row.value



