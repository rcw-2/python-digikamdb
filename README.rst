Digikam-DB
===========

Python library to access Digikam metadata (database)

Digikam is an image management application using KDE.
For more information on Digikam, see https://www.digikam.org/.

Digikam-DB can read and write Digikam metadata. It works with both
SQLite and MySQL databases.

.. warning::
    
    This package is still under development. Use at your own risk and make
    a backup of your Digikam database before writing to it.

Installation
-------------

For installation via PIP, simply type:

.. code-block:: sh
    
    pip install Digikam-DB

If you are using a MySQL database, you may want to install the additional
dependencies:

.. code-block:: sh
    
    pip install Digikam-DB[mysql]

To get the source code, go to https://github.com/rcw-2/Digikam-DB.
