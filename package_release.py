"""Package a verified Windows build; never substitute a Linux binary."""
import hashlib
import json
from pathlib import Path
import zipfile
from release_info import VERSION

REQUIRED_SCREENS = {
    'menu', 'tier_1', 'tier_2', 'tier_3', 'tier_4', 'tier_5',
    'challenge', 'challenge_hall', 'controls', 'sanctuary', 'support', 'coop'
}
MINIMUM_SCREEN_COUNT = 52
REQUIRED_WINDOW_SIZES = [[800, 600], [1280, 720], [1600, 900]]


def package(build=Path('dist/ApplinEscape'), preview=Path('build-preview'), output=Path('release')):
    build, preview, output = map(Path, (build, preview, output))
    manifest = json.loads((preview/'release_check.json').read_text())
    if manifest.get('version') != VERSION or not manifest.get('asset_check'):
        raise ValueError('Run the current executable preview with --verify-build first.')
    screens = set(manifest.get('screens', ()))
    if (manifest.get('count') != len(screens) or len(screens) < MINIMUM_SCREEN_COUNT
            or not REQUIRED_SCREENS <= screens):
        raise ValueError('The release preview is incomplete or contains duplicate screens.')
    if manifest.get('window_sizes') != REQUIRED_WINDOW_SIZES:
        raise ValueError('The release preview did not pass every required window size.')
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
        for name in ('README.md', 'RELEASE_NOTES.md', 'RELEASE_STATUS.md',
                     'WINDOWS_RELEASE.md', 'LICENSE', 'PRIVACY.md', 'SUPPORT.md'):
            archive.write(name, Path('ApplinEscape')/name)
        archive.write(preview/'release_check.json', 'ApplinEscape/build_check.json')
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.sha256').write_text(f'{digest}  {target.name}\n')
    print(target)
    return target

if __name__ == '__main__': package()
