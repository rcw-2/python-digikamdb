# Test base

import logging

from sqlalchemy.exc import NoResultFound                    # noqa: F401


log = logging.getLogger(__name__)


class CheckComments:
    """Mixin with tests for comments"""
    
    # Title helper methods
    def _set_titles(self, img, titles):
        old_titles = {}
        for lang, newtitle in titles.items():
            if lang == '_default':
                old_titles[lang] = img.title
                img.title = newtitle
                log.debug(
                    'Image %d: title %s -> %s',
                    img.id, old_titles[lang], newtitle
                )
            else:
                old_titles[lang] = img.titles[lang]
                img.titles[lang] = newtitle
                log.debug(
                    'Image %d: titles[%s] %s -> %s',
                    img.id, lang, old_titles[lang], newtitle
                )
        return old_titles
    
    def _set_captions(self, img, captions):
        old_captions = {}
        for lang, newdata in captions.items():
            if lang == '_default':
                old_captions[lang] = img.caption
                img.caption = newdata
                log.debug(
                    'Image %d: caption %s -> %s',
                    img.id, old_captions[lang], newdata
                )
            else:
                old_captions[lang] = {}
                for author, newcaption in newdata.items():
                    old_captions[lang][author] = img.captions[(lang, author)]
                    img.captions[(lang, author)] = newcaption
                    if isinstance(newcaption, str):
                        newdata[author] = (newcaption, None)
                log.debug(
                    'Image %d: captions[%s,%s] %s -> %s',
                    img.id, lang, author, old_captions[lang][author], newdata[author]
                )
        return old_captions
    
    def _check_titles(self, img, titles):
        for lang, newtitle in titles.items():
            if lang == '_default':
                self.assertEqual(img.title, newtitle)
            else:
                self.assertEqual(img.titles[lang], newtitle)
    
    def _check_captions(self, img, captions):
        for lang, refdata in captions.items():
            if lang == '_default':
                self.assertEqual(img.caption, refdata)
            else:
                for author, refcaption in refdata.items():
                    self.assertEqual(img.captions[(lang, author)], refcaption)
    
    def test10_create_comments(self):
        # Set new values
        old_comments = {}
        for data in self.test_comments:
            with self.subTest(imageid = data['id']):
                img = self.dk.images[data['id']]
                self.assertEqual(img.id, data['id'])
                old_comments[img.id] = {}
                
                if 'title' in data:
                    old_comments[img.id]['title'] = self._set_titles(
                        img,
                        data['title'],
                    )
                
                if 'caption' in data:
                    old_comments[img.id]['caption'] = self._set_captions(
                        img,
                        data['caption'],
                    )
        self.dk.session.commit()
        self.__class__.old_image_comments = old_comments
    
    def test20_verify_comments(self):
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
    
    def test30_restore_comments(self):
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
    
    def test40_verify_restored_comments(self):
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


