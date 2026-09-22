import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import hashlib
from pathlib import Path
import tempfile
import unittest
import pygame
from main import App
from model import distances, ROSTERS
from compose import TRACKS


class BiomeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=App(self.tmp.name)

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def test_collision_matches_visible_terrain_and_grass(self):
        seen=set()
        for tier in range(5):
            self.app.start(tier)
            g=self.app.game
            for (x,y),kind in self.app.world.kinds.items():
                self.assertEqual(bool(g.grid[y][x]),kind in ('water','tree','rock','ruin'))
                seen.add(kind)
            self.assertEqual(g.hidden_cells,self.app.world.grass_cells)
            self.assertEqual(tuple(e.species for e in g.enemies),ROSTERS[tier])
            g.abandon()
        self.assertTrue({'bridge','water','grass','paving','tree','ruin'} <= seen)

    def test_grass_reduces_detection(self):
        self.app.start(4)
        g=self.app.game
        g.player=next(iter(g.hidden_cells))
        d=distances(g.grid,[g.player])
        enemy=g.enemies[0]
        enemy.pos=next(p for p in g.floors if d[p]==g.config.detection//2+1)
        enemy.role='TRACKER'
        enemy.target=g.exit
        g.elapsed=g.config.patrol_seconds+1
        g.enemy_target(enemy,d)
        self.assertEqual(enemy.mood,'patrol')
        g.hidden_cells.remove(g.player)
        self.assertEqual(g.enemy_target(enemy,d),g.player)
        self.assertEqual(enemy.mood,'chase')

    def test_camera_overview_and_edges_keep_player_visible(self):
        self.app.comfort=False
        self.app.start(4)
        for mode in (False,True):
            self.app.overview=mode
            for cell in (self.app.game.player,self.app.game.exit,self.app.game.floors[-1]):
                self.app.game.player=cell
                self.app.visual_player=list(map(float,cell))
                self.app.draw()
                self.assertTrue(pygame.Rect(30,150,880,610).collidepoint(self.app.center(cell)))
        self.assertEqual(self.app.canvas.get_clip(),self.app.canvas.get_rect())

    def test_five_distinct_tracks_switch_on_entry(self):
        hashes=set()
        for tier,track in enumerate(TRACKS):
            self.app.start(tier)
            self.assertEqual(self.app.audio.current_biome,tier)
            self.assertTrue(self.app.audio.available)
            path=Path(__file__).resolve().parents[1]/'assets'/'audio'/f'{track[0]}.wav'
            hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
            self.app.game.abandon()
        self.assertEqual(len(hashes),5)
        self.app.action('menu')
        self.assertIsNone(self.app.audio.current_biome)

    def test_five_distinct_pursuer_sprites(self):
        hashes=set()
        for species in ('pidgeotto','spearow','murkrow','talonflame','cramorant'):
            sprite=self.app.sprites.get(species,64,0)
            hashes.add(hashlib.sha256(pygame.image.tostring(sprite,'RGBA')).hexdigest())
        self.assertEqual(len(hashes),5)


if __name__=='__main__':
    unittest.main()
