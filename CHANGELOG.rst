v0.3.4 (2024-07-07)
--------------------
*   Better parsing of AlbumRoot.identifier

v0.3.3 (2023-11-11)
--------------------
*   AlbumRoot.mountpoint emits a warning when trying to determine mount point
    on other systems than Linux.

v0.3.2 (2023-10-01)
--------------------
*   New ``ExifExposureProgram`` value ``BULB``
    (unofficial, but used by Canon).
*   ``DigikamImageInformation.colorModel`` returns numeric value if
    it is not a valid ``ImageColorModel``.

v0.3.1 (2023-06-11)
--------------------
*   ``Tags.add()`` accepts hierarchical tag names.
*   Replaced ``DigikamObjectNotFound`` and ``DigikamMultipleObjectsFound`` with
    ``DigikamObjectNotFoundError`` and ``DigikamMultipleObjectsFoundError``. The
    old exceptions are still present for compatibility, but will be removed in
    the future.
*   Changed capitalize() in enum string representations to title().

v0.3.0 (2023-05-09)
--------------------
*   Reader-friendly string conversions for Exif classes.
*   Made ``ExifFlash`` more standards-conforming (may break existing code if
    ``function`` attribute is used).

v0.2.2 (2023-05-05)
--------------------
*   Added support for MySQL without nested sets in `Tags` (DBVersion > 10).
*   Raise ``DigikamVersionError`` when trying to access properties not supported
    by the used database version.
*   Added ``Album.modificationDate`` and ``AlbumRoot.caseSensitivity``.

v0.2.1 (2023-04-07)
--------------------
* Digikam.__init__: don't log sensitive data.
* BasicProperties: added get method.
* Imageinformation.orientation can be None.

v0.2.0 (2023-04-03)
--------------------
* Changes may break existing code.
* Image.caption returns string instead of tuple.
* ExifMeteringMode: Fixed typo in CENTER_WEIGHTED_AVERAGE.

v0.1.3 (2023-04-01)
--------------------
* Fixed exceptions when some ImageMetadata columns contain NULL.
* Fixed column names in nested tags check.

v0.1.2 (2023-03-27)
--------------------
* Fixed SQLAlchemy 2.0 compatibility issues.

v0.1.1 (2023-03-27)
--------------------
* Changed SQLAlchemy dependency to ~=1.4 as tests fail with 2.0.
* Added Sphinx as doc dependency.

v0.1.0 (2022-08-29)
--------------------
* First public release

