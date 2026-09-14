import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publish', ROOT/'releases/publish.py')
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


class Releases(unittest.TestCase):
    def test_all_snapshots_validated_and_assets_checksummed(self):
        with patch.object(pub.subprocess, 'check_output', return_value=b'print("historical snapshot")\n') as git:
            prepared = pub.prepare()
        self.assertEqual(len(prepared), 13)
        self.assertEqual(sum(r[0]['latest'] for r in prepared), 1)
        self.assertEqual(prepared[-1][0]['tag'], 'v0.7.0')
        self.assertTrue(all('SHA256SUMS.txt' in assets for _, _, assets in prepared))
        self.assertTrue(all(len(c.args[0][-1].split(':')[0]) == 40 for c in git.call_args_list))

    def test_draft_then_upload_then_publish(self):
        api = Mock()
        api.call.side_effect = [None, None, {'id': 1, 'upload_url': 'https://uploads.github.com/assets{?name}'}, [], {}, {}]
        item = dict(tag='v0.1.0', commit='a'*40, title='Original', latest=False)
        pub.publish(api, [(item, 'notes', {'lyrics.py': b'code'})])
        calls = api.call.call_args_list
        self.assertTrue(calls[2].args[2]['draft'])
        self.assertTrue(calls[4].kwargs['binary'])
        self.assertFalse(calls[5].args[2]['draft'])
        self.assertEqual(calls[5].args[2]['make_latest'], 'false')

    def test_conflicting_tag_stops_before_writes(self):
        api = Mock()
        api.call.return_value = {'object': {'type': 'commit', 'sha': 'b'*40}}
        with self.assertRaises(ValueError):
            pub.publish(api, [({'tag': 'v0.1.0', 'commit': 'a'*40}, '', {})])
        self.assertEqual(api.call.call_count, 1)

    def test_existing_published_release_is_not_overwritten(self):
        api = Mock()
        api.call.side_effect = [None, {'draft': False}]
        pub.publish(api, [({'tag': 'v0.1.0', 'commit': 'a'*40}, '', {})])
        self.assertEqual(api.call.call_count, 2)


if __name__ == '__main__':
    unittest.main()

