# Test base

import datetime
import logging
import os
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, skip     # noqa: F401

from sqlalchemy.exc import NoResultFound


log = logging.getLogger(__name__)


class DigikamTestBase(TestCase):
    """Base Class"""
    
    @classmethod
    def setUpClass(cls):
        log.info('Setting up %s', cls.__name__)
        cls.mydir = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        log.info('Tearing down %s', cls.__name__)
        rmtree(cls.mydir)
    
    def replacepath(self, path):
        return path.replace('MYDIR', self.mydir)


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


class TestData:
    """Mixin to check test data"""
    
    def test10_albumroots(self):
        for data in self.test_data['albumroots']:
            with self.subTest(albumrootid = data['id']):
                ar = self.dk.albumRoots[data['id']]
                self.assertIsInstance(ar, self.dk.albumroot_class)
                self.assertEqual(ar.label, data['label'])
                self.assertEqual(
                    ar.mountpoint,
                    self.replacepath(data['mountpoint']))
                self.assertEqual(
                    ar.abspath,
                    self.replacepath(data['path']))
    
    def test11_albums(self):
        for data in self.test_data['albums']:
            with self.subTest(albumid = data['id']):
                al = self.dk.albums[data['id']]
                self.assertEqual(al.id, data['id'])
                self.assertEqual(
                    al.abspath,
                    self.replacepath(data['path']))
    
    def test12_images(self):
        for data in self.test_data['images']:
            with self.subTest(imageid = data['id']):
                img = self.dk.images[data['id']]
                self.assertEqual(img.id, data['id'])
                self.assertEqual(img.name, data['name'])
                
                img2 = self.dk.images.find(img.abspath)
                self.assertIs(img, img2)
        
        with self.subTest(file = 'not in DB'):
            self.assertIsNone(self.dk.images.find('/does/not/exist'))
    
    def test13_tags(self):
        for data in self.test_data['tags']:
            with self.subTest(tagid = data['id']):
                tag = self.dk.tags[data['name']]
                self.assertEqual(tag.id, data['id'])
                self.assertEqual(tag.pid, data['pid'])
                
                tag2 = self.dk.tags[tag.id]
                self.assertIs(tag, tag2)


class CheckComments:
    """Mixin with tests for comments"""
    
    # Title helper methods
    def _set_titles(self, img, titles):
        old_titles = {}
        for lang, newtitle in titles.items():
            if lang == '_default':
                old_titles[lang] = img.title.get()
                img.title = newtitle
            else:
                old_titles[lang] = img.title.get(lang)
                img.title.set(newtitle, language = lang)
        return old_titles
    
    def _set_captions(self, img, captions):
        old_captions = {}
        for lang, newdata in captions.items():
            if lang == '_default':
                old_captions[lang] = img.caption.get()
                img.caption = newdata
            else:
                old_captions[lang] = {}
                for author, newcaption in newdata.items():
                    old_captions[lang][author] = img.caption.get(lang, author)
                    img.caption.set(newcaption, language = lang, author = author)
        return old_captions
    
    def _check_titles(self, img, titles):
        for lang, newtitle in titles.items():
            if lang == '_default':
                self.assertEqual(img.title.get(), newtitle)
            else:
                self.assertEqual(img.title.get(lang), newtitle)
    
    def _check_captions(self, img, captions):
        for lang, newdata in captions.items():
            if lang == '_default':
                self.assertEqual(img.caption.get(), newdata)
            else:
                for author, newcaption in newdata.items():
                    self.assertEqual(img.caption.get(lang, author), newcaption)
    
    def test10_create_comments(self):
        # Set new values
        old_comments = {}
        for data in self.test_data['images']:
            if 'comments' in data:
                with self.subTest(imageid = data['id']):
                    img = self.dk.images[data['id']]
                    self.assertEqual(img.id, data['id'])
                    old_comments[img.id] = {}
                    
                    if 'title' in data['comments']:
                        old_comments[img.id]['title'] = self._set_titles(
                            img,
                            data['comments']['title']
                        )
                    
                    if 'caption' in data['comments']:
                        old_comments[img.id]['caption'] = self._set_captions(
                            img,
                            data['comments']['caption']
                        )
        self.dk.session.commit()
        self.__class__.old_image_comments = old_comments
    
    def test11_verify_comments(self):
        # Check new values
        for data in self.test_data['images']:
            if 'comments' in data:
                with self.subTest(imageid = data['id']):
                    img = self.dk.images[data['id']]
                    self._check_titles(
                            img,
                            data['comments']['title']
                        )
                    if 'caption' in data['comments']:
                        self._check_captions(
                            img,
                            data['comments']['caption']
                        )
    
    def test12_restore_comments(self):
        # Restore old values
        old_comments = self.__class__.old_image_comments
        for id_, comments in old_comments.items():
            with self.subTest(imageid = id_):
                img = self.dk.images[id_]
                self.assertEqual(img.id, id_)
                if 'title' in comments:
                    self._set_titles(img, comments['title'])
                if 'caption' in comments:
                    self._set_captions(img, comments['caption'])
        self.dk.session.commit()
    
    def test13_verify_restored_comments(self):
        # Check old values
        old_comments = self.__class__.old_image_comments
        for id_, comments in old_comments.items():
            with self.subTest(imageid = id_):
                img = self.dk.images[id_]
                self.assertEqual(img.id, id_)
                if 'title' in comments:
                    self._check_titles(img, comments['title'])
                if 'caption' in comments:
                    self._check_captions(img, comments['caption'])


class NewData:
    """Mixin to test adding new objects"""
    
    def test10_defines(self):
        basedir = mkdtemp()
        new_data = {
            'basedir':      basedir,
            'albumroots':   [],
            'albums':       [],
            'images':       [],
            'tags':         [],
        }
        self.__class__.new_data = new_data
    
    def test11_add_roots(self):
        new_data = self.__class__.new_data
        new_root = self.dk.albumRoots.add(
            new_data['basedir'],
            label = 'New AlbumRoot',
        )
        self.dk.session.commit()
        new_data['albumroots'].append({
            '_idx':         len(new_data['albumroots']),
            'id':           new_root.id,
            'label':        'New AlbumRoot',
            'identifier':   new_root.identifier,
            'specificPath': new_root.specificPath,
            'path':         new_data['basedir'],
        })
    
    def test12_verify_roots(self):
        new_data = self.__class__.new_data
        for rootdata in new_data['albumroots']:
            with self.subTest(albumroot = rootdata['_idx']):
                root = self.dk.albumRoots[rootdata['id']]
                self.assertEqual(root.id, rootdata['id'])
                self.assertEqual(root.label, rootdata['label'])
                self.assertEqual(root.status, 0)
                self.assertEqual(root.type, 1)
                self.assertEqual(root.identifier, rootdata['identifier'])
                self.assertEqual(root.specificPath, rootdata['specificPath'])
                self.assertEqual(root.abspath, rootdata['path'])
        
    def test13_add_albums(self):
        new_data = self.__class__.new_data
        root = self.dk.albumRoots[new_data['albumroots'][0]['id']]
        today = datetime.date.today()
        
        for relpath in ['/', '/New_Album']:
            with self.subTest(Album = relpath):
                new_album = self.dk.albums._insert(
                    albumRoot = root.id,
                    relativePath = relpath,
                    date = today,
                    caption = None,
                    collection = None,
                    icon = None
                )
                self.dk.session.commit()
                if relpath == '/':
                    abspath = root.abspath
                else:
                    abspath = os.path.join(root.abspath, relpath.lstrip('/'))
                new_data['albums'].append({
                    '_idx':         len(new_data['albums']),
                    'id':           new_album.id,
                    'albumRoot':    root.id,
                    'relativePath': abspath,
                    'date':         today,
                    'caption':      None,
                    'collection':   None,
                    'icon':         None,
                    'path':         abspath,
                })
    
    def test14_verify_albums(self):
        new_data = self.__class__.new_data
        for albumdata in new_data['albums']:
            with self.subTest(album = albumdata['_idx']):
                album = self.dk.albums[albumdata['id']]
                self.assertEqual(album.id, albumdata['id'])
                self.assertEqual(album.albumRoot, albumdata['albumRoot'])
                self.assertEqual(album.relativePath, albumdata['relativePath'])
                self.assertEqual(album.date, albumdata['date'])
                self.assertEqual(album.caption, albumdata['caption'])
                self.assertEqual(album.collection, albumdata['collection'])
                self.assertEqual(album.icon, albumdata['icon'])
                self.assertEqual(album.abspath, albumdata['path'])
                self.assertIsNone(album.iconImage)
    
    def test15_add_images(self):
        new_data = self.__class__.new_data
        now = datetime.datetime.now()
        new_image = self.dk.images._insert(
            album = new_data['albums'][1]['id'],
            name = 'new_image.jpg',
            status = 1,
            category = 1,
            modificationDate = now,
            fileSize = 249416,
            uniqueHash = 'e5f60a712fc36977a14816727242262b'
        )
        self.dk.session.commit()
        new_data['images'].append({
            '_idx':             len(new_data['images']),
            'id':               new_image.id,
            'album':            new_data['album']['id'],
            'name':             'new_image.jpg',
            'status':           1,
            'category':         1,
            'modificationDate': now,
            'fileSize':         249416,
            'uniqueHash':       'e5f60a712fc36977a14816727242262b',
        })
    
    def test16_verify_images(self):
        new_data = self.__class__.new_data
        for imgdata in new_data['images']:
            with self.subTest(image = imgdata['_idx']):
                img = self.dk.images[imgdata['id']]
                self.assertEqual(img.id, imgdata['id'])
                self.assertEqual(img.name, imgdata['name'])
                self.assertEqual(img.album, imgdata['album'])
                self.assertEqual(img.status, imgdata['status'])
                self.assertEqual(img.category, imgdata['category'])
                self.assertEqual(img.modificationDate, imgdata['modificationDate'])
                self.assertEqual(img.fileSize, imgdata['fileSize'])
                self.assertEqual(img.uniqueHash, imgdata['uniqueHash'])
    
    def test88_remove_new_data(self):
        new_data = self.__class__.new_data
        for img in new_data['images']:
            with self.subTest(image = img['_idx']):
                self.dk.images._delete(id = img['id'])
        for alb in new_data['albums']:
            with self.subTest(album = alb['_idx']):
                self.dk.albums._delete(id = alb['id'])
        for ar in new_data['albumroots']:
            with self.subTest(albumroot = ar['_idx']):
                self.dk.albumRoots._delete(id = ar['id'])
        self.dk.session.commit()
        rmtree(new_data['basedir'])

    def test89_verify_removal(self):
        new_data = self.__class__.new_data
        for img in new_data['images']:
            with self.subTest(image = img['idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.images[img['id']]
        for alb in new_data['albums']:
            with self.subTest(album = alb['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.albums[alb['id']]
        for ar in new_data['albumroots']:
            with self.subTest(albumroot = ar['_idx']):
                self.dk.albumRoots._delete(id = ar['id'])
                with self.assertRaises(NoResultFound):
                    _ = self.dk.albumRoots[ar['id']]

