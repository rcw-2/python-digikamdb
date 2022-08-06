"""
Enables access to Digikam tags.
"""

import logging
from typing import Iterable, List, Optional, Union

from sqlalchemy import (
    Column, Integer, String, Table,
    case, event, inspect, select, text,
)
from sqlalchemy.orm import object_session, relationship

from .table import DigikamTable
from .properties import BasicProperties
from .exceptions import DigikamError, DigikamDataIntegrityError


log = logging.getLogger(__name__)


def _tag_class(dk: 'Digikam') -> type:                      # noqa: F821, C901
    """
    Defines the Tag class
    """
    
    class Tag(dk.base):
        """
        Digikam tag.
        
        The following column-related properties can be directly accessed:
        
        * **id** (*int*)
        * **pid** (*int*) - The parent tag's id.
        * **name** (*str*) - The tag's name.
        * **icon** (*int*)
        * **iconkde** (*str*)
        
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

        See also:
            * Class :class:`~digikamdb.tags.Tags`
        """
        
        __tablename__ = 'Tags'
        __mapper_args__ = {
            "batch": False  # allows extension to fire for each
                            # instance before going to the next.
        }
        _properties = relationship(
            'TagProperty',
            primaryjoin = 'foreign(TagProperty.tagid) == Tag.id',
            lazy = 'dynamic')
        
        # Special functions
        
        def __repr__(self) -> str:
            return '<Digikam Tag (%s, %d, %d)>' % (self.name, self.id, self.pid)
        
        def __contains__(self, obj: 'Tag') -> bool:
            if not isinstance(obj, Tag):
                raise TypeError('A tag can only contain other tags')
            if Tag.is_mysql:
                return self.lft < obj.lft and self.rgt > obj.rgt
            else:
                return self.id in obj._ancestors
        
        @property
        def _ancestors(self) -> List:
            """
            Returns the ancestors of a tag.
            
            Returns:
                In SQLite, an unsorted list with the ancestor's ids.
                In MySQL, a sorted list (top-down) with the ancestor objects.
            """
            log.debug('Getting ancestors for tag %d', self.id)
            
            if self.is_mysql:
                # MySQL
                return self._session.scalars(
                    select(Tag)
                    .where(Tag.lft < self.lft, Tag.rgt > self.rgt)
                    .order_by(Tag.lft)
                ).all()
            
            # We're on SQLite
            return [
                row.pid
                for row in self._session.scalars(
                    select(self._container.TagsTreeEntry).filter_by(id = self.id)
                )
                if row.pid > 0
            ]
            
        # Other properties and methods
        
        # Since Digikam doesn't use a foreign key, this is a regular property.
        @property
        def parent(self) -> Optional['Tag']:                # noqa: F821
            """
            Returns the tag's parent object.
            
            For the root tag, returns ``None``.
            """

            # Tags without a parent
            if self.is_mysql:
                if self.pid < 0:
                    return None
            else:
                if self.pid <= 0:
                    return None

            return self._container._select(id = self.pid).one()
        
        @property
        def children(self) -> Iterable['Tag']:              # noqa: F821
            """
            Returns the tag's children.
            """
            return self._container._select(pid = self.id)
        
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
            
            if self.is_mysql:
                return '/'.join(
                    [t.name for t in self._ancestors if t.id > 0]
                ) + '/' + self.name
            
            if self.parent:
                return self.parent.hierarchicalname() + '/' + self.name
            
            raise DigikamDataIntegrityError(
                'Unable to generate hierarchical name for tag %d (%s)',
                self.id, self.name,
            )
        
        def _check(self):
            """
            Checks if the tree is consistent.
            
            Raises:
                DigikamDataIntegrityError
            """
            
            p = self.parent
            if p and self not in p:
                raise DigikamDataIntegrityError(
                    'Tag table: Tag id=%d is not in children of parent (%d)' % (
                        self.id, p.id
                    )
                )
            while p:
                if not isinstance(p, Tag):
                    raise DigikamError(
                        'Tag parent is of class %s, not Tag' % p.__class__.__name__
                    )
                if self not in p:
                    raise DigikamDataIntegrityError(
                        'Tag table inconsistent: Tag id=%d is not in descendents ' +
                        'of ancestor %d' % (self.id, p.id)  # noqa: F507
                    )
                if p.id == self.id:
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
            d = self.rgt - self.lft
            if d <= 0 or d % 2 == 0:
                raise DigikamDataIntegrityError(
                    'Tag table: inconsistent lft, rgt in id=%d (%d,%d)' % (
                        self.id, self.lft, self.rgt
                    )
                )
            pos = self.lft
            for ch in self.children.order_by(self.__class__.lft):
                if not (self.lft < ch.lft and self.rgt > ch.rgt):
                    raise DigikamDataIntegrityError(
                        'Tag table inconsistent: parent %d (%d,%d), child %d (%d,%d)' % (
                            self.id, self.lft, self.rgt, ch.id, ch.lft, ch.rgt
                        )
                    )
                for ch2 in self.children:
                    if ch == ch2:
                        continue
                    if ch.rgt < ch2.lft or ch.lft > ch2.rgt:
                        continue
                    raise DigikamDataIntegrityError(
                        'Tag table has ' +
                        'overlapping siblings %d (%d,%d), %d (%d,%d)' % (
                            ch.id, ch.lft, ch.rgt, ch2.id, ch2.lft, ch2.rgt
                        )
                    )
                if ch.lft > pos + 1:
                    raise DigikamDataIntegrityError(
                        'Tag table inconsistent: gap before %d (%d), last pos %d' % (
                            ch.id, ch.lft, pos
                        )
                    )
                pos = ch.rgt
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
        mytag2 = dk.tags[42]                # access by id
        newtag = dk.tags.add('New Tag', 0)  # creates new tag with name 'New Tag'
    
    Access via ``[]`` returns ``None`` if the name or id cannot be found.
    If there are multiple matches, an exception is raised.
    
    Parameters:
        digikam:     Digikam object for access to database and other classes.
    
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
            
            tagid = Column(Integer, primary_key = True)
            property = Column(String, primary_key = True)
        
        if not self.is_mysql:
            class TagsTreeEntry(self.digikam.base):
                """Class for the tags tree"""
                __tablename__ = 'TagsTree'
                
                id = Column(Integer, primary_key = True)
                pid = Column(Integer, primary_key = True)
            
            self.TagsTreeEntry = TagsTreeEntry
        
        self.TagProperty = TagProperty
    
    def _before_insert(
        self,
        mapper: 'Mapper',                                   # noqa: F821
        connection: 'Connection',                           # noqa: F821
        instance: 'Tag'                                     # noqa: F821
    ):
        """
        Adjusts the lft and rgt columns on insert.
        """
        
        if not self._do_before_insert:
            return

        if instance.pid < 0:
            raise ValueError('Parent must be >= 0')
        
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
            tags.update(tags.c.rgt >= new_position).values(
                lft = case(
                    [(
                        tags.c.lft >= new_position,
                        tags.c.lft + 2, )],
                    else_ = tags.c.lft),
                rgt = case(
                    [(
                        tags.c.rgt >= new_position,
                        tags.c.rgt + 2, )],
                    else_ = tags.c.rgt)))
        
        instance.lft = new_position
        instance.rgt = new_position + 1

    # before_update() would be needed to support moving of nodes
    def _before_update(
        self,
        mapper: 'Mapper',                                   # noqa: F821
        connection: 'Connection',                           # noqa: F821
        instance: 'Tag'                                     # noqa: F821
    ):
        if not self._do_before_update:
            return
        
        log.debug('Reordering nested sets for tags before update')
        if object_session(instance).is_modified(
            instance,
            include_collections = False
        ):
            attrs = inspect(instance).attrs
            if (
                attrs.pid.history.has_changes() or
                attrs.lft.history.has_changes() or
                attrs.rgt.history.has_changes()
            ):
                raise NotImplementedError('Moving tags is not implemlemented')
    
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

        if not self._do_after_delete:
            return
        
        if instance.rgt - instance.lft > 1:
            raise DigikamError('Cannot delete tag with sub-tags')

        log.debug('Reordering nested sets for tags after delete')
        
        tags = mapper.persist_selectable
        right = instance.rgt
        
        connection.execute(
            tags.update(tags.c.rgt > right).values(
                lft = case(
                    [(
                        tags.c.lft > right,
                        tags.c.lft - 2, )],
                    else_ = tags.c.lft),
                rgt = case(
                    [(
                        tags.c.rgt > right,
                        tags.c.rgt - 2, )],
                    else_ = tags.c.rgt)))

    def setup(self):
        """
        Sets the event listeners for nested sets.
        
        Called by Digikam constructor.
        """
        
        if self.is_mysql:
            self._do_before_insert = True
            self._do_before_update = True
            self._do_after_delete = True

            event.listen(self.Class, 'before_insert', self._before_insert)
            event.listen(self.Class, 'before_update', self._before_update)
            event.listen(self.Class, 'after_delete', self._after_delete)
        
        else:
            self._do_before_insert = False
            self._do_before_update = False
            self._do_after_delete = False
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return self._select(name = key).one()
        
        return super().__getitem__(key)
    
    @property
    def _root(self) -> 'Tag':                               # noqa: F821
        """
        Returns the root tag when on MySQL.
        
        Raises :exc:`~sqlalchemy.exc.NoResultError` in SQLite.
        """
        return self._select(pid = -1).one()
    
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
          (MySQL only)
        
        Raises:
            DigikamDataIntegrityError:  Table is in an inconsistent state.
        """

        for tag in self:
            tag._check()
        if self.Class.is_mysql:
            self._root._check_nested_sets()
    
    def find(self, name: str) -> List['Tag']:               # noqa: F821
        """
        Finds all tags with a certain name.
        
        Since tags are hierarchical, it is possible that more than one tag
        have the same name. This funcion returns a list with all of them.
        
        Args:
            name:   Tag name to find.
        Returns:
            List containing the found tags
        """
        return self._select(name = name).all()


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
    _parent_id_col = 'tagid'
    
    # Key column
    _key_col = 'property'
    
    # Value column
    _value_col = 'value'
    
    tagid = Column(Integer, primary_key = True)
    property = Column(String, primary_key = True)
    

