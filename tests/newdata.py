# Test base

import datetime
import logging
import os
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase, skip     # noqa: F401
from typing import Any, List, Optional

from sqlalchemy.exc import NoResultFound

from digikamdb import DigikamDataIntegrityError


log = logging.getLogger(__name__)


class NewData:
    """Mixin to test adding new objects"""
    
    def test00_defines(self):
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
    ) -> 'AlbumRoot':                                       # noqa: F821
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
        return new_root
            
    def test10_add_roots(self):
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
    
    def test11_change_roots(self):
        new_data = self.__class__.new_data
        rootdata = new_data['albumroots'][0]
        root = self.dk.albumRoots[rootdata['id']]
        self.assertEqual(root.id, rootdata['id'])
        self.assertEqual(root.identifier, rootdata['identifier'])
        self.assertEqual(root.specificPath, rootdata['specificPath'])
        self.assertEqual(root.abspath, rootdata['path'])
        root.identifier = 'volumeid:?path=' + rootdata['path']
        root.specificPath = '/'
        self.dk.session.commit()
        rootdata.update(
            identifier = 'volumeid:?path=' + rootdata['path'],
            specificPath = '/',
        )
    
    def test15_verify_roots(self):
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
                self.assertTrue(os.path.isdir(root.abspath))
    
    def _add_album(
        self,
        data: List,
        albumRoot: int,
        relativePath: str,
        date: datetime
    ) -> 'Album':                                           # noqa: F821
        with self.subTest(Album = relativePath):
            new_album = self.dk.albums._insert(
                albumRoot = albumRoot,
                relativePath = relativePath,
                date = date,
                caption = None,
                collection = None,
                icon = None
            )
            self.dk.session.commit()
            root = self.dk.albumRoots[albumRoot]
            if relativePath == '/':
                abspath = root.abspath
            else:
                abspath = os.path.join(root.abspath, relativePath.lstrip('/'))
            data.append({
                '_idx':         len(data),
                'id':           new_album.id,
                'albumRoot':    albumRoot,
                'relativePath': relativePath,
                'date':         date,
                'caption':      None,
                'collection':   None,
                'icon':         None,
                'path':         abspath,
            })
        return new_album
    
    def test20_add_albums(self):
        new_data = self.__class__.new_data
        root1 = self.dk.albumRoots[new_data['albumroots'][0]['id']]
        root2 = self.dk.albumRoots[new_data['albumroots'][1]['id']]
        today = datetime.date.today()
        
        os.mkdir(os.path.join(root1.abspath, 'New_Album'))
        self._add_album(new_data['albums'], root1.id, '/', today)
        self._add_album(new_data['albums'], root1.id, '/New_Album', today)
        self._add_album(new_data['albums'], root2.id, '/', today)
    
    def test25_verify_albums(self):
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
    
    def _add_image(
        self,
        data: List,
        album: int,
        name: str,
        modificationDate: datetime,
        fileSize: int,
        uniqueHash: str,
    ) -> 'Image':                                           # noqa: F821
        with self.subTest(image = name):
            new_image = self.dk.images._insert(
                album = album,
                name = name,
                status = 1,
                category = 1,
                modificationDate = modificationDate,
                fileSize = fileSize,
                uniqueHash = uniqueHash
            )
            self.dk.session.commit()
            data.append({
                '_idx':             len(data),
                'id':               new_image.id,
                'album':            album,
                'name':             name,
                'status':           1,
                'category':         1,
                'modificationDate': modificationDate,
                'fileSize':         fileSize,
                'uniqueHash':       uniqueHash,
            })
        return new_image
    
    def test30_add_images(self):
        new_data = self.__class__.new_data
        album = self.dk.albums[new_data['albums'][1]['id']]
        now = datetime.datetime.now().replace(microsecond = 0)
        path = os.path.join(album.abspath, 'new_image.jpg')
        Path(path).touch()
        img1 = self._add_image(
            new_data['images'],
            album.id,
            'new_image.jpg',
            now,
            638843,
            '54b4f8875a9885643582a31edf933822'
        )
        img2 = self.dk.images.find(path)
        self.assertEqual(img1.id, img2.id)
        self.assertIs(img1, img2)
    
    def test31_image_position(self):
        new_data = self.__class__.new_data
        imgdata = new_data['images'][0]
        img = self.dk.images[imgdata['id']]
        img.position = (50.10961004586001, 8.702938349511566)
        self.dk.session.commit()
        imgdata['position'] = (50.10961004586001, 8.702938349511566, None)
    
    def test32_change_image_position(self):
        new_data = self.__class__.new_data
        imgdata = new_data['images'][0]
        img = self.dk.images[imgdata['id']]
        self.assertEqual(
            imgdata['position'],
            (50.10961004586001, 8.702938349511566, None)
        )
        self.assertEqual(img.position, imgdata['position'])
        img.position = (50.11088572429458, 8.668430363718421)
        self.dk.session.commit()
        imgdata['position'] = (50.11088572429458, 8.668430363718421, None)
    
    def test35_verify_images(self):
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
    
    def test36_verify_image_position(self):
        new_data = self.__class__.new_data
        for imgdata in new_data['images']:
            if 'position' in imgdata:
                with self.subTest(image = imgdata['_idx']):
                    img = self.dk.images[imgdata['id']]
                    self.assertEqual(img.position, imgdata['position'])
    
    def _add_tag(
        self,
        data: List,
        name: str,
        parent: Any,
        icon: Optional[Any] = None
    ) -> 'Tag':                                             # noqa: F821
        """Adds a tag and saves data"""
        tag = self.dk.tags.add(name, parent, icon)
        self.dk.session.commit()
        
        if isinstance(parent, self.dk.tag_class):
            parent = parent.id
        
        if icon is None:
            iconkde = None
        elif isinstance(icon, self.dk.image_class):
            icon = icon.id
            iconkde = None
        elif isinstance(icon, int):
            iconkde = None
        elif isinstance(icon, str):
            iconkde = icon
            icon = None
        
        data.append({
            '_idx':     len(data),
            'id':       tag.id,
            'pid':      parent,
            'name':     name,
            'icon':     icon,
            'iconkde':  iconkde,
        })
        
        return tag
    
    def test40_add_tags(self):
        new_data = self.__class__.new_data
        tag1 = self._add_tag(
            new_data['tags'],
            'New Tag 1',
            0
        )
        tag2 = self._add_tag(
            new_data['tags'],
            'New Tag 2',
            tag1,
            'applications-development'
        )
        imgid = new_data['images'][0]['id']
        tag3 = self._add_tag(                               # noqa: F841
            new_data['tags'],
            'New Tag 3',
            tag2.id,
            imgid
        )
        tag4 = self._add_tag(                               # noqa: F841
            new_data['tags'],
            'New Tag 4',
            tag2,
            self.dk.images[imgid]
        )
    
    def test41_tag_properties(self):
        new_data = self.__class__.new_data
        tagdata = new_data['tags'][0]
        tag = self.dk.tags[tagdata['id']]
        tag.properties['tagKeyboardShortcut'] = 'Alt+Shift+S'
        self.dk.session.commit()
        tagdata['properties'] = {
            'tagKeyboardShortcut':  'Alt+Shift+S'
        }
    
    def test42_change_tag_properties(self):
        new_data = self.__class__.new_data
        tagdata = new_data['tags'][0]
        tag = self.dk.tags[tagdata['id']]
        self.assertEqual(tagdata['properties']['tagKeyboardShortcut'], 'Alt+Shift+S')
        self.assertEqual(tag.properties['tagKeyboardShortcut'], 'Alt+Shift+S')
        tag.properties['tagKeyboardShortcut'] = 'Alt+Shift+A'
        self.dk.session.commit()
        tagdata['properties']['tagKeyboardShortcut'] = 'Alt+Shift+A'
    
    def test45_verify_tags(self):
        with self.subTest(msg = 'data integrity check'):
            try:
                self.dk.tags.check()
            except DigikamDataIntegrityError:
                self.fail('Tags table inconsistent')
        new_data = self.__class__.new_data
        for tagdata in new_data['tags']:
            with self.subTest(tag = tagdata['_idx']):
                tag = self.dk.tags[tagdata['id']]
                self.assertEqual(tag.id, tagdata['id'])
                self.assertEqual(tag.pid, tagdata['pid'])
                self.assertEqual(tag.name, tagdata['name'])
                self.assertEqual(tag.icon, tagdata['icon'])
                self.assertEqual(tag.iconkde, tagdata['iconkde'])
    
    def test46_verify_tag_properties(self):
        new_data = self.__class__.new_data
        for tagdata in new_data['tags']:
            if 'properties' in tagdata:
                with self.subTest(tag = tagdata['_idx']):
                    tag = self.dk.tags[tagdata['id']]
                    for prop, value in tagdata['properties'].items():
                        self.assertEqual(tag.properties[prop], value)
    
    def test90_remove_new_data(self):
        new_data = self.__class__.new_data
        for tag in new_data['tags']:
            with self.subTest(tag = tag['_idx']):
                self.dk.tags.remove(tag['id'])
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
    
    def test95_verify_removal(self):
        new_data = self.__class__.new_data
        for tag in new_data['tags']:
            with self.subTest(tag = tag['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.tags[tag['id']]
                self.assertFalse(self.dk.tags._select(id = tag['id']).all())
        for img in new_data['images']:
            with self.subTest(image = img['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.images[img['id']]
                self.assertFalse(self.dk.images._select(id = img['id']).all())
        for alb in new_data['albums']:
            with self.subTest(album = alb['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.albums[alb['id']]
                self.assertFalse(self.dk.albums._select(id = alb['id']).all())
        for ar in new_data['albumroots']:
            with self.subTest(albumroot = ar['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.albumRoots[ar['id']]
                self.assertFalse(self.dk.albumRoots._select(id = ar['id']).all())

