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
    Error in Digikam Digikam configuration.
    """
    pass


class DigikamFileError(DigikamError):
    """
    Error accessing an image file or album directory.
    """
    pass


class DigikamAssignmentError(DigikamError):
    """
    A value cannot be assigned to a Digikam object.
    """
    pass


class DigikamQueryError(DigikamError):
    """
    Error executing database query, or invalid result.
    """
    pass


class DigikamObjectNotFound(DigikamQueryError):
    """
    No matching object was not found.
    """
    pass


class DigikamMultipleObjectsFound(DigikamQueryError):
    """
    Multiple objects were found when at most one was expected.
    """


class DigikamDataIntegrityError(DigikamError):
    """
    The database is in an inconsistent state.
    """
    pass

class DigikamVersionError(DigikamError):
    """
    The requested property is not present in the used database version.
    """

