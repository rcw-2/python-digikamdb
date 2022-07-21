import datetime
import os
import re
import logging
from shutil import unpack_archive, rmtree
from tempfile import mkdtemp
from unittest import TestCase, skip

from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound

from digikamdb import Digikam

logging.basicConfig(filename = 'test.log', level = logging.DEBUG)


# Hide DigikamTestBase so unittest doesn't run it
class Wrapper:

    class DigikamTestBase(TestCase):
        
        __abstract__ = True
        
        def replacepath(self, path):
            return path.replace('MYDIR', self.mydir)
        
        def test_albumroots(self):
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
        
        def test_albums(self):
            for al in self.dk.albums:
                with self.subTest(albumid = al.id):
                    self.assertIsInstance(al, self.dk.album_class)
                    self.assertEqual(al.albumRoot, al.root.id)
                    self.assertIn(al, al.root.albums)
                    self.assertEqual(
                        os.path.commonpath([self.mydir, al.abspath]),
                        self.mydir)
        
        def test_albums_access(self):
            for data in self.test_data['albums']:
                with self.subTest(albumid = data['id']):
                    al = self.dk.albums[data['id']]
                    self.assertEqual(al.id, data['id'])
                    self.assertEqual(
                        al.abspath,
                        self.replacepath(data['path']))
        
        def test_images(self):
            for img in self.dk.images:
                with self.subTest(imageid = img.id):
                    self.assertIsInstance(img, self.dk.image_class)
                    self.assertEqual(img.album, img.albumObj.id)
                    self.assertIn(img, img.albumObj.images)
                    self.assertEqual(
                        os.path.commonpath([self.mydir, img.abspath]),
                        self.mydir)
                    self.assertEqual(img.id, img.information.imageid)
                    if img.category == 1:
                        self.assertEqual(img.id, img.imagemeta.imageid)
                    if img.category == 2:
                        self.assertEqual(img.id, img.videometa.imageid)
                    self.assertEqual(
                        img.abspath,
                        os.path.join(img.albumObj.abspath, img.name))
        
        def test_images_access(self):
            for data in self.test_data['images']:
                with self.subTest(imageid = data['id']):
                    img = self.dk.images[data['id']]
                    self.assertEqual(img.id, data['id'])
                    self.assertEqual(img.name, data['name'])
                    
                    img2 = self.dk.images.find(img.abspath)
                    self.assertIs(img, img2)
            
            with self.subTest(file = 'not in DB'):
                self.assertIsNone(self.dk.images.find('/does/not/exist'))
        
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
        
        def test_images_comments_1(self):
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
        
        def test_images_comments_2(self):
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
        
        def test_images_comments_3(self):
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
        
        def test_images_comments_4(self):
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
        
        def test_tags(self):
            for tag in self.dk.tags:
                with self.subTest(tagid = tag.id):
                    self.assertIsInstance(tag, self.dk.tag_class)
                    if tag.parent:
                        self.assertIn(tag, tag.parent.children)
                    for ch in tag.children:
                        self.assertEqual(tag.id, ch.pid)
                        self.assertIs(tag, ch.parent)
        
        def test_tags_access(self):
            for data in self.test_data['tags']:
                with self.subTest(tagid = data['id']):
                    tag = self.dk.tags[data['name']]
                    self.assertEqual(tag.id, data['id'])
                    self.assertEqual(tag.pid, data['pid'])
                    
                    tag2 = self.dk.tags[tag.id]
                    self.assertIs(tag, tag2)
        
        def test_tags_internal(self):
            internal = self.dk.tags['_Digikam_Internal_Tags_']
            self.assertEqual(internal.id, 1)
            for tag in internal.children:
                with self.subTest(internal_tag = tag.name):
                    self.assertIn('internalTag', tag.properties)
        
        @skip
        def test_imagetags(self):
            pass
        
        # This only works on Linux
        def _get_albumroot_data(self, path):
            mountpoints = {}
            with open('/proc/mounts', 'r') as mt:
                for line in mt.readlines():
                    dev, dir, fstype, options = line.strip().split(maxsplit=3)
                    # Resolve /dev/root for some installations
                    if dev == '/dev/root':
                        st1 = os.stat(dev)
                        for f in os.scandir('/dev'):
                            if not re.match(r'/dev/sd'):
                                continue
                            st2 = f.stat()
                            if st1.st_dev == st2.st_dev:
                                dev = f.name
                                break
                    mountpoints[dir] = dev
            
            uuids = {}
            for f in os.scandir('/dev/disk/by-uuid'):
                if f.is_symlink():
                    uuids[os.path.realpath(f.path)] = f.name
            mpt = os.path.realpath(path)
            while True:
                while not os.path.ismount(mpt):
                    mpt = os.path.dirname(mpt)
                if mpt in mountpoints:
                    dev = mountpoints[mpt]
                    if dev in uuids:
                        return (
                            'volumeid:?uuid=' + uuids[dev],
                            '/' + os.path.relpath(path, mpt).rstrip('.')
                        )
                if mpt == '/': break
            
            return None
        
        def test_new_data_A(self):
            basedir = mkdtemp()
            new_data = {
                'basedir':  basedir
            }
            
            ident, spath = self._get_albumroot_data(basedir)
            new_root = self.dk.albumRoots.insert(
                label = 'New AlbumRoot',
                status = 0,
                type = 1,
                identifier = ident,
                specificPath = spath
            )
            self.dk.session.commit()
            new_data['albumroot'] = {
                'id':           new_root.id,
                'label':        'New AlbumRoot',
                'identifier':   ident,
                'specificPath': spath,
                'path':         new_data['basedir'],
            }
            
            self.__class__.new_data = new_data
        
        def test_new_data_B(self):
            new_data = self.__class__.new_data
            root = self.dk.albumRoots[new_data['albumroot']['id']]
            self.assertEqual(root.id, new_data['albumroot']['id'])
            self.assertEqual(root.label, new_data['albumroot']['label'])
            self.assertEqual(root.status, 0)
            self.assertEqual(root.type, 1)
            self.assertEqual(root.identifier, new_data['albumroot']['identifier'])
            self.assertEqual(root.specificPath, new_data['albumroot']['specificPath'])
            self.assertEqual(root.abspath, new_data['albumroot']['path'])
            
            today = datetime.date.today()
            new_album = self.dk.albums.insert(
                albumRoot = root.id,
                relativePath = '/New_Album',
                date = today,
                caption = None,
                collection = None,
                icon = None
            )
            self.dk.session.commit()
            new_data['album'] = {
                'id':           new_album.id,
                'albumRoot':    root.id,
                'relativePath': '/New_Album',
                'date':         today,
                'caption':      None,
                'collection':   None,
                'icon':         None,
                'path':         os.path.join(root.abspath, 'New_Album'),
            }
        
        def test_new_data_C(self):
            new_data = self.__class__.new_data
            album = self.dk.albums[new_data['album']['id']]
            self.assertEqual(album.id, new_data['album']['id'])
            self.assertEqual(album.albumRoot, new_data['album']['albumRoot'])
            self.assertEqual(album.relativePath, new_data['album']['relativePath'])
            self.assertEqual(album.date, new_data['album']['date'])
            self.assertEqual(album.caption, new_data['album']['caption'])
            self.assertEqual(album.collection, new_data['album']['collection'])
            self.assertEqual(album.icon, new_data['album']['icon'])
            self.assertEqual(album.abspath, new_data['album']['path'])
            if new_data['album']['icon'] is None:
                self.assertIsNone(album.iconImage)
            else:
                self.assertIsInstance(album.iconImage, self.dk.image_class)
       
        def test_new_data_Y(self):
            new_data = self.__class__.new_data
            self.dk.albums.delete(id = new_data['album']['id'])
            self.dk.albumRoots.delete(id = new_data['albumroot']['id'])
            self.dk.session.commit()

        def test_new_data_Z(self):
            new_data = self.__class__.new_data
            with self.assertRaises(NoResultFound):
                _ = self.dk.albums[new_data['album']['id']]
            with self.assertRaises(NoResultFound):
                _ = self.dk.albumRoots[new_data['albumroot']['id']]


class DigikamSQLiteTest(Wrapper.DigikamTestBase):
    
    @classmethod
    def setUpClass(cls):
        archive = os.path.join(
            os.path.dirname(__file__),
            'data',
            'testdb.tar.gz')
        cls.mydir = mkdtemp()
        unpack_archive(archive, cls.mydir)
        cls.root_override = {
            'ids':      {1: 'TEST'},
            'paths':    {1: cls.mydir}
        }
        cls.test_data = {
            'albumroots': [{
                'id': 1,
                'label': 'Pictures',
                'mountpoint': 'TEST',
                'path': 'MYDIR'}],
            'albums': [{'id': 1, 'path': 'MYDIR'}],
            'images': [{
                'id': 1,
                'name': '20210806_165143.jpg',
                'comments': {
                    'title': {
                        '_default':     'New title for image 1',
                        'de-DE':        'Die Destillerie',
                    },
                    'caption': {
                        '_default':     'New caption for image 1',
                        'de-DE': {
                            'RCW':      'Ein Kommentar von RCW',
                        },
                    },
                },
            }],
            'tags': [{'id': 22, 'pid': 0, 'name': 'France'}]
        }
    
    @classmethod
    def tearDownClass(cls):
        rmtree(cls.mydir)
    
    def setUp(self):
        dbfile = os.path.join(self.mydir, 'digikam4.db')
        db = create_engine('sqlite:///' + dbfile)
        self.dk = Digikam(db, root_override = self.root_override)
    
    def tearDown(self):
        self.dk.destroy()
        
    def test_sqlite(self):
        self.assertFalse(self.dk.is_mysql)
        with self.assertRaises(NoResultFound):
            _ = self.dk.tags._root


class DigikamMySQLTest(Wrapper.DigikamTestBase):
    
    @classmethod
    def setUpClass(cls):
        import mysql_data
        cls.mydir = mkdtemp()
        cls.mysql_db = mysql_data.mysql_db
        cls.root_override = mysql_data.root_override or {
            'ids': {
                'volumeid:?uuid=722b9c6f-0249-4fc2-8acf-d9926bb2995a': 'MYDIR',
            },
        }
        
        # Test data
        cls.test_data = mysql_data.test_data or {
            'albumroots': [{
                'id': 1,
                'label': 'Pictures',
                'mountpoint': 'MYDIR',
                'path': 'MYDIR/home/digikam2/Pictures'}],
            'albums': [{'id': 1, 'path': 'MYDIR/home/digikam2/Pictures'}],
            'images': [{
                'id': 1,
                'name': '20210806_165143.jpg',
                'comments': {
                    'title': {
                        '_default':     'New title for image 1',
                        'de-DE':        'Die Destillerie',
                    },
                    'caption': {
                        '_default':     'New caption for image 1',
                        'de-DE': {
                            'RCW':      'Ein Kommentar von RCW',
                        },
                    },
                },
            }],
            'tags': [{'id': 22, 'pid': 0, 'name': 'Normandy'}]
        }
    
    @classmethod
    def tearDownClass(cls):
        rmtree(cls.mydir)
    
    def setUp(self):
        db = create_engine(self.mysql_db)

        root_override = {}
        for group in ['ids', 'paths']:
            if group in self.root_override:
                root_override[group] = {}
                for key, value in self.root_override[group].items():
                    root_override[group][key] = self.replacepath(value)
        self.dk = Digikam(db, root_override = root_override)
    
    def tearDown(self):
        self.dk.destroy()
        
    def test_mysql(self):
        self.assertTrue(self.dk.is_mysql)
        root = self.dk.tags._root
        self.assertEqual(root.id, 0)
        self.assertEqual(root.pid, -1)
        self.assertIsNone(root.parent)
        self.assertEqual(root.name, '_Digikam_root_tag_')
    
