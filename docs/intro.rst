Introduction
=============

What is Digikam-DB?
--------------------

Digikam-DB is a SQLAlchemy-based Python library that enables access to the
Digikam database containing Digikam's metadata (title, tags, rating, Exif
information...). You can use it to read or manipulate this data by directly
accessing the Digikam database.

Digikam is an image management application using KDE.
For more information on Digikam, see https://www.digikam.org/.

Digikam-DB aims at offering a convenient encapsulating the more complicated
aspects of the Digikam database. 

.. warning::
    
    This package is still under development. Use at your own risk and make
    a backup of your Digikam database before writing to it.

Installation
-------------

For installation via PIP, simply type:

.. code-block:: console
    
    pip install Digikam-DB

If you are using a MySQL database, you may want to install the additional
dependencies:

.. code-block:: console
    
    pip install Digikam-DB[mysql]

The source code is available on :source:`Github<#>`.

Basic Usage
-------------

In this small example, we

* connect to the database via a :class:`~digikamdb.conn.Digikam` object,
* create a tag **my tag** if it does not exist yet,
* add this tag to image :file:`/path/to/my/image.jpg`,
* change some properties of :file:`/path/to/my/image.jpg`,
* commit these changes to the database and
* print file name and complete path of the image with id **42**.

.. code-block:: python
    
    from digikamdb import Digikam
    
    dk = Digikam('mysql://myuser:mypass@my.host.org/mydb')
    
    tag = dk.tags['my tag']
    if not tag:
        tag = dk.tags.add('my tag', dk.tags.root)
    
    img = dk.images.find('/path/to/my/image.jpg')[0]
    img.tags.append(tag)
    img.caption = 'My Caption'
    img.title = 'My Title'
    img.information.rating = 3
    dk.session.commit()     # Commit changes to database
    
    img2 = dk.images[42]    # Access image by id
    print(img2.name, img2.abspath)

For more information on usage, see :doc:`/tutorial`.

Limitations
------------

* Adding or deleting albumroots, albums and images is not supported.
* Digikam-DB will probably not run under Windows or MacOS.
* Fractions of seconds on datetime fields are ignored (this is standard on
  MySQL, but not on SQLite).
* The only tables implemented are:
  
  * AlbumRoots
  * Albums
  * ImageComments
  * ImageCopyright
  * ImageInformation
  * ImageHistory
  * ImageMetadata
  * ImagePositions
  * Images
  * ImageTags
  * Settings
  * TagProperties
  * Tags
  * VideoMetadata

