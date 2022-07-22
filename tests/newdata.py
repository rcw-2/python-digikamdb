# Test base

import datetime
import logging
import os
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, skip     # noqa: F401
from typing import List

from sqlalchemy.exc import NoResultFound


log = logging.getLogger(__name__)


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
    
    def _add_root(
        self,
        data: List,
        basedir: str,
        label: str,
        check_dir: bool = True,
        use_uuid: bool = True,
    ) -> None:
        """Add albumroot"""
        new_root = self.dk.albumRoots.add(
            basedir,
            label,
            check_dir = check_dir,
            use_uuid = use_uuid,
        )
        self.dk.session.commit()
        data.append({
            '_idx':         len(data),
            'id':           new_root.id,
            'label':        label,
            'identifier':   new_root.identifier,
            'specificPath': new_root.specificPath,
            'path':         basedir,
        })
            
    def test11_add_roots(self):
        new_data = self.__class__.new_data
        self._add_root(
            new_data['albumroots'],
            mkdtemp(),
            'Album Root 0'
        )
        self._add_root(
            new_data['albumroots'],
            mkdtemp(),
            'Album Root 1',
            use_uuid = False
        )
    
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
                    'relativePath': relpath,
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
        album = self.dk.albums[new_data['albums'][1]['id']]
        now = datetime.datetime.now().replace(microsecond = 0)
        new_image = self.dk.images._insert(
            album = album.id,
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
            'album':            album.id,
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
                rmtree(self.dk.albumRoots[ar['id']].abspath)
                self.dk.albumRoots._delete(id = ar['id'])
        self.dk.session.commit()

    def test89_verify_removal(self):
        new_data = self.__class__.new_data
        for img in new_data['images']:
            with self.subTest(image = img['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.images[img['id']]
        for alb in new_data['albums']:
            with self.subTest(album = alb['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.albums[alb['id']]
        for ar in new_data['albumroots']:
            with self.subTest(albumroot = ar['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.albumRoots[ar['id']]

