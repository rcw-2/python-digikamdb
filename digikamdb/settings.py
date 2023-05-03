"""
Provides access to Digikam settings.
"""

from typing import Generator, Iterable, Tuple               # noqa: F401

from sqlalchemy import Column, String

from .table import DigikamTable


def _settings_class(dk: 'Digikam') -> type:                    # noqa: F821
    """Defines the Settings class."""
    
    class Setting(dk.base):
        """
        Digikam Settings
        
        This table should be accessed via
        Class :class:`~digikamdb.settings.Settings`.
        """

        __tablename__ = 'Settings'
        
        keyword = Column(String, primary_key = True)
    
    return Setting


class Settings(DigikamTable):
    """
    Digikam settings class
    
    The Digikam settings can be accessed like a dict:
    
    .. code-block:: python
        
        dk = digikamdb.Digikam()
        if 'DBVersion' in dk.settings:
            db_version = dk.settings['DBVersion']           # Get DB version
        dk.settings['databaseUserImageFormats'] = '-xcf'    # Exclude GIMP files
        for k in dk.settings:                               # Iterate over settings
            print(k, '=', dk.settings[k])
        for k, v in dk.settings.items():                    # Iterate over settings
            print(k, '=', v)
    
    Args:
        digikam:     Digikam object
    """
    
    _class_function = _settings_class
    _id_column = '_keyword'
    
    def __init__(self, digikam: 'Digikam'):                       # noqa: F821
        super().__init__(digikam)
    
    def __iter__(self) -> Iterable:
        for s in super().__iter__():
            yield s._keyword
    
    def __getitem__(self, key: str) -> str:
        return super().__getitem__(key)._value
    
    def __setitem__(self, key: str, value: str):
        row = self._select(keyword = key).one_or_none()
        if row:
            row._value = value
        else:
            self._insert(_keyword = key, _value = value)
    
    def items(self) -> Iterable[Tuple[str, str]]:
        """
        Returns an iterable with (key, value) pairs.
        
        Yields:
            The settings (key, value) pairs.
        """
        for row in self._select():
            yield row._keyword, row._value



