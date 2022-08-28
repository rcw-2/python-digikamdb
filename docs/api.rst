API: Connection and Base Classes
=================================

.. module:: digikamdb.conn

The Digikam Class
------------------

.. autoclass:: Digikam
    :no-show-inheritance:
    :members:

Base Class for Mapped Tables
-----------------------------

.. autoclass:: _sqla.DigikamObject
    :no-show-inheritance:
    :members:

.. module:: digikamdb.table

Digikam Table
--------------

.. autoclass:: DigikamTable
    :no-show-inheritance:
    :members:

.. module:: digikamdb.properties

Basic Properties
-----------------

.. autoclass:: BasicProperties
    :no-show-inheritance:
    :members:

.. module:: digikamdb.settings

Digikam Settings
-----------------

.. autoclass:: Settings
    :no-show-inheritance:
    :members:

.. ifconfig::   include_private_content
    
    .. autoclass:: _sqla.Setting

.. module:: digikamdb.exceptions

Exceptions
-------------

Digikam-DB defines several Exceptions for Digikam-specific errors.

.. autoexception:: DigikamError

.. autoexception:: DigikamConfigError

.. autoexception:: DigikamFileError

.. autoexception:: DigikamAssignmentError

.. autoexception:: DigikamQueryError

.. autoexception:: DigikamObjectNotFound

.. autoexception:: DigikamMultipleObjectsFound

.. autoexception:: DigikamDataIntegrityError

