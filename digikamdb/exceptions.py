"""
Digikam Exceptions
"""


class DigikamError(Exception):
    """
    General Digikam Exception.
    
    All other Digikam-DB exceptions are derived from this class.
    """
    pass


class DigikamConfigError(DigikamError):
    """
    Error in Digikam Digikam configuration
    """
    pass


class DigikamFileError(DigikamError):
    """
    Error accessing an image file or album directory
    """
    pass


class DigikamDataIntegrityError(DigikamError):
    """
    The database is in an inconsistent state.
    """
