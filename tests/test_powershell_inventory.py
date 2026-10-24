"""Run with PWSH pointing to a PowerShell executable. Uses temporary fixtures only."""
import csv
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

PWSH = os.environ.get('PWSH')
SCRIPT = Path(__file__).resolve().parents[1]/'inventory-windows.ps1'

@unittest.skipUnless(PWSH, 'Set PWSH for the actual PowerShell integration tests')
class PowerShellInventoryTests(unittest.TestCase):
    def execute(self, source, report):
        return subprocess.run([PWSH,'-NoLogo','-NoProfile','-File',str(SCRIPT),
            '-Source',str(source),'-Output',str(report),'-NoOpen'],capture_output=True,text=True)

    def test_read_only_report_and_category_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir()
            for name in ['factory.mp4','Design/a.jpg','Lab/Design/b.png','实验室/测量.jpg','=SUM(1).jpg','notes.txt']:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture')
            before={str(p.relative_to(root)):(p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
            report=Path(tmp)/'report.csv'
            result=self.execute(root,report)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            after={str(p.relative_to(root)):(p.read_bytes(),p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before,after)
            self.assertTrue(report.read_bytes().startswith(b'\xef\xbb\xbf'))
            with report.open(encoding='utf-8-sig',newline='') as stream:
                rows={r['Relative path']:r for r in csv.DictReader(stream)}
            self.assertEqual(len(rows),5)
            self.assertEqual(rows['factory.mp4']['Suggested category'],'To Review')
            self.assertEqual(rows[str(Path('Design/a.jpg'))]['Suggested category'],'Design')
            self.assertEqual(rows[str(Path('Lab/Design/b.png'))]['Suggested category'],'To Review')
            self.assertEqual(rows[str(Path('实验室/测量.jpg'))]['Suggested category'],'Lab')
            self.assertEqual({r['Review status'] for r in rows.values()},{'Needs review'})
            self.assertTrue(rows["'=SUM(1).jpg"]['Name'].startswith("'="))
            original=report.read_bytes()
            result=self.execute(root,report)
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertEqual(report.read_bytes(),original)

    def test_report_inside_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=self.execute(root,root/'report.csv')
            self.assertEqual(result.returncode,1,result.stdout+result.stderr)
            self.assertFalse((root/'report.csv').exists())

    def test_link_skipped_and_incomplete_report_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';root.mkdir()
            outside=Path(tmp)/'outside';outside.mkdir()
            (outside/'private.jpg').write_bytes(b'fixture')
            try: (root/'linked').symlink_to(outside,target_is_directory=True)
            except OSError: self.skipTest('Symbolic links unavailable')
            report=Path(tmp)/'report.csv'
            result=self.execute(root,report)
            self.assertEqual(result.returncode,2,result.stdout+result.stderr)
            with report.open(encoding='utf-8-sig',newline='') as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['Scan status'],'Skipped')
            self.assertNotIn('private.jpg',report.read_text(encoding='utf-8-sig'))

    def test_empty_source_is_not_reported_as_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'empty';root.mkdir()
            result=self.execute(root,Path(tmp)/'report.csv')
            self.assertEqual(result.returncode,2,result.stdout+result.stderr)

if __name__=='__main__': unittest.main()
