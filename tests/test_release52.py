import tempfile
import unittest
from model import Store, distances
from expedition import Session, challenge_code

LEGACY = ['34c32f53316a82493057a1f4cfa11aa33b86c894a1a4b2e27fdf10a5cba3c9e9','54113e0f7e8f6c78a32281a158d0923f6d34876f7983cc21b313b23b5908b032','d10ed040a27535e93b0e0a48dbfa1d4b13b4a76dae18b644b6e36595d40b7507','72fada55df911608f1f0213a6bad998639139431c5354e51143904f0a01223ec','5c67f21e6dcb7eeac316e779e57d2e4f6a4ea4d832c284b25e511081f688d1bd']

class Release52(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.store=Store(self.tmp.name)
    def tearDown(self): self.store.close(); self.tmp.cleanup()
    def test_older_map_fingerprints_are_unchanged(self):
        for tier, expected in enumerate(LEGACY):
            for rules in (31,42):
                g=Session(self.store,code=challenge_code(tier,12345,'Standard','Leaf Slip',False,rules=rules))
                self.assertEqual(g.fingerprint, expected)
    def test_new_regions_connected_objectives_reachable_and_replay_exact(self):
        for tier in range(5):
            for seed in range(12):
                g=Session(self.store,tier,seed_source=lambda: seed,coop=True)
                reached=distances(g.grid,[(1,1)])
                self.assertEqual(len(reached),sum(c==0 for row in g.grid for c in row))
                self.assertTrue((g.seeds|g.berries|g.rescues|{g.exit}).issubset(reached))
                self.assertTrue(all(reached[e.spawn]>=16 for e in g.enemies))
                replay=Session(self.store,code=g.code)
                self.assertEqual(g.grid,replay.grid)
                self.assertEqual(g.seeds,replay.seeds)
                self.assertEqual(g.interactables,replay.interactables)
                self.assertEqual(g.rules_version,52)
