"""
Enables access to Digikam tags.
"""

import logging
from typing import Iterable, List, Optional, Union

from sqlalchemy import (
    Column, Integer, ForeignKey, String, Table,
    case, event, inspect, select, text,
)
from sqlalchemy.orm import object_session, relationship, validates
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from .table import DigikamTable
from .properties import BasicProperties
from .exceptions import (
    DigikamError,
    DigikamAssignmentError,
    DigikamObjectNotFound,
    DigikamMultipleObjectsFound,
    DigikamDataIntegrityError
)


log = logging.getLogger(__name__)


def _tag_class(dk: 'Digikam') -> type:                      # noqa: F821, C901
    """
    Defines the Tag class
    """
    
    class Tag(dk.base):
        """
        Digikam tag.
        
        Tags in Digikam are hierarchical. ``Tag`` reflects this by providing:
        
        * The :attr:`parent` and :attr:`children` properties,
        * ``tag1 in tag2`` can be used to test if ``tag2`` is an ancestor of
          ``tag1``.
        * The :meth:`hierarchicalname` method.
        
        .. note::
            The tree structure differs between SQLite and MySQL:
            
            *   On SQLite, tags at the top level have a ``pid == 0``,
                and there is no row with ``id == 0``. There can be many
                tags without a parent tag.
            *   On MySQL, there is a tag ``_Digikam_Root_Tag_`` with
                ``id == 0`` and ``pid == -1``, and there is no tag with
                ``id == -1``. All other tags are descendents of
                ``_Digikam_Root_Tag_``.
            *   On MySQL with DBVersion <= 10, the ``Tags`` table implements an
                additional *nested sets* structure with columns ``lft`` and ``rgt``.

        .. seealso::
            * Class :class:`~digikamdb.tags.Tags`
        """
        
        __tablename__ = 'Tags'
        __mapper_args__ = dk.base.__mapper_args__.copy()
        __mapper_args__.update({
            "batch": False  # allows extension to fire for each
                            # instance before going to the next.
        })
        _properties = relationship(
            'TagProperty',
            primaryjoin = 'foreign(TagProperty._tagid) == Tag._id',
            lazy = 'dynamic'
        )
        _iconObj = relationship(
            'Image',
            primaryjoin = 'foreign(Image._id) == Tag._icon',
            viewonly = True,
            uselist = False
        )
        _images = relationship(
            'Image',
            primaryjoin = 'foreign(ImageTags.c.tagid) == Tag._id',
            secondaryjoin = 'foreign(ImageTags.c.imageid) == Image._id',
            secondary = 'ImageTags',
            back_populates = '_tags',
            lazy = 'dynamic'
        )
        
        # Needed to determine if root tag exists
        _is_mysql = dk.is_mysql
        
        #: Needed for nested sets operations
        _has_nested_sets = dk.has_tags_nested_sets
        
        #: Needed for Tagstree operations
        _session = dk.session
        
        @validates('_pid')
        def _check_pid(self, key: str, value: int) -> int:
            if value < 0:
                raise DigikamAssignmentError('Tag parent id cannot be negative')
            return value
        
        # Special functions
        
        def __repr__(self) -> str:
            return '<Digikam Tag (%s, %d, %d)>' % (self.name, self.id, self.pid)
        
        def __contains__(self, obj: 'Tag') -> bool:
            if not isinstance(obj, Tag):
                raise TypeError('A tag can only contain other tags')
            if self._has_nested_sets:
                return self._lft < obj._lft and self._rgt > obj._rgt
            else:
                return self.id in obj._ancestors
        
        @property
        def id(self) -> int:
            """The tag's id (read-only)"""
            return self._id
        
        @property
        def pid(self) -> int:
            """The parent tag's id (read-only)"""
            return self._pid
        
        @property
        def name(self) -> str:
            """The tag's name"""
            return self._name
        
        @name.setter
        def name(self, value: str):
            self._name = value
        
        @property
        def icon(self) -> Union['Image', str, None]:        # noqa: F821
            """
            Returns the tag's icon.
            
            Possible types are:
            
            :`~_sqla.Image`:class:: The icon is an image from the Digikam
                                    collection. When setting, you can also
                                    specify the image's id.
            :`str`:class::          The icon is a KDE icon string
            :``None``:              No icon is set
            """
            if self._icon is not None:
                return self._iconObj
            return self._iconkde
        
        @icon.setter
        def icon(self, value: Union['Image', str, int, None]):  # noqa: F821
            if isinstance(value, self.digikam.images.Image):
                value = value.id
            if value is None:
                self._icon = None
                self._iconkde = None
            elif isinstance(value, int):
                self._icon = value
                self._iconkde = None
            elif isinstance(value, str):
                self._icon = None
                self._iconkde = value
            else:
                raise DigikamAssignmentError('Tag.icon must be Image, str, or None')
        
        @property
        def images(self) -> Iterable['Image']:              # noqa: F821
            """Images belonging to the tag (no setter)"""
            return self._images
        
        @property
        def _ancestors(self) -> List:
            """
            Returns the ancestors of a tag.
            
            Returns:
                In SQLite, an unsorted list with the ancestor's ids.
                In MySQL, a sorted list (top-down) with the ancestor objects.
            """
            log.debug('Getting ancestors for tag %d', self.id)
            
            if self._has_nested_sets:
                # MySQL
                return self._session.scalars(
                    select(Tag)
                    .where(Tag._lft < self._lft, Tag._rgt > self._rgt)
                    .order_by(Tag._lft)
                ).all()
            
            # We're on a newer DBVersion or on SQLite
            if self._is_mysql:
                min_pid = 0
            else:
                min_pid = 1
            return [
                row._pid
                for row in self._session.scalars(
                    select(self.digikam.tags.TagsTreeEntry).filter_by(_id = self.id)
                )
                if row._pid >= min_pid
            ]
            
        # Other properties and methods
        
        # Since Digikam doesn't use a foreign key, this is a regular property.
        @property
        def parent(self) -> Optional['Tag']:                # noqa: F821
            """
            Returns the tag's parent object.
            
            Returns ``None`` for
            
            * the root tag on MySQL or
            * tags at top level on SQLite
            
            .. todo:: Check for fresh MySQL DB with DBversion > 10
            """

            # Tags without a parent
            if self._is_mysql:
                if self.pid < 0:
                    return None
            else:
                if self.pid <= 0:
                    return None

            return self.digikam.tags._select(_id = self.pid).one()
        
        @property
        def children(self) -> Iterable['Tag']:              # noqa: F821
            """
            Returns the tag's children.
            """
            return self.digikam.tags._select(_pid = self.id)
        
        @property
        def properties(self) -> TagProperties:
            """
            Returns the tag's properties
            """
            if not hasattr(self, '_propertiesObj'):
                self._propertiesObj = TagProperties(self)
            return self._propertiesObj
        
        def hierarchicalname(self) -> str:
            """
            Returns the name including parents, separated by ``/``.
            """
            
            # Parent is the root tag or does not exist
            if self.pid <= 0:
                return self.name
            
            # No hierarchical name for internal tags:
            if 'internalTag' in self.properties:
                return self.name
            
            if self._has_nested_sets:
                return '/'.join(
                    [t.name for t in self._ancestors if t.id > 0]
                ) + '/' + self.name
            
            return self.parent.hierarchicalname() + '/' + self.name
        
        def _check(self):
            """
            Checks if the tree is consistent.
            
            Raises:
                DigikamDataIntegrityError
            """
            
            p = self.parent
            if p and self not in p:                         # pragma: no cover
                raise DigikamDataIntegrityError(
                    'Tag table: Tag id=%d is not in children of parent (%d)' % (
                        self.id, p.id
                    )
                )
            while p:
                if not isinstance(p, Tag):                  # pragma: no cover
                    raise DigikamError(
                        'Tag parent is of class %s, not Tag' % p.__class__.__name__
                    )
                if self not in p:                           # pragma: no cover
                    raise DigikamDataIntegrityError(
                        'Tag table inconsistent: Tag id=%d is not in descendents ' +
                        'of ancestor %d' % (self.id, p.id)  # noqa: F507
                    )
                if p.id == self.id:                         # pragma: no cover
                    raise DigikamDataIntegrityError(
                        'Tag table inconsistent: Circular ancestry in id=%d' % self.id
                    )
                p = p.parent
        
        def _check_nested_sets(self):
            """
            Checks if the tree is consistent.
            
            Raises:
                DigikamDataIntegrityError
            """
            d = self._rgt - self._lft
            if d <= 0 or d % 2 == 0:                        # pragma: no cover
                raise DigikamDataIntegrityError(
                    'Tag table: inconsistent lft, rgt in id=%d (%d,%d)' % (
                        self.id, self._lft, self._rgt
                    )
                )
            pos = self._lft
            for ch in self.children.order_by(self.__class__._lft):
                if not (
                    self._lft < ch._lft and self._rgt > ch._rgt
                ):                                          # pragma: no cover
                    raise DigikamDataIntegrityError(
                        'Tag table inconsistent: parent %d (%d,%d), child %d (%d,%d)' % (
                            self.id, self._lft, self._rgt, ch.id, ch._lft, ch._rgt
                        )
                    )
                for ch2 in self.children:
                    if ch == ch2:
                        continue
                    if ch._rgt < ch2._lft or ch._lft > ch2._rgt:
                        continue
                    raise DigikamDataIntegrityError(        # pragma: no cover
                        'Tag table has ' +
                        'overlapping siblings %d (%d,%d), %d (%d,%d)' % (
                            ch.id, ch._lft, ch._rgt, ch2.id, ch2._lft, ch2._rgt
                        )
                    )
                if ch._lft > pos + 1:                       # pragma: no cover
                    raise DigikamDataIntegrityError(
                        'Tag table inconsistent: gap before %d (%d), last pos %d' % (
                            ch.id, ch._lft, pos
                        )
                    )
                pos = ch._rgt
                ch._check_nested_sets()
    
    return Tag


class Tags(DigikamTable):
    """
    Offers access to the tags in the Digikam instance.
    
    ``Tags`` represents all tags present in the Digikam database. It is
    usually accessed through the :class:`~digikamdb.connection.Digikam`
    property :attr:`~digikamdb.connection.Digikam.tags`.
    
    Basic usage:
    
    .. code-block:: python
        
        dk = Digikam(...)
        mytag = dk.tags['My Tag']           # access by name
        mytag2 = dk.tags['parent/child']    # access by hierarchical name
        mytag3 = dk.tags[42]                # access by id
        newtag = dk.tags.add('New Tag', 0)  # creates new tag with name 'New Tag'
    
    Access via ``[]`` raises an exception if the name or id cannot be found,
    or if there are multiple matches.
    
    Parameters:
        digikam:     Digikam object for access to database and other classes.
    Raises:
        DigikamObjectNotFound:          No matching tag was found.
        DigikamMultipleObjectsFound:    Multiple tags where found when one
                                        was expected.
    
    See also:
        * Class :class:`~_sqla.Tag`
"""
    
    _class_function = _tag_class
    
    def __init__(
        self,
        digikam: 'Digikam',                                  # noqa: F821
    ):
        super().__init__(digikam)
        self._define_helper_tables()
    
    def _define_helper_tables(self):
        """Defines the classes for helper tables."""
        
        class TagProperty(self.digikam.base):
            """
            Tag Properties
            
            This table should be accessed via
            Class :class:`~digikamdb.tags.TagProperties`.
            """
            __tablename__ = 'TagProperties'
            
            _tagid = Column('tagid', Integer, primary_key = True)
            _property = Column('property', String, primary_key = True)
        
        self.TagProperty = TagProperty
        
        if not self.digikam.has_tags_nested_sets:
            class TagsTreeEntry(self.digikam.base):
                """
                Class for the tags tree
                
                This is a view on MySQL with DBVersion <= 10.
                
                .. versionchanged:: 0.2.2
                    Also defined for MySQL.
                """
                __tablename__ = 'TagsTree'
                
                _id = Column('id', Integer, primary_key = True)
                _pid = Column('pid', Integer, primary_key = True)
            
            self.TagsTreeEntry = TagsTreeEntry
    
    def _before_insert(
        self,
        mapper: 'Mapper',                                   # noqa: F821
        connection: 'Connection',                           # noqa: F821
        instance: 'Tag'                                     # noqa: F821
    ):
        """
        Adjusts the lft and rgt columns on insert.
        """
        
        if not self._do_before_insert:                      # pragma: no cover
            return

        if instance.pid < 0:                                # pragma: no cover
            # This will never happen, but we keep it for safety
            raise DigikamAssignmentError('Parent must be >= 0')
        
        log.debug('Reordering nested sets for tags before insert')
        tags = mapper.persist_selectable
        if instance.pid == 0:
            new_position = connection.scalar(
                select(tags.c.lft).where(
                    tags.c.name == '_Digikam_Internal_Tags_'))
        else:
            new_position = connection.scalar(
                select(tags.c.rgt).where(
                    tags.c.id == instance.pid))

        connection.execute(
            tags.update().where(tags.c.rgt >= new_position).values(
                lft = case(
                    (
                        tags.c.lft >= new_position,
                        tags.c.lft + 2,
                    ),
                    else_ = tags.c.lft
                ),
                rgt = tags.c.rgt + 2,
            )
        )
        
        instance._lft = new_position
        instance._rgt = new_position + 1

    # before_update() would be needed to support moving of nodes
    def _before_update(
        self,
        mapper: 'Mapper',                                   # noqa: F821
        connection: 'Connection',                           # noqa: F821
        instance: 'Tag'                                     # noqa: F821
    ):
        if not self._do_before_update:                      # pragma: no cover
            return
        
        log.debug('Reordering nested sets for tags before update')
        attrs = inspect(instance).attrs
        if (
            attrs._pid.history.has_changes() or
            attrs._lft.history.has_changes() or
            attrs._rgt.history.has_changes()
        ):
            raise NotImplementedError('Moving tags is not implemented')
    
    # after_delete() would be needed to support removal of nodes.
    def _after_delete(
        self,
        mapper: 'Mapper',                                   # noqa: F821
        connection: 'Connection',                           # noqa: F821
        instance: 'Tag'                                     # noqa: F821
    ):
        """
        Adjusts the lft and rgt columns on delete.
        """

        if not self._do_after_delete:                       # pragma: no cover
            return
        
        if instance._rgt - instance._lft > 1:               # pragma: no cover
            raise DigikamError('Cannot delete tag with sub-tags')

        log.debug('Reordering nested sets for tags after delete')
        
        tags = mapper.persist_selectable
        right = instance._rgt
        
        connection.execute(
            tags.update().where(tags.c.rgt > right).values(
                lft = case(
                    (
                        tags.c.lft > right,
                        tags.c.lft - 2,
                    ),
                    else_ = tags.c.lft
                ),
                rgt = tags.c.rgt - 2
            )
        )

    def setup(self):
        """
        Sets the event listeners for nested sets.
        
        Called by Digikam constructor.
        """
        
        self._do_before_insert = False
        self._do_before_update = False
        self._do_after_delete = False
        self._has_nested_sets = False
        
        if self.digikam.has_tags_nested_sets:
            self._do_before_insert = True
            self._do_before_update = True
            self._do_after_delete = True

            event.listen(self.Class, 'before_insert', self._before_insert)
            event.listen(self.Class, 'before_update', self._before_update)
            event.listen(self.Class, 'after_delete', self._after_delete)
    
    def __getitem__(self, key):
        if isinstance(key, str):
            if '/' in key:
                name = key.split('/')[-1]
            else:
                name = key
            
            q = self._select(_name = name)
            num = q.count()
            if num == 0:
                raise DigikamObjectNotFound('No Tag for name=' + key)
            
            if num == 1:
                tag = q.one()
                if '/' not in key:
                    return tag
                if tag.hierarchicalname() == key:
                    return tag
                raise DigikamObjectNotFound('No Tag for name=' + key)
            
            for tag in q:
                if tag.hierarchicalname() == key:
                    return tag
            
            if '/' in key:
                raise DigikamObjectNotFound('No Tag for name=' + key)
            else:
                raise DigikamMultipleObjectsFound('Multiple tags for name=' + key)

        return super().__getitem__(key)

    @property
    def _root(self) -> 'Tag':                               # noqa: F821
        """
        Returns the root tag when on MySQL.
        
        Raises:
            DigikamObjectNotFound:  When called on SQLite.
        """
        try:
            return self._select(_pid = -1).one()
        except NoResultFound:
            raise DigikamObjectNotFound('No tag for pid=-1')
    
    def add(
        self,
        name: str,
        parent: Union[int, 'Tag'],                          # noqa: F821
        icon: Optional[Union['Image', str, int]] = None,    # noqa: F821
    ) -> 'Tag':                                             # noqa: F821
        """
        Adds a new tag.
        
        To create a Tag at the root of the tag tree, set ``parent`` to 0.
        
        Parameters:
            name:   The new tag's name
            parent: The new tag's parent as an id or a Tag object
            icon:   The new tag's icon. If given as an Image, the icon is set
                    to this Image from the Digikam collection. If given as an
                    int, the icon is set to the image with the id **icon**. If
                    given as a str, the icon is set to the corresponding KDE
                    icon.
        Returns:
            The newly created tag object.
        """
        
        if isinstance(parent, self.Class):
            pid = parent.id
        elif isinstance(parent, int):
            pid = parent
        else:
            raise TypeError('Parent must be int or Tag')
        
        options = {}
        if icon is not None:
            if isinstance(icon, self.digikam.images.Class):
                options['icon'] = icon.id
            elif isinstance(icon, int):
                options['icon'] = icon
            elif isinstance(icon, str):
                options['iconkde'] = icon
            else:
                raise TypeError('Icon must be int, str or Image')
        
        return self._insert(name = name, pid = pid, **options)
    
    def remove(self, tag: Union[int, 'Tag']):               # noqa: F821
        """
        Removes a tag.
        
        Parameters:
            tag:    the tag to delete. Can be a :class:`Tag` object or an id.
        """
        
        if isinstance(tag, int):
            tag = self[tag]
        elif not isinstance(tag, self.Class):
            raise TypeError('Tag must be int or ' + self.Class.__name__)
        
        for p in tag.properties._select_self().all():
            self._session.delete(p)
        self._session.delete(tag)
    
    def check(self):
        """
        Checks the integrity of the *Tags* table.
        
        Checks that
        
        * each tag is among the children of its parent
        * each tag is contained in its ancestors
        * there are no circular parent-child relations
        * the nested sets and adjacency list structures are consistent
          (MySQL with DBVersion <= 10 only)
        
        Raises:
            DigikamDataIntegrityError:  Table is in an inconsistent state.
        
        .. versionchanged:: 0.2.2
            Do not check nested sets for DBVersion > 10
        """

        for tag in self:
            tag._check()
        if self.digikam.has_tags_nested_sets:
            self._root._check_nested_sets()


def _tagproperty_class(dk: 'Digikam') -> type:              # noqa: F821
    """Defines the TagProperty class."""
    return dk.tags.TagProperty


class TagProperties(BasicProperties):
    """
    Tag Properties

    Args:
        digikam(Digikam):   Digikam object.
        parent(Tag):        The corresponding ``Tag`` object.
    """
    
    # Funktion returning the table class
    _class_function = _tagproperty_class
    
    # Parent id column
    _parent_id_col = '_tagid'
    
    # Key column
    _key_col = '_property'
    
    # Value column
    _value_col = '_value'
    
    _tagid = Column('tagid', Integer, primary_key = True)
    _property = Column('tagid', String, primary_key = True)
    

