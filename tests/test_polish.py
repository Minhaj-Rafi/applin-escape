import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
from pathlib import Path
import sqlite3
from contextlib import closing
import unittest
from unittest.mock import patch
import pygame
from main import App
from model import Store,path_to,distances,neighbors
from expedition import Session,challenge_code
from save_recovery import backup_store,restore_backup


class Recovery(unittest.TestCase):
    def test_backup_restore_preserves_progress_and_previous_files(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(d); store.set('example',{'value':7}); backup_store(store)
            store.set('example',{'value':99}); store.db.close()
            preserved=restore_backup(d)
            self.assertTrue((preserved/'progress.sqlite3').exists())
            with closing(sqlite3.connect(Path(d)/'progress.sqlite3')) as db:
                self.assertIn('7',db.execute("SELECT value FROM settings WHERE name='example'").fetchone()[0])
            with self.assertRaises(ValueError): restore_backup(d,4)

    def test_bad_backup_is_rejected_without_changing_current_save(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(d); store.set('hello',12); store.close()
            source=Path(d)/'progress.sqlite3'; before=source.read_bytes()
            (Path(d)/'backups/progress-1.sqlite3').write_bytes(b'broken')
            with self.assertRaises(sqlite3.DatabaseError): restore_backup(d)
            self.assertEqual(source.read_bytes(),before)


class Polish(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.a=App(self.tmp.name)
    def tearDown(self): self.a.close(); self.tmp.cleanup()

    def test_inspecting_every_biome_pauses_and_returns_without_using_it(self):
        a=self.a
        for tier in range(5):
            a.start(tier); g=a.game; target=a.inspect_targets()[0]; before=g.snapshot()
            a.action(f'inspect:{target[0]}:{target[1]}'); a.draw(); a.update(.5)
            self.assertEqual(a.screen,'object_info'); self.assertEqual(before,g.snapshot())
            self.assertTrue(a.object_status(target))
            a.action('back'); self.assertEqual(a.screen,'paused'); a.action('resume')
            self.assertEqual(a.screen,'play')

    def test_nearest_inspection_button_and_controller_back(self):
        a=self.a; a.start(); a.action('pause'); a.draw()
        self.assertIn('inspect_nearest',[action for _,action in a.buttons])
        a.action('inspect_nearest'); a.draw(); self.assertEqual(a.screen,'object_info')
        a.control_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,instance_id=44,button=pygame.CONTROLLER_BUTTON_B))
        self.assertEqual(a.screen,'paused')

    def test_existing_function_key_binding_takes_priority_over_call(self):
        a=self.a; a.coop=True; a.start(); a.controls.bind_key(0,4,pygame.K_F3)
        pygame.event.clear(); pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F3)); a.events()
        self.assertEqual(a.pings,{})
        self.assertEqual(a.controls.keys[0][4],pygame.K_F3)

    def test_lure_inspection_reports_real_cooldown(self):
        a=self.a; a.start(0); g=a.game; pos=g.interactables[0]; g.player=pos
        self.assertIn('Ready',a.object_status(pos)); g.interact()
        self.assertIn('14 seconds',a.object_status(pos)); g.update(.25)
        self.assertIn('Recharging',a.interaction_hint())

    def test_tutorial_includes_distraction_and_refills_escapes(self):
        a=self.a; a.start(mode='tutorial'); g=a.game
        g.steps=6; g.tutorial_seen_grass=True; g.update(.01)
        self.assertEqual(g.tutorial_step,2)
        g.player=g.interactables[0]; g.interact(); g.update(.01)
        self.assertEqual(g.tutorial_step,3)
        g.escapes_used=1; g.escapes=0; g.update(.01)
        self.assertEqual(g.tutorial_step,4); self.assertGreater(g.escapes,0)
        g.tutorial_seed=True; g.update(.01); self.assertEqual(g.tutorial_step,5)
        a.draw()

    def test_coop_ping_keyboard_and_expiry_without_changing_positions(self):
        a=self.a; a.coop=True; a.start(); g=a.game; original=(g.player,g.partner['pos'])
        pygame.event.clear()
        for key in (pygame.K_F3,pygame.K_F4): pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=key))
        a.events(); self.assertEqual(set(a.pings),{0,1}); a.draw()
        self.assertEqual(original,(g.player,g.partner['pos']))
        g.elapsed+=6
        self.assertTrue(all(expiry<g.elapsed for _,expiry in a.pings.values()))
        g.partner['down']=True; g.partner['revive']=3; a.draw()

    def test_reading_volume_and_new_screens_persist(self):
        a=self.a; a.action('accessibility'); a.action('large_text')
        a.action('music_level'); a.action('effects_level'); a.draw()
        self.assertTrue(a.store.get('large_text_v42',False))
        self.assertEqual(a.audio.music_volume,.6); self.assertEqual(a.audio.effects_volume,1)
        a.action('effects_level'); self.assertEqual(a.audio.effects_volume,0)
        a.action('back'); self.assertEqual(a.screen,'menu')
        for tier in range(5):
            a.start(tier); a.game.rescued=2; a.game.finish('cleared'); a.consume_events()
            a.action('ending'); a.draw(); self.assertEqual(a.screen,'ending')
            a.action('back'); self.assertEqual(a.screen,'result')

    def test_personal_best_comparison_captures_prior_record(self):
        a=self.a; a.start(); g=a.game; g.elapsed=80; g.steps=100; g.finish('cleared')
        a.start(); h=a.game; h.elapsed=70; h.steps=90; h.finish('cleared')
        self.assertEqual(h.previous_best['seconds'],80)
        self.assertIn('-10.0s',a.result_comparison()); self.assertIn('-10 steps',a.result_comparison())

    def test_tactical_rules_are_versioned_and_replay_keeps_legacy(self):
        for version in (31,42):
            code=challenge_code(3,345,'Standard','Leaf Slip',False,rules=version)
            g=Session(self.a.store,code=code)
            self.assertEqual(g.rules_version,version); self.assertEqual(g.code,code)
            h=Session.restore(self.a.store,g.snapshot()); self.assertEqual(h.rules_version,version)
        g=Session(self.a.store,3,seed_source=lambda:937)
        self.assertTrue(g.code.startswith('AE52-'))
        # A close interceptor predicts a legal corridor cell; a lure wins over prediction.
        e=g.enemies[1]; e.role='TRACKER'; g.elapsed=g.config.patrol_seconds+1
        origin=next(p for p in g.floors if (p[0]+1,p[1]) in g.floors)
        g.player=origin; g.direction=(1,0); e.pos=origin; g.hidden_cells=set()
        target=g.enemy_target(e,distances(g.grid,[origin]))
        self.assertIn(target,g.floors)
        self.assertNotEqual(target,origin)
        g.lure_pos=origin; g.lure_time=5
        self.assertEqual(g.enemy_target(e,distances(g.grid,[origin])),origin)
        self.assertEqual(e.mood,'lured')

    def test_pose_changes_and_comfort_restores_static_sprite(self):
        a=self.a; a.start(); a.characters=True; a.comfort=False; g=a.game
        a.visual_player=list(g.player); g.escape_cooldown=0
        idle=a.hero_sprite(70,0,(1,0))
        g.escape_cooldown=1
        escaped=a.hero_sprite(70,0,(1,0))
        self.assertNotEqual(pygame.image.tostring(idle,'RGBA'),pygame.image.tostring(escaped,'RGBA'))
        a.comfort=True
        one=a.hero_sprite(70,0,(1,0)); g.escape_cooldown=0
        two=a.hero_sprite(70,0,(1,0))
        self.assertEqual(pygame.image.tostring(one,'RGBA'),pygame.image.tostring(two,'RGBA'))

if __name__=='__main__': unittest.main()
