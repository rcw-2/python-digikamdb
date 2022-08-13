# Test base

import logging
from unittest import TestCase, skip     # noqa: F401

from sqlalchemy.exc import NoResultFound    # noqa: F401


log = logging.getLogger(__name__)


class TestData:
    """Mixin to check test data"""
    
    def test10_albumroots(self):
        for data in self.test_data['albumroots']:
            with self.subTest(albumrootid = data['id']):
                ar = self.dk.albumRoots[data['id']]
                self.assertIsInstance(ar, self.dk.albumRoots.Class)
                self.assertEqual(ar.label, data['label'])
                self.assertEqual(
                    ar.mountpoint,
                    self.replacepath(data['mountpoint']))
                self.assertEqual(
                    ar.abspath,
                    self.replacepath(data['path']))
    
    def test20_albums(self):
        for data in self.test_data['albums']:
            with self.subTest(albumid = data['id']):
                al = self.dk.albums[data['id']]
                self.assertEqual(al.id, data['id'])
                self.assertEqual(
                    al.abspath,
                    self.replacepath(data['path']))
    
    def test30_images(self):
        for data in self.test_data['images']:
            with self.subTest(imageid = data['id']):
                img = self.dk.images[data['id']]
                for prop, value in data.items():
                    self.assertEqual(getattr(img, prop), value)
                
                img2 = self.dk.images.find(img.abspath)[0]
                self.assertIs(img, img2)
        
        with self.subTest(file = 'not in DB'):
            self.assertFalse(self.dk.images.find('/does/not/exist'))
        
        if 'image_queries' in self.test_data:
            for data in self.test_data['image_queries']:
                with self.subTest(select = data['where']):
                    num = 0
                    for img in self.dk.images.select(*data['where']):
                        num = num + 1
                        self.assertIn(img.id, data['result'])
                    self.assertEqual(num, len(data['result']))
    
    def test40_tags(self):
        for data in self.test_data['tags']:
            with self.subTest(tagid = data['id']):
                tag = self.dk.tags[data['name']]
                self.assertEqual(tag.id, data['id'])
                self.assertEqual(tag.pid, data['pid'])
                
                tag2 = self.dk.tags[tag.id]
                self.assertIs(tag, tag2)


