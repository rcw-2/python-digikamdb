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

.. code-block:: sh
    
    pip install Digikam-DB

If you are using a MySQL database, you may want to install the additional
dependencies:

.. code-block:: sh
    
    pip install Digikam-DB[mysql]

To get the source code, go to :source:`#`.

Basic Usage
-------------

.. code-block:: python
    
    from digikamdb import Digikam
    
    dk = Digikam('mysql://myuser:mypass@my.host.org/mydb')
    
    tag = dk.tags['my tag']
    if not tag:
        tag = dk.tags.add('my tag', dk.tags.root)
    
    img = dk.images.find('/path/to/my/image.jpg')
    img.caption = 'My Caption'
    img.title = 'My Title'
    img.information.rating = 3
    img.tags.append(tag)
    
    img2 = dk.images[42]    # Access image by id
    print(img2.name, img2.abspath())
    
    



Limitations
------------

* Adding or deleting albumroots, albums and images is not supported.
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
  * Settings
  * Tags
  * TagProperties
  * VideoMetadata

* Only `x-default` in language fields is supported.

