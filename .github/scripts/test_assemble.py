import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('assemble', Path(__file__).with_name('assemble.py'))
assemble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assemble)


class SitemapDates(unittest.TestCase):
    def test_corrected_article_retains_real_update_day(self):
        article = {'published_at': '2026-10-01T23:00:00+02:00',
                   'updated_at': '2026-10-03T10:00:00Z'}
        self.assertEqual(assemble.article_lastmod(article), '2026-10-03')
        article['updated_at'] = '2026-09-30T10:00:00+02:00'
        self.assertEqual(assemble.article_lastmod(article), '2026-10-01')
        article['updated_at'] = 'not-a-date'
        self.assertEqual(assemble.article_lastmod(article), '2026-10-01')

    def test_window_correction_overrides_archive_without_losing_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'archive').mkdir()
            (root / 'sitemap-legacy.json').write_text(json.dumps({'urls': {'old': '2026-07-01'}}))
            article = {'slug': 'story', 'published_at': '2026-10-01T10:00:00+02:00'}
            (root / 'archive' / '2026-10-01.json').write_text(json.dumps({'articles': [article]}))
            corrected = {**article, 'updated_at': '2026-10-03T10:00:00+02:00'}
            result = dict(assemble._sitemap_urls(directory, [corrected]))
            self.assertEqual(result, {'old': '2026-07-01', 'story': '2026-10-03'})

    def test_corrupt_archive_blocks_incomplete_sitemap(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'archive'
            archive.mkdir()
            (archive / 'broken.json').write_text('{')
            with self.assertRaises(RuntimeError):
                assemble._sitemap_urls(directory, [])


if __name__ == '__main__':
    unittest.main()
