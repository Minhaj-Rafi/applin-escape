"""Package a verified Windows build; never substitute a Linux binary."""
import hashlib
import json
from pathlib import Path
import zipfile
from release_info import VERSION


def package(build=Path('dist/ApplinEscape'), preview=Path('build-preview'), output=Path('release')):
    build, preview, output = map(Path, (build, preview, output))
    manifest = json.loads((preview/'release_check.json').read_text())
    if manifest.get('version') != VERSION or not manifest.get('asset_check'):
        raise ValueError('Run the current executable preview with --verify-build first.')
    executable = build/'ApplinEscape.exe'
    if not executable.is_file() or executable.read_bytes()[:2] != b'MZ':
        raise ValueError('A native Windows executable is required.')
    if not (build/'_internal').is_dir():
        raise ValueError('Missing bundled game dependencies.')
    output.mkdir(parents=True, exist_ok=True)
    target = output/f'ApplinEscape-{VERSION}-Windows-RC.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(build.rglob('*')):
            if path.is_file(): archive.write(path, Path('ApplinEscape')/path.relative_to(build))
        for name in ('README.md', 'RELEASE_STATUS.md', 'WINDOWS_RELEASE.md'):
            archive.write(name, Path('ApplinEscape')/name)
        archive.write(preview/'release_check.json', 'ApplinEscape/build_check.json')
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.sha256').write_text(f'{digest}  {target.name}\n')
    print(target)
    return target

if __name__ == '__main__': package()
