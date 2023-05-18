"""
Digikam Exceptions
"""


class DigikamError(Exception):
    """
    General Digikam Exception.
    
    All other Digikam-DB exceptions are derived from this class.
    """


class DigikamConfigError(DigikamError):
    """
    Error in Digikam Digikam configuration.
    """


class DigikamFileError(DigikamError):
    """
    Error accessing an image file or album directory.
    """


class DigikamAssignmentError(DigikamError):
    """
    A value cannot be assigned to a Digikam object.
    """


class DigikamQueryError(DigikamError):
    """
    Error executing database query, or invalid result.
    """


class DigikamObjectNotFound(DigikamQueryError):
    """
    No matching object was not found.
    
    .. deprecated: 0.3.1
        use :exc:`DigikamObjectNotFoundError` instead
    """


class DigikamMultipleObjectsFound(DigikamQueryError):
    """
    Multiple objects were found when at most one was expected.
    
    .. deprecated: 0.3.1
        use :exc:`DigikamMultipleObjectsFoundError` instead
    """


class DigikamObjectNotFoundError(DigikamObjectNotFound):
    """
    No matching object was not found.
    
    .. versionadded:: 0.3.1
    """


class DigikamMultipleObjectsFoundError(DigikamMultipleObjectsFound):
    """
    Multiple objects were found when at most one was expected.
    
    .. versionadded:: 0.3.1
    """


class DigikamDataIntegrityError(DigikamError):
    """
    The database is in an inconsistent state.
    """


class DigikamVersionError(DigikamError):
    """
    The requested property is not present in the used database version.
    """

