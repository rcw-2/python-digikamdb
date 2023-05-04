v0.2.2 (2023-??-??)
--------------------
*   Added support for MySQL without nested sets in `Tags` (DBVersion > 10)
*   Raise ``DigikamVersionError`` when trying to access properties not supported
    by the used database version.
*   Added ``Album.modificationDate`` and ``AlbumRoot.caseSensitivity``

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

