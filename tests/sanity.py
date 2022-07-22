# Test base

import logging
import os
from unittest import TestCase, skip     # noqa: F401

from sqlalchemy.exc import NoResultFound    # noqa: F401


log = logging.getLogger(__name__)


class SanityCheck:
    """Mixin with some sanity checks"""
    
    def test10_albumroots(self):
        for ar in self.dk.albumRoots:
            with self.subTest(albumrootid = ar.id):
                self.assertIsInstance(ar, self.dk.albumroot_class)
                self.assertIs(ar, self.dk.albumRoots[ar.id])
    
    def test11_albums(self):
        for al in self.dk.albums:
            with self.subTest(albumid = al.id):
                self.assertIsInstance(al, self.dk.album_class)
                self.assertEqual(al.albumRoot, al.root.id)
                self.assertIn(al, al.root.albums)
                self.assertEqual(
                    os.path.commonpath([self.mydir, al.abspath]),
                    self.mydir)
    
    def test12_images(self):
        for img in self.dk.images:
            with self.subTest(imageid = img.id):
                self.assertIsInstance(img, self.dk.image_class)
                self.assertEqual(img.album, img.albumObj.id)
                self.assertIn(img, img.albumObj.images)
                self.assertEqual(img.id, img.information.imageid)
                if img.category == 1:
                    self.assertEqual(img.id, img.imagemeta.imageid)
                if img.category == 2:
                    self.assertEqual(img.id, img.videometa.imageid)
                self.assertEqual(
                    img.abspath,
                    os.path.join(img.albumObj.abspath, img.name))
    
    def test13_tags(self):
        for tag in self.dk.tags:
            with self.subTest(tagid = tag.id):
                self.assertIsInstance(tag, self.dk.tag_class)
                if tag.parent:
                    self.assertIn(tag, tag.parent.children)
                for ch in tag.children:
                    self.assertEqual(tag.id, ch.pid)
                    self.assertIs(tag, ch.parent)
    
    def test14_tags_internal(self):
        internal = self.dk.tags['_Digikam_Internal_Tags_']
        self.assertEqual(internal.id, 1)
        for tag in internal.children:
            with self.subTest(internal_tag = tag.name):
                self.assertIn('internalTag', tag.properties)

