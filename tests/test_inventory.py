import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import media_inventory as m


class InventoryTests(unittest.TestCase):
    def test_filename_alone_never_classifies(self):
        self.assertEqual(m.classify(Path('factory-manufacturing-photo.jpg'))[0], 'To Review')
        self.assertEqual(m.classify(Path('Holiday/lab-test.jpg'))[0], 'To Review')

    def test_folder_clues_tentative_and_conflicts_flagged(self):
        category, evidence, reason = m.classify(Path('Manufacturing/assembly/001.jpg'))
        self.assertEqual(category, 'Manufacturing')
        self.assertIn('Folder context only', reason)
        self.assertIn('Manufacturing', evidence)
        self.assertEqual(m.classify(Path('Design/Lab/001.jpg'))[0], 'To Review')
        self.assertEqual(m.classify(Path('实验室/001.jpg'))[0], 'Lab')
        self.assertEqual(m.classify(Path('collaboration/001.jpg'))[0], 'To Review')

    def test_scan_preserves_sources_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'source'
            (root/'Lab').mkdir(parents=True)
            photo = root/'Lab'/'测量.jpg'
            photo.write_bytes(b'photo fixture')
            (root/'factory.mp4').write_bytes(b'video fixture')
            (root/'notes.txt').write_text('unrelated')
            before = {p.relative_to(root): (p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
            report = Path(tmp)/'inventory.csv'
            self.assertEqual(m.create_report(root, report), (2,0))
            after = {p.relative_to(root): (p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before, after)
            data = report.read_bytes()
            with self.assertRaises(FileExistsError):
                m.create_report(root,report)
            self.assertEqual(report.read_bytes(),data)
            with report.open(encoding='utf-8-sig',newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual({r['Review status'] for r in rows}, {'Needs review'})
            self.assertEqual({r['Original path'] for r in rows}, {str(photo),str(root/'factory.mp4')})

    def test_report_inside_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                m.create_report(root,root/'inventory.csv')
            self.assertEqual(list(root.iterdir()),[])

    def test_symlink_target_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source'; root.mkdir()
            outside=Path(tmp)/'outside';outside.mkdir()
            (outside/'secret.jpg').write_bytes(b'fixture')
            try:
                (root/'linked').symlink_to(outside,target_is_directory=True)
            except OSError:
                self.skipTest('Symlinks unavailable')
            rows=list(m.inventory(root))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['Scan status'],'Skipped')
            self.assertNotIn('secret.jpg',str(rows))

    def test_unreadable_directory_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(m.os,'scandir',side_effect=PermissionError('denied')):
                rows=list(m.inventory(root))
            self.assertEqual(rows[0]['Scan status'],'Skipped')
            self.assertIn('denied',rows[0]['Review reason'])

    def test_csv_formula_protection(self):
        for value in ['=cmd()', '+SUM(1)', '@SUM(1)', '-123']:
            self.assertTrue(m.safe_cell(value).startswith("'"))
        self.assertEqual(m.safe_cell('D:\\source\\=photo.jpg'), 'D:\\source\\=photo.jpg')


if __name__=='__main__':
    unittest.main()
