# Test base

import logging
from unittest import TestCase, skip                         # noqa: F401

from sqlalchemy.exc import NoResultFound                    # noqa: F401

from digikamdb.exceptions import *                          # noqa: F403

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
    
    def test30_images(self):                                # noqa: C901
        for data in self.test_data['images']:
            with self.subTest(imageid = data['id']):
                img = self.dk.images[data['id']]
                for prop, value in data.items():
                    if prop == 'information':
                        for p, v in value.items():
                            self.assertEqual(getattr(img.information, p), v)
                    elif prop == 'imagemeta':
                        for p, v in value.items():
                            self.assertEqual(getattr(img.imagemeta, p), v)
                    elif prop == 'videometa':
                        for p, v in value.items():
                            self.assertEqual(getattr(img.videometa, p), v)
                    elif prop == 'properties':
                        for p, v in value.items():
                            self.assertEqual(img.properties[p], v)
                    elif prop == 'titles':
                        for p, v in value.items():
                            self.assertEqual(img.titles[p], v)
                    elif prop == 'captions':
                        for p, v in value.items():
                            self.assertEqual(img.captions[p], v)
                    elif prop == 'copyright':
                        for p, v in value.items():
                            self.assertEqual(img.copyright[p], v)
                    elif prop == 'title':
                        self.assertEqual(img.title, value)
                        self.assertEqual(img.titles[None], value)
                        self.assertEqual(img.titles[''], value)
                    else:
                        self.assertEqual(getattr(img, prop), value)
                
                self.assertIsNone(img.titles['no-language'])
                self.assertIsNone(
                    img.titles.select(language = 'no-language').one_or_none()
                )
                img.titles['no-language'] = None                # should call remove()
                self.assertIsNone(
                    img.titles.select(language = 'no-language').one_or_none()
                )
                
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
        
        name = self.test_data['tags'][0]['name']
        with self.assertRaises(DigikamObjectNotFound):
            _ = self.dk.tags['not/existing/parent/' + name]


