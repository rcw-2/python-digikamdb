|PyPi Package| |Documentation Status| |Test Status|

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

.. code-block:: bash
    
    pip install Digikam-DB

If you are using a MySQL database, you may want to install the additional
dependencies:

.. code-block:: bash
    
    pip install Digikam-DB[mysql]

To get the source code, go to https://github.com/rcw-2/python-digikamdb.


Running the Tests
------------------

The MySQL tests need a MySQL database to run. The database must be specified
in a module ``mysql_data`` somewhere in the Python path (e.g. in the same
directory as this file, it will be ignored by Git) that defines the variables
``db_host``, ``db_user``, ``db_pass`` and ``db_name``. The given user must
have all privileges on the given database.

To fill the database, the ``mysql`` binary is called, so make sure to
have ``mysql-client`` installed.


.. |PyPi Package| image:: https://badge.fury.io/py/Digikam-DB.svg
    :target: https://badge.fury.io/py/Digikam-DB

.. |Documentation Status| image:: https://readthedocs.org/projects/digikam-db/badge/?version=latest
    :target: http://digikam-db.readthedocs.io/?badge=latest

.. |Test Status| image:: https://github.com/rcw-2/python-digikamdb/actions/workflows/test.yml/badge.svg
    :target: https://github.com/rcw-2/python-digikamdb/actions/workflows/test.yml


