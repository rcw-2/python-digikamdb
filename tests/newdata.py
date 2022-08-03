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

from digikamdb import DigikamDataIntegrityError, DigikamFileError


log = logging.getLogger(__name__)


class NewDataRoot:
    """Mixin to test adding new album roots"""
    
    def test00_defines(self):
        basedir = mkdtemp()
        new_data = {
            'basedir':      basedir,
            'albumroots':   [],
            'albums':       [],
            'images':       [],
            'tags':         [],
            'settings':     [],
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
        self._add_root(
            new_data['albumroots'],
            mkdtemp(),
            'Album Root 2'
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


class NewDataRootOverride(NewDataRoot):
    """Mixin for path override"""
    
    def test11_override(self):
        new_data = self.__class__.new_data
        rootdata = new_data['albumroots'][2]
        self.__class__.root_override = {
            'paths': {
                (rootdata['identifier'] + rootdata['specificPath']).rstrip('/'):
                    rootdata['path']
            }
        }


class NewData(NewDataRoot):
    """Mixin to test adding new objects"""
    
    def test11_change_roots(self):
        new_data = self.__class__.new_data
        rootdata = new_data['albumroots'][0]
        root = self.dk.albumRoots[rootdata['id']]
        self.assertEqual(root.id, rootdata['id'])
        self.assertEqual(root.label, rootdata['label'])
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
    
    def test12_nested_roots(self):
        new_data = self.__class__.new_data
        path = new_data['albumroots'][0]['path']
        with self.assertRaises(DigikamFileError):
            _ = self.dk.albumRoots.add(path)
        with self.assertRaises(DigikamFileError):
            _ = self.dk.albumRoots.add(os.path.join(path, 'test'))
        with self.assertRaises(DigikamFileError):
            _ = self.dk.albumRoots.add(os.path.dirname(path))
    
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
    
    def test28_verify_albums(self):
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
                'position':         None,
            })
        return new_image
    
    def _check_image(self, imgdata):
        img = self.dk.images[imgdata['id']]
        self.assertEqual(img.id, imgdata['id'])
        self.assertEqual(img.name, imgdata['name'])
        self.assertEqual(img.album, imgdata['album'])
        self.assertEqual(img.status, imgdata['status'])
        self.assertEqual(img.category, imgdata['category'])
        self.assertEqual(img.modificationDate, imgdata['modificationDate'])
        self.assertEqual(img.fileSize, imgdata['fileSize'])
        self.assertEqual(img.uniqueHash, imgdata['uniqueHash'])
        if 'position' in imgdata:
            self.assertEqual(img.position, imgdata['position'])
        if 'copyright' in imgdata:
            for k, v in imgdata['copyright'].items():
                self.assertEqual(img.copyright[k], v)
            for k, v in img.copyright.items():
                self.assertEqual(imgdata['copyright'][k], v)
    
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
        img1a = self.dk.images.find(path)[0]
        self.assertEqual(img1.id, img1a.id)
        self.assertIs(img1, img1a)
        _ = self._add_image(
            new_data['images'],
            album.id,
            'new_image2.jpg',
            now,
            618645,
            '64d4a2295ab3f19e02dd7921ab642561'
        )
    
    def _set_image_position(self, imgdata, pos, datapos=None):
        self._check_image(imgdata)
        img = self.dk.images[imgdata['id']]
        img.position = pos
        self.dk.session.commit()
        if datapos is None:
            datapos = pos
        if isinstance(pos, tuple) and len(pos) == 2:
            datapos = (datapos[0], datapos[1], None)
        imgdata['position'] = datapos
        
    def test31_image_position(self):
        new_data = self.__class__.new_data
        with self.subTest(image = 0):
            imgdata = new_data['images'][0]
            self._set_image_position(
                imgdata,
                (50.10961004586001, 8.702938349511566)
            )
        with self.subTest(image = 1):
            imgdata = new_data['images'][1]
            self._set_image_position(
                imgdata,
                (50.10961004586001, 8.702938349511566, 612)
            )
    
    def test32_change_image_position(self):
        new_data = self.__class__.new_data
        imgdata = new_data['images'][0]
        self.assertEqual(
            imgdata['position'],
            (50.10961004586001, 8.702938349511566, None)
        )
        self._set_image_position(
            imgdata,
            ("50.11088572429458N", "8.668430363718421E", 721),
            (50.11088572429458, 8.668430363718421, 721)
        )
    
    def test33_remove_image_position(self):
        new_data = self.__class__.new_data
        imgdata = new_data['images'][0]
        self.assertEqual(
            imgdata['position'],
            (50.11088572429458, 8.668430363718421, 721)
        )
        self._set_image_position(imgdata, None)
    
    def test34_image_copyright(self):
        new_data = self.__class__.new_data
        imgdata = new_data['images'][0]
        img = self.dk.images[imgdata['id']]
        self.assertNotIn('creator', img.copyright)
        self.assertNotIn('copyrightNotice', img.copyright)
        img.copyright['creator'] = 'RCW'
        img.copyright['copyrightNotice'] = ('(c) 2022 RCW', 'x-default')
        self.dk.session.commit()
        imgdata['copyright'] = {
            'creator':          'RCW',
            'copyrightNotice':  ('(c) 2022 RCW', 'x-default'),
        }
    
    def test35_find_images(self):
        new_data = self.__class__.new_data
        album = self.dk.albums[new_data['albums'][1]['id']]
        images = self.dk.images.find(album.abspath)
        self.assertEqual(len(images), 2)
        for i in images:
            self.assertIsInstance(i, self.dk.images.Class)
        ids = [i.id for i in images]
        for idx in [0, 1]:
            id_ = new_data['images'][idx]['id']
            self.assertIn(id_, ids)
    
    def test38_verify_images(self):
        new_data = self.__class__.new_data
        for imgdata in new_data['images']:
            with self.subTest(image = imgdata['_idx']):
                self._check_image(imgdata)
    
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
        
        if isinstance(parent, self.dk.tags.Class):
            parent = parent.id
        
        if icon is None:
            iconkde = None
        elif isinstance(icon, self.dk.images.Class):
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
    
    def test41_change_tags(self):
        new_data = self.__class__.new_data
        tagdata = new_data['tags'][0]
        tag = self.dk.tags[tagdata['id']]
        self.assertEqual(tag.name, tagdata['name'])
        tag.name += 'a'
        self.dk.session.commit()
        tagdata['name'] += 'a'
    
    def test42_tag_properties(self):
        new_data = self.__class__.new_data
        tagdata = new_data['tags'][0]
        tag = self.dk.tags[tagdata['id']]
        tag.properties['tagKeyboardShortcut'] = 'Alt+Shift+S'
        self.dk.session.commit()
        tagdata['properties'] = {
            'tagKeyboardShortcut':  'Alt+Shift+S'
        }
    
    def test43_change_tag_properties(self):
        new_data = self.__class__.new_data
        tagdata = new_data['tags'][0]
        tag = self.dk.tags[tagdata['id']]
        self.assertEqual(tagdata['properties']['tagKeyboardShortcut'], 'Alt+Shift+S')
        self.assertEqual(tag.properties['tagKeyboardShortcut'], 'Alt+Shift+S')
        tag.properties['tagKeyboardShortcut'] = 'Alt+Shift+A'
        self.dk.session.commit()
        tagdata['properties']['tagKeyboardShortcut'] = 'Alt+Shift+A'
    
    def test48_verify_tags(self):
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
    
    def test49_verify_tag_properties(self):
        new_data = self.__class__.new_data
        for tagdata in new_data['tags']:
            if 'properties' in tagdata:
                with self.subTest(tag = tagdata['_idx']):
                    tag = self.dk.tags[tagdata['id']]
                    for prop, value in tagdata['properties'].items():
                        self.assertEqual(tag.properties[prop], value)
    
    def test50_add_settings(self):
        new_data = self.__class__.new_data
        self.assertTrue('databaseUserImageFormats' not in self.dk.settings)
        self.dk.settings['databaseUserImageFormats'] = '-cr2'
        self.dk.session.commit()
        new_data['settings'].append({
            'keyword':  'databaseUserImageFormats',
            'value':    '-cr2',
        })
    
    def test51_change_settings(self):
        new_data = self.__class__.new_data
        setdata = new_data['settings'][0]
        self.assertEqual(self.dk.settings[setdata['keyword']], setdata['value'])
        self.dk.settings[setdata['keyword']] += ';-xcf'
        self.dk.session.commit()
        setdata['value'] += ';-xcf'
    
    def test58_verify_settings(self):
        new_data = self.__class__.new_data
        for setdata in new_data['settings']:
            self.assertEqual(self.dk.settings[setdata['keyword']], setdata['value'])
    
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
        for st in new_data['settings']:
            with self.subTest(setting = st['keyword']):
                self.dk.settings._delete(keyword = st['keyword'])
        self.dk.session.commit()
    
    def test95_verify_removal(self):
        new_data = self.__class__.new_data
        for tag in new_data['tags']:
            with self.subTest(tag = tag['_idx']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.tags[tag['id']]
                self.assertFalse(self.dk.tags._select(id = tag['id']).all())
        with self.subTest(msg = 'tags sanity check'):
            self.dk.tags.check()
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
        for st in new_data['settings']:
            with self.subTest(setting = st['keyword']):
                with self.assertRaises(NoResultFound):
                    _ = self.dk.settings[st['keyword']]

