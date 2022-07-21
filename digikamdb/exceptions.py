"""
Digikam Exceptions
"""


class DigikamError(Exception):
    """
    General Digikam Exception
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


