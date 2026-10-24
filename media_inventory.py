"""Read-only media metadata inventory. Writes one new report outside the source."""
import argparse
import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import stat
import sys

PHOTOS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.tif', '.tiff', '.bmp', '.gif', '.dng', '.cr2', '.cr3', '.nef', '.arw', '.avif'}
VIDEOS = {'.mp4', '.mov', '.m4v', '.avi', '.mkv', '.mts', '.m2ts', '.wmv', '.webm', '.mpg', '.mpeg', '.3gp'}
RULES = {
    'Design': ('design', 'cad', 'drawings', '设计', '图纸'),
    'Prototyping': ('prototype', 'prototypes', 'prototyping', '试制', '样机', '原型'),
    'Lab': ('lab', 'laboratory', 'testing', 'test lab', '实验室', '测试', '检测'),
    'Manufacturing': ('manufacturing', 'production', 'assembly', 'factory', '生产', '制造', '装配', '工厂'),
}
COLUMNS = ['Name', 'Original path', 'Relative path', 'Original folder', 'File type',
           'Extension', 'Size bytes', 'Modified UTC', 'Suggested category', 'Evidence',
           'Review status', 'Review reason', 'Visual inspection', 'Scan status']


def matches(value, keyword):
    if keyword.isascii():
        return re.search(r'(?<![a-z0-9])' + re.escape(keyword) + r'(?![a-z0-9])', value.lower()) is not None
    return keyword in value


def classify(relative):
    # Filename is intentionally excluded from classification input.
    folders = relative.parts[:-1]
    hits = {category: [folder for folder in folders if any(matches(folder, key) for key in keys)]
            for category, keys in RULES.items()}
    hits = {category: folders for category, folders in hits.items() if folders}
    evidence = '; '.join(f'{category}: folder "{folder}"' for category, folders in hits.items() for folder in folders)
    if len(hits) == 1:
        return next(iter(hits)), evidence, 'Folder context only; content has not been inspected. Confirm manually.'
    if hits:
        return 'To Review', evidence, 'Conflicting category clues in folder names.'
    return 'To Review', 'No recognized category clues in relative folder names.', 'Insufficient evidence. Filename alone is not used.'


def protected_link(info):
    # Do not recurse into symlinks, junctions or other reparse directories.
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def row_issue(path, root, reason):
    return {'Name': path.name, 'Original path': str(path), 'Relative path': str(path.relative_to(root)),
            'Original folder': str(path.parent), 'File type': 'Scan issue',
            'Suggested category': 'To Review', 'Review status': 'Needs review',
            'Review reason': reason, 'Visual inspection': 'Not performed', 'Scan status': 'Skipped'}


def inventory(root):
    stack = [root]
    while stack:
        folder = stack.pop()
        try:
            with os.scandir(folder) as entries:
                entries = sorted(entries, key=lambda entry: entry.name.casefold())
        except OSError as error:
            yield row_issue(folder, root, f'Cannot list folder: {error}')
            continue
        for entry in entries:
            path = Path(entry.path)
            try:
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    if protected_link(info):
                        yield row_issue(path, root, 'Reparse directory/junction skipped to avoid following another location.')
                    else:
                        stack.append(path)
                    continue
                if entry.is_symlink():
                    yield row_issue(path, root, 'Symbolic link skipped; target not accessed.')
                    continue
                if not stat.S_ISREG(info.st_mode):
                    continue
                extension = path.suffix.lower()
                if extension not in PHOTOS | VIDEOS:
                    continue
                relative = path.relative_to(root)
                category, evidence, reason = classify(relative)
                yield {'Name': path.name, 'Original path': str(path), 'Relative path': str(relative),
                       'Original folder': str(path.parent), 'File type': 'Photo' if extension in PHOTOS else 'Video',
                       'Extension': extension, 'Size bytes': info.st_size,
                       'Modified UTC': datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(),
                       'Suggested category': category, 'Evidence': evidence, 'Review status': 'Needs review',
                       'Review reason': reason, 'Visual inspection': 'Not performed', 'Scan status': 'Listed'}
            except OSError as error:
                yield row_issue(path, root, f'Cannot inspect metadata: {error}')


def safe_cell(value):
    # Prevent spreadsheet formula execution when imported/opened in Excel.
    # Original path remains exact and preserves the original filename.
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')):
        return "'" + value
    return value


def create_report(source, destination):
    source = Path(source).expanduser().absolute()
    destination = Path(destination).expanduser().absolute()
    info = source.lstat()
    if not stat.S_ISDIR(info.st_mode) or protected_link(info):
        raise ValueError('Source must be a real directory, not a symlink or reparse directory.')
    real_source = source.resolve()
    real_destination = destination.resolve()
    if real_destination == real_source or real_source in real_destination.parents:
        raise ValueError('The CSV must be saved outside the source folder.')
    if not destination.parent.is_dir():
        raise ValueError('Report folder does not exist. Select an existing folder outside the source.')
    count = issues = 0
    # Exclusive creation never overwrites a previous report, even under concurrent runs.
    with destination.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        for row in inventory(source):
            writer.writerow({key: safe_cell(value) for key, value in row.items()})
            if row['Scan status'] == 'Listed':
                count += 1
            else:
                issues += 1
    return count, issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True, help='New CSV path outside source; existing files are never overwritten')
    args = parser.parse_args()
    try:
        count, issues = create_report(args.source, args.output)
    except (OSError, ValueError) as error:
        print(f'Inventory stopped: {error}', file=sys.stderr)
        print('Source files were not modified. If a partial report exists, preserve it and choose a new report name.', file=sys.stderr)
        return 1
    print(f'Media files listed: {count}. Scan issues: {issues}.')
    print(f'New CSV: {args.output}')
    print('All category suggestions require human review. No media content was opened.')
    if issues:
        print('The inventory is incomplete: review the Scan issue rows.')
    if not count:
        print('No supported media files were found. This does not establish a complete media inventory.')
    return 2 if issues or not count else 0


if __name__ == '__main__':
    raise SystemExit(main())
