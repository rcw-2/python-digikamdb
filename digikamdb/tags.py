"""
Digikam Tags
"""

from typing import Any, Iterable, List, Optional, Union

from sqlalchemy import MetaData, Table, case, event, func, insert, inspect, select, update
from sqlalchemy.orm import object_session

from .table import DigikamTable
from .properties import BasicProperties
from .exceptions import DigikamError


def _tag_class(dk: 'Digikam') -> type:
    """
    Defines the Tag class
    """
    
    class Tag(dk.base):
        """
        Digikam tag.
        
        The following column-related properties can be directly accessed:
        
        * **id** (*int*)
        * **name** (*str*) - The tag's name.
        * **icon** (*int*)
        * **iconkde** (*str*)
        
        Tags in Digikam are hierarchical. ``Tag`` reflects this by providing:
        
        * The :attr:`parent` and :attr:`children` properties,
        * ``tag1 in tag2`` can be used to test if ``tag2`` is an ancestor of
          ``tag1``.
        * The :meth:`hierarchicalname` method.
        
        """
        
        __tablename__ = 'Tags'
        __mapper_args__ = {
            "batch": False  # allows extension to fire for each
                            # instance before going to the next.
        }
        
        # Special functions
        
        def __repr__(self) -> str:
            return 'Digikam Tag (%s, %d, %d)' % (self.name, self.id, self.pid)
        
        def __contains__(self, obj: 'Tag') -> bool:
            if not isinstance(obj, Tag):
                raise TypeError('A tag can only contain other tags')
            if Tag.is_mysql:
                return self.lft < obj.lft and self.rgt > obj.rgt
            else:
                return self.id in obj.ancestors
        
        @property
        def ancestors(self) -> List:
            anc = []
            if self.is_mysql:
                # MySQL
                return [tag.id for tag in self.session.scalars(
                    select(Tag)
                        .where(Tag.lft < self.lft,
                               Tag.rgt > self.rgt))]
            
            # We're on SQLite
            conn = self.session.connection()
            return [row['id'] for row in conn.execute(
                select(self.tagtree_table)
                    .filter(text("id = %d" % self.id)))]
            
        
        # Other properties and methods
        
        # Since Digikam doesn't use a foreign key, this is a regular property.
        @property
        def parent(self) -> Optional['Tag']:
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

            return self.session.scalars(
                select(Tag).filter_by(id = self.pid)
            ).one()
        
        @property
        def children(self) -> Iterable['Tag']:
            """
            Returns the tag's children.
            """
            # Since Digikam doesn't use a foreign key, this is a regular property.
            
            return self.session.scalars(
                select(Tag).filter_by(pid = self.id))
        
        @property
        def properties(self) -> TagProperties:
            """
            Returns the tag's properties
            """
            
            if not hasattr(self, '_properties'):
                self._properties = TagProperties(self)
            return self._properties
        
        def hierarchicalname(self) -> str:
            """
            Returns the name including parents.
            """
            if self.pid < 0:
                return self.name
            else:
                return self.parent.hierarchicalname() + '/' + self.name
        
        def check_tree(self):
            """
            Checks if the tree is consistent
            """
            
            d = self.rgt - self.lft
            if d <= 0 or d % 2 == 0:
                raise DigikamError('Tag table inconsistent: %d (%d,%d)' % (
                    self.id, self.lft, self.rgt))
            
            p = self.parent
            while p:
                if not self in p:
                    raise DigikamError('Internal Error')
                p = p.parent
            
            for ch in self.children:
                if not (self.lft < ch.lft and self.rgt > ch.rgt):
                    raise DigikamError(
                        'Tag table inconsistent: parent %d (%d,%d), child %d (%d,%d)' % (
                            self.id, self.lft, self.rgt, ch.id, ch.lft, ch.rgt))
                for ch2 in self.children:
                    if ch == ch2:
                        continue
                    if ch.rgt < ch2.lft or ch.lft > ch2.rgt:
                        continue
                    raise DigikamError(
                        'Tag table inconsistent: overlapping siblings %d (%d,%d), %d (%d,%d)' % (
                            ch.id, ch.lft, ch.rgt, ch2.id, ch2.lft, ch2.rgt))
                ch.check_tree()
    
    return Tag


class Tags(DigikamTable):
    """
    Offers access to the tags in the Digikam instance.
    
    ``Tags`` represents all tags present in the Digikam database. It is
    usually accessed through the :class:`~digikamdb.connection.Digikam`
    property :attr:`~digikamdb.connection.Digikam.tags`.
    
    Usage:
    
    .. code-block:: python
        
        dk = Digikam(...)
        mytag = dk.tags['My Tag']       # access by name
        mytag2 = dk.tags[42]            # access by id
        newtag = dk.text.add('New Tag') # creates new tag with name 'New Tag'
    
    Access via ``[]`` returns ``None`` if the name or id cannot be found.
    If there are multiple matches, an exception is raised.
    
    Parameters:
        parent:     Digikam object for access to database and other classes.
    """
    
    class_function = _tag_class
    
    def __init__(
        self,
        parent: 'Digikam',
    ):
        super().__init__(parent)
        self.Class.properties_table = Table(
            'TagProperties',
            parent.base.metadata,
            autoload_with = self.parent.engine)
        if not self.is_mysql:
            self.Class.tagtree_table = Table(
                'TagsTree',
                parent.base.metadata,
                autoload_with = self.parent.engine)
    
    
    def _before_insert(self, mapper: 'Mapper', connection: 'Connection', instance: 'Tag'):
        """
        Adjusts the lft and rgt columns on insert.
        """
        
        if not self._do_before_insert:
            return

        if instance.pid < 0:
            raise ValueError('Parent must be specified')

        tags = mapper.mapped_table
        right_most_sibling = connection.scalar(
            select(tags.c.rgt).where(
                tags.c.id == instance.pid))

        connection.execute(
            tags.update(tags.c.rgt >= right_most_sibling).values(
                lft = case(
                    [(
                        tags.c.lft > right_most_sibling,
                        tags.c.lft + 2, )],
                    else_ = tags.c.lft),
                rgt = case(
                    [(
                        tags.c.rgt >= right_most_sibling,
                        tags.c.rgt + 2, )],
                    else_ = tags.c.rgt)))
        
        instance.lft = right_most_sibling
        instance.rgt = right_most_sibling + 1

    # before_update() would be needed to support moving of nodes
    def _before_update(self, mapper: 'Mapper', connection: 'Connection', instance: 'Tag'):
        if not self._do_before_update:
            return
        
        if object_session(instance).is_modified(instance, include_collections = False):
            attrs = inspect(instance).attrs
            if (
                attrs.pid.history.has_changes() or
                attrs.lft.history.has_changes() or
                attrs.rgt.history.has_changes()
            ):
                raise NotImplementedError('Moving tags is not implemlemented')
    
    # after_delete() would be needed to support removal of nodes.
    def _after_delete(self, mapper: 'Mapper', connection: 'Connection', instance: 'Tag'):
        """
        Adjusts the lft and rgt columns on delete.
        """

        if not self._do_after_delete:
            return
        
        if instance.rgt - instance.lft > 1:
            raise DigikamError('Cannot delete tag with sub-tags')

        tags = mapper.mapped_table
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
            return self.session.scalars(
                select(self.Class).filter_by(name = key)
            ).one_or_none()
        
        return super().__getitem__(key)
    
    @property
    def _root(self) -> 'Tag':
        """
        Returns the root tag when on MySQL.
        
        Raises :exc:`~sqlalchemy.exc.NoResultError` in SQLite.
        """
        return self.select(pid = -1).one()
    
    def add(self, name: str, parent: Union[int,'Tag']) -> 'Tag':
        """
        Adds a new tag.
        
        Parameters:
            name:   the new tag's name
            parent: the new tag's parent as an id or a Tag object
        Returns:
            The newly created tag object.
        """
        
        if isinstance(parent, self.Class):
            pid = parent.id
        elif isinstance(parent, int):
            pid = parent
        else:
            raise TypeError('Parent must be int or Tag')
        
        return self.insert(name = name, pid = pid)
    
    def remove(self, tag: Union[int,'Tag']):
        """
        Removes a tag.
        
        Parameters:
            tag:    the tag to delete. Can be a :class:`Tag` object or an id.
        """
        
        if isinstance(tag, self.Class):
            pass
        elif isinstance(tag, int):
            tag = self.session.scalars(
                select(self.Class).filter_by(id = key)
            ).one()
        else:
            raise TypeError('Tag must be int or Tag')
        
        self.parent.delete(tag)
        self.parent.commit()
    
    def check(self) -> None:
        """
        Checks the integrity of the *Tags* table.
        
        Raises an exception on SQLite.
        """
        
        self._root.check_tree()

class TagProperties(BasicProperties):
    """
    Tag Properties
    """
    
    # Parent id column
    _parent_id_col = 'tagid'
    
    # Key column
    _key_col = 'property'    
    
    # Value column
    _value_col = 'value'

