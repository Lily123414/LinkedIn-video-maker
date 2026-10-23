import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import argparse
import pipeline as p

BOARD = json.loads(Path('examples/storyboard.json').read_text())

class WorkflowTests(unittest.TestCase):
    def test_waiting_states_cannot_advance(self):
        for state in ['待脚本审核','待分镜审核','待视频审核','待上传','已交付','视频已通过']:
            self.assertNotIn(state, p.STAGES)

    def test_no_week_does_not_generate_arbitrary_script(self):
        page = {'properties':{'制作状态':{'select':{'name':'待制作'}}}}
        with patch.object(p,'notion',return_value={'results':[page],'has_more':False}), patch.object(p,'ai') as ai:
            p.tick(argparse.Namespace(week='',output='output/test'))
            ai.assert_not_called()

    def test_preview_rejects_invalid_board_and_escapes(self):
        with self.assertRaises(ValueError):
            p.validate_board({'slides':[]})
        board = json.loads(json.dumps(BOARD))
        board['slides'][0]['title'] = '<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as tmp:
            paths = p.previews(board,Path(tmp))
            self.assertEqual(len(paths),10)
            self.assertIn('&lt;script&gt;',paths[0].read_text())
            self.assertNotIn('<script>',paths[0].read_text())

    def test_latest_saved_script_is_used(self):
        def block(n):
            return {'type':'code','code':{'rich_text':[{'plain_text':'VIDEO_PIPELINE:script:'+json.dumps({'narration':n})}]}}
        with patch.object(p,'blocks',return_value=[block('old'),block('approved edit')]):
            self.assertEqual(p.payload('page','script')['narration'],'approved edit')

    @unittest.skipUnless(os.environ.get('RUN_RENDER_TEST') == '1','Opt-in integration render')
    def test_real_sixty_second_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, seconds in [('intro',6),('outro',14)]:
                p.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=c=gray:s=320x180:r=30',
                       '-t',seconds,'-c:v','libx264','-pix_fmt','yuv420p',root/f'{name}.mp4'])
            wav=root/'test.wav'
            p.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','sine=frequency=440:duration=2',wav])
            with patch.object(p,'request',return_value=wav.read_bytes()), patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}):
                final=p.render(BOARD,{'narration':'Test narration'},root/'output',root/'intro.mp4',root/'outro.mp4')
            self.assertLess(abs(p.duration(final)-60),.3)
            self.assertEqual(len(list((root/'output').glob('frame-*.png'))),10)

if __name__=='__main__':
    unittest.main()
