# Test base

import logging
import os
from unittest import TestCase, skip     # noqa: F401

from sqlalchemy.exc import NoResultFound    # noqa: F401

from digikamdb import DigikamDataIntegrityError
from digikamdb.types import ImageCategory


log = logging.getLogger(__name__)


class SanityCheck:
    """Mixin with some sanity checks"""
    
    def test00_class_definitions(self):
        self.assertIs(self.dk.albumRoots.Class, self.dk.albumRoots.AlbumRoot)
        self.assertIs(self.dk.albums.Class, self.dk.albums.Album)
        self.assertIs(self.dk.images.Class, self.dk.images.Image)
        self.assertIs(self.dk.tags.Class, self.dk.tags.Tag)
        self.assertIs(self.dk.settings.Class, self.dk.settings.Setting)
    
    def test10_albumroots(self):
        for ar in self.dk.albumRoots:
            with self.subTest(albumrootid = ar.id):
                self.assertIsInstance(ar, self.dk.albumRoots.Class)
                self.assertIs(ar, self.dk.albumRoots[ar.id])
    
    def test20_albums(self):
        for al in self.dk.albums:
            with self.subTest(albumid = al.id):
                self.assertIsInstance(al, self.dk.albums.Class)
                self.assertEqual(al._albumRoot, al.root.id)
                self.assertIn(al, al.root.albums)
                self.assertEqual(
                    os.path.commonpath([self.mydir, al.abspath]),
                    self.mydir)
    
    def test30_images(self):
        for img in self.dk.images:
            with self.subTest(imageid = img.id):
                self.assertIsInstance(img, self.dk.images.Class)
                self.assertEqual(img._album, img.album.id)
                self.assertIn(img, img.album.images)
                self.assertEqual(img.id, img.information._imageid)
                if img.category == ImageCategory.Image:
                    self.assertEqual(img.id, img.imagemeta._imageid)
                if img.category == ImageCategory.Video:
                    self.assertEqual(img.id, img.videometa._imageid)
                self.assertEqual(
                    img.abspath,
                    os.path.join(img.album.abspath, img.name))
                for k, v in img.titles.items():
                    self.assertIsInstance(k, str)
                    self.assertIsInstance(v, str)
                for k, v in img.properties.items():
                    self.assertIsInstance(k, str)
                    self.assertIsInstance(v, str)
    
    def test31_image_tags(self):
        for img in self.dk.images:
            for tag in img.tags:
                with self.subTest(imageid = img.id, tagid = tag.id):
                    self.assertIn(img, tag.images)
    
    def test40_tags(self):
        for tag in self.dk.tags:
            with self.subTest(tagid = tag.id):
                self.assertIsInstance(tag, self.dk.tags.Class)
                if tag.parent:
                    self.assertIn(tag, tag.parent.children)
                for ch in tag.children:
                    self.assertEqual(tag.id, ch.pid)
                    self.assertIs(tag, ch.parent)
                hname = tag.hierarchicalname()
                if '/' in hname:
                    self.assertEqual(
                        self.parent.hierarchicalname() + '/' + self.name,
                        hname
                    )
                    self.assertIs(tag, self.dk.tags[hname])
                self.assertIn(tag, self.dk.tags.select(name = tag.name))
                self.assertRegex(str(tag), '<Digikam Tag (.*)>')
                with self.assertRaises(TypeError):
                    'tag name' in tag
                numprops = 0
                props = []
                for k, v in tag.properties.items():
                    numprops += 1
                    props.append(k)
                    self.assertIsInstance(k, str)
                    if v is not None:
                        self.assertIsInstance(v, str)
                self.assertEqual(numprops, len(tag.properties))
                for k in tag.properties:
                    self.assertIn(k._property, props)
    
    def test41_tags_check(self):
        try:
            self.dk.tags.check()
        except DigikamDataIntegrityError:
            self.fail('Tags table inconsistent')
    
    def test42_tags_internal(self):
        internal = self.dk.tags['_Digikam_Internal_Tags_']
        self.assertEqual(internal.id, 1)
        for tag in internal.children:
            with self.subTest(internal_tag = tag.name):
                self.assertIn('internalTag', tag.properties)
                self.assertFalse(tag.children.first())
    
    def test50_settings(self):
        settings = {}
        for k, v in self.dk.settings.items():
            self.assertEqual(self.dk.settings[k], v)
            settings[k] = v
        for k in self.dk.settings:
            self.assertEqual(self.dk.settings[k], settings[k])

