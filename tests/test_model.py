from pathlib import Path
import random
import tempfile
import unittest
from model import Store, Session, TIERS, canonical_layout, generate, distances, neighbors, path_to


class Rules(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)
        self.seed = 100

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def game(self, tier=0):
        self.seed += 1
        return Session(self.store, tier, seed_source=lambda: self.seed)

    def test_100_maps_connected_objectives_reachable_and_safe_spawn(self):
        hashes = set()
        for tier in range(5):
            for _ in range(20):
                g = self.game(tier)
                floors = {(x, y) for y, row in enumerate(g.grid) for x, wall in enumerate(row) if not wall}
                reachable = distances(g.grid, [g.player])
                self.assertEqual(floors, set(reachable))
                self.assertTrue(g.seeds <= floors)
                self.assertEqual(len(g.seeds), TIERS[tier].seeds)
                self.assertTrue(all(reachable[e.pos] >= 16 for e in g.enemies))
                self.assertIn(g.exit, floors)
                self.assertNotIn(g.exit, g.seeds | g.berries | g.dew)
                self.assertFalse(g.seeds & (g.berries | g.dew))
                self.assertFalse(g.berries & g.dew)
                self.assertNotIn(g.fingerprint, hashes)
                hashes.add(g.fingerprint)
                # Connected graph must have cycles, unlike an unbraided DFS tree.
                edges = sum(len(list(neighbors(g.grid, p))) for p in floors)//2
                self.assertGreater(edges, len(floors)-1)

    def test_symmetry_and_persistent_repeat_rejection(self):
        original = Session(self.store, 0, seed_source=lambda: 77)
        grid = original.grid
        layout = canonical_layout(grid)
        self.assertEqual(layout, canonical_layout([r[::-1] for r in grid]))
        self.assertEqual(layout, canonical_layout([list(r) for r in zip(*grid[::-1])]))
        first = original.fingerprint
        self.assertTrue(first)
        self.assertIsNone(self.store.claim(layout, 999, 0))
        self.store.close()
        self.store = Store(self.tmp.name)
        self.assertIsNone(self.store.claim(layout, 77, 0))
        seeds = iter([77, 78])
        g = Session(self.store, 0, seed_source=lambda: next(seeds))
        self.assertEqual(g.seed, 78)
        self.assertNotEqual(g.fingerprint, first)

    def test_wall_collision_and_step_count(self):
        g = self.game()
        self.assertFalse(g.move((-1, 0)))
        self.assertEqual(g.steps, 0)
        nxt = next(neighbors(g.grid, g.player))
        self.assertTrue(g.move((nxt[0]-1, nxt[1]-1)))
        self.assertEqual(g.steps, 1)
        self.assertEqual(g.player, nxt)

    def test_leaf_slip_safe_landing_cooldown_and_exhaustion(self):
        for tier in range(5):
            g = self.game(tier)
            for i in range(g.config.escapes):
                old = g.player
                g.escape_cooldown = 0
                self.assertTrue(g.escape())
                self.assertNotEqual(g.player, old)
                self.assertEqual(g.grid[g.player[1]][g.player[0]], 0)
                safety = distances(g.grid, [e.pos for e in g.enemies])
                self.assertGreaterEqual(safety[g.player], 3)
                self.assertGreater(g.invulnerable, 0)
                self.assertEqual(g.decoy, old)
                self.assertEqual(g.escapes_used, i+1)
                self.assertFalse(g.escape())
            self.assertEqual(g.escapes, 0)
            g.escape_cooldown = 0
            self.assertFalse(g.escape())

    def test_collision_respawn_and_game_over_saved_once(self):
        g = self.game()
        for remaining in reversed(range(g.config.hearts)):
            g.invulnerable = 0
            g.enemies[0].pos = g.player
            self.assertTrue(g.collision())
            self.assertEqual(g.health, remaining)
            if remaining:
                self.assertEqual(g.player, (1, 1))
                self.assertGreater(g.invulnerable, 0)
        self.assertEqual(g.state, 'caught')
        g.finish('caught')
        self.assertEqual(len(self.store.records()), 1)

    def test_invulnerability_and_stunned_birds_do_not_damage(self):
        g = self.game()
        g.enemies[0].pos = g.player
        self.assertFalse(g.collision())
        g.invulnerable = 0
        g.enemies[0].stunned = 1
        self.assertFalse(g.collision())

    def test_all_five_objective_routes_complete(self):
        for tier in range(5):
            g = self.game(tier)
            # Isolate collection/exit rules; enemy simulation tested separately below.
            g.invulnerable = 999
            targets = sorted(g.seeds) + [g.exit]
            for target in targets:
                for cell in path_to(g.grid, g.player, target)[1:]:
                    self.assertTrue(g.move((cell[0]-g.player[0], cell[1]-g.player[1])))
            self.assertEqual(g.state, 'cleared')
            self.assertFalse(g.seeds)
            self.assertGreater(g.score, 0)
            before = g.elapsed
            g.update(1)
            self.assertEqual(g.elapsed, before)

    def test_locked_gate_and_berry(self):
        g = self.game()
        g.player = g.exit
        g.collect()
        self.assertEqual(g.state, 'playing')
        cell = next(iter(g.berries))
        g.player = cell
        g.collect()
        self.assertEqual(g.slow_time, 6)
        self.assertNotIn(cell, g.berries)

    def test_enemies_move_legally_over_30_seconds_each_tier(self):
        for tier in range(5):
            g = self.game(tier)
            g.invulnerable = 999
            steps = 0
            for _ in range(600):
                old = [e.pos for e in g.enemies]
                g.update(.05)
                for before, e in zip(old, g.enemies):
                    self.assertIn(e.pos, [before]+list(neighbors(g.grid, before)))
                    steps += e.pos != before
                self.assertEqual(len(set(e.pos for e in g.enemies)), len(g.enemies))
            self.assertGreater(steps, 10)

    def test_tracker_ambusher_and_decoy_targets(self):
        g = self.game(4)
        d = distances(g.grid, [g.player])
        enemy = g.enemies[0]
        enemy.pos = next(p for p in g.floors if d[p] == 3)
        g.elapsed = g.config.patrol_seconds + 1
        self.assertEqual(g.enemy_target(enemy, d), g.player)
        self.assertEqual(enemy.mood, 'chase')
        enemy.role = 'AMBUSHER'
        target = g.enemy_target(enemy, d)
        self.assertIn(target, g.floors)
        self.assertLessEqual(d[target], 4)
        g.decoy_time = 2
        g.decoy = g.exit
        self.assertEqual(g.enemy_target(enemy, d), g.exit)

    def test_settings_and_abandon_persist(self):
        self.store.set('music', False)
        g = self.game()
        g.update(.05)
        g.abandon()
        self.store.close()
        self.store = Store(self.tmp.name)
        self.assertFalse(self.store.get('music', True))
        self.assertEqual(self.store.records()[0][1], 'abandoned')
        self.assertEqual(self.store.summary()[0], 1)


if __name__ == '__main__':
    unittest.main()
