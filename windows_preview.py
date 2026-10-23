"""Render locally, then open the MP4 in the Windows default player."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys

import pipeline


def find_ffmpeg():
    if shutil.which('ffmpeg') and shutil.which('ffprobe'):
        return
    packages = Path(os.environ.get('LOCALAPPDATA', ''))/'Microsoft'/'WinGet'/'Packages'
    for exe in packages.glob('Gyan.FFmpeg*/**/ffmpeg.exe'):
        if exe.with_name('ffprobe.exe').exists():
            os.environ['PATH'] = str(exe.parent) + os.pathsep + os.environ.get('PATH','')
            return
    raise RuntimeError('FFmpeg not found. Run setup-windows.cmd first, then reopen this window.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(Path.home()/'OneDrive'/'Video'))
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    base = Path(args.output).expanduser().resolve()
    if not base.is_dir():
        raise RuntimeError(f'The OneDrive folder does not exist: {base}. Confirm its location first.')
    find_ffmpeg()
    # A new directory for every run protects previous versions.
    output = base/('Preview-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    board = json.loads((Path(__file__).parent/'examples'/'storyboard.json').read_text(encoding='utf-8'))
    video = pipeline.demo_video(board, output)
    print(f'Video saved: {video}', flush=True)
    print('Silent 40-second layout preview. Notion and AI were not called.', flush=True)
    print('OneDrive uploads it only if the desktop sync client is running and signed in.', flush=True)
    if sys.platform == 'win32' and not args.no_open:
        os.startfile(str(video))


if __name__ == '__main__':
    main()
