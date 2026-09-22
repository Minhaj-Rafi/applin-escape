import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from package_release import (package, REQUIRED_SCREENS, REQUIRED_WINDOW_SIZES,
                             MINIMUM_SCREEN_COUNT)
from release_info import VERSION


class Packaging531(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.build = root / 'build'
        self.preview = root / 'preview'
        self.output = root / 'release'
        (self.build / '_internal').mkdir(parents=True)
        self.preview.mkdir()
        (self.build / 'ApplinEscape.exe').write_bytes(b'MZtest executable')
        (self.build / '_internal' / 'asset.dat').write_bytes(b'asset')

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self, screens=None):
        if screens is None:
            screens = REQUIRED_SCREENS | {
                f'verified_screen_{index}'
                for index in range(MINIMUM_SCREEN_COUNT - len(REQUIRED_SCREENS))
            }
        screens = sorted(screens)
        (self.preview / 'release_check.json').write_text(json.dumps({
            'version': VERSION,
            'screens': screens,
            'count': len(screens),
            'window_sizes': REQUIRED_WINDOW_SIZES,
            'asset_check': True,
        }))

    def test_verified_windows_candidate_packages_release_documents(self):
        self.manifest()
        target = package(self.build, self.preview, self.output)
        self.assertTrue(target.is_file())
        self.assertTrue(target.with_suffix('.sha256').is_file())
        with zipfile.ZipFile(target) as archive:
            names = set(archive.namelist())
        self.assertIn('ApplinEscape/ApplinEscape.exe', names)
        self.assertIn('ApplinEscape/RELEASE_NOTES.md', names)
        self.assertIn('ApplinEscape/LICENSE', names)
        self.assertIn('ApplinEscape/PRIVACY.md', names)
        self.assertIn('ApplinEscape/build_check.json', names)

    def test_incomplete_preview_cannot_be_packaged(self):
        self.manifest(REQUIRED_SCREENS - {'challenge'})
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            package(self.build, self.preview, self.output)

    def test_windows_icon_and_release_workflow_are_present(self):
        icon = Path('assets/app_icon.ico')
        version_info = Path('version_info.txt').read_text()
        workflow = Path('.github/workflows/windows-build.yml').read_text()
        self.assertTrue(icon.is_file())
        self.assertEqual(icon.read_bytes()[:4], b'\x00\x00\x01\x00')
        self.assertIn("StringStruct('ProductVersion', '5.3.1')", version_info)
        self.assertIn('Create draft GitHub release', workflow)
        self.assertIn('gh release create', workflow)
