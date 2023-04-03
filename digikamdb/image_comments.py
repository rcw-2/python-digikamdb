"""
Image Comments
"""

import logging
import os
from datetime import datetime
from itertools import groupby
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from sqlalchemy import Column, Integer, String, delete, text
from sqlalchemy.orm import relationship, validates

from .table import DigikamTable
from .properties import BasicProperties


log = logging.getLogger(__name__)

def _imageproperty_class(dk: 'Digikam'):                    # noqa: F821
    return dk.images.ImageComment


class ImageComments(BasicProperties):
    """
    Encapsulates ImageComments (caption and title).
    
    Args:
        parent:     Corresponding Image object
        type\\_:    Comment type (1 for caption, 3 for title)
    """
    #: Funktion returning the table class
    _class_function = _imageproperty_class
    
    #: Parent id column
    _parent_id_col = '_imageid'
    
    #: Key column
    _key_col = ['_language', '_author']
    
    #: Value column
    _value_col = ['_comment', '_date']
    
    #: Return ``None`` when select does not find a row
    _raise_on_not_found = False
    
    #: Remove item when set to ``None``
    _remove_on_set_none = True
    
    def __init__(self, parent: 'Image', type_: int):       # noqa: F821
        super().__init__(parent)
        self._type = type_
    
    def __repr__(self) -> str:                              # pragma: no cover
        return '<ImageComments object type=%d>' % self._type
    
    def _select_self(self) -> '~sqlalchemy.orm.Query':      # noqa: F821
        """
        Selects all comments with the riqht type of the parent object.
        """
        return super()._select_self().filter_by(_type = self._type)
    
    def _prop_attributes(self, prop: Union[str, int, Iterable, None], **values):
        """Adds type to the standard properties."""
        values['_type'] = self._type
        return super()._prop_attributes(prop, **values)
    
    def _pre_process_key(self, prop: Union[str, Iterable, None]) -> Tuple:
        """Preprocesses key for [] operations."""
        ret = list(super()._pre_process_key(prop))
        if ret[0] is None or ret[0] == '':
            ret[0] = 'x-default'
        return tuple(ret)


class ImageTitles(ImageComments):
    """
    Enables access to multilingual image titles.
    
    Objects of this type are normally accessed through an :class:`Image`
    object, see :attr:`~Image.titles`. In general, it is not necessary to
    call the constructor directly.
    
    Titles can be multilingual. Individual languages can be retrieved from the
    Titles object like from a dict where the key is a string containing the
    language. The language can be given as ``None`` or as an empty string,
    both are replaced internally by **x-default**.
    
    .. code-block:: python
        
        c1 = img.titles['']             # Default language
        c2 = img.titles['es-ES']        # Spanish
        c3 = img.titles[None]           # Default language
        
        img.titles[''] = 'Some text'    # sets the default title

    Args:
        parent:     Image object the title belongs to.
    """
    
    #: Value column
    _value_col = '_comment'

    def __init__(self, parent: 'Image'):                    # noqa: F821
        # set type=3
        super().__init__(parent, 3)
    
    def __repr__(self) -> str:                              # pragma: no cover
        return '<Titles for image %d>' % self._parent.id
    
    def _post_process_key(self, key: Union[str, Tuple]) -> str:
        """Just remove author"""
        key = super()._post_process_key(key)
        if isinstance(key, tuple):
            return key[0]
        return key                                          # pragma: no cover
    
    def _post_process_value(self, value: 'DigikamObject') -> Tuple:  # noqa: F821
        """Preprocesses values for [] operations."""
        value = super()._post_process_value(value)
        if isinstance(value, tuple):
            return value[0]                                 # pragma: no cover
        return value


class ImageCaptions(ImageComments):
    """
    Contains an image's captions.
    
    An Image can have multiple captions: by different authors and in different
    languages. Individual captions can be retrieved from the Captions object
    like from a dict where the keys are either a string (containing the
    language, the author defaults to ``None`` in this case) or a tuple
    containing language and author. The language can be given as ``None`` or as
    an empty string, both are replaced internally by **x-default**.
    
    .. code-block:: python
        
        c1 = img.captions[('', 'Fred')]         # Default language, author Fred
        c2 = img.captions['es-ES']              # Spanish, no author
        c3 = img.captions[None]                 # Default language, no author
        c4 = img.captions[('de-DE', 'Ralph')]   # German, author Ralph
        
        img.captions[''] = 'Some text'          # sets the default caption
    
    The caption's value is a tuple containing the caption text and the
    caption's date. When setting the value, just the text can be given, and
    the date will be set to ``None``
    
    Args:
        parent:     Image object the title belongs to.
    """
    def __init__(self, parent: 'Image'):                    # noqa: F821
        # set type=1
        super().__init__(parent, 1)

    def __repr__(self) -> str:                              # pragma: no cover
        return '<Captions for image %d>' % self._parent.id

