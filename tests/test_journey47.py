import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
from main import App
from expedition import Session
from model import neighbors
from journey47 import map_report,home_snapshot,home_feedback
from home_progress import home_progress
from home_activities import care_state

class Journey47(unittest.TestCase):
 def setUp(self): self.tmp=tempfile.TemporaryDirectory();self.a=App(self.tmp.name)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def test_map_batch_objectives_accessible_without_shortcuts(self):
  for tier in range(5):
   for seed in range(10):
    g=Session(self.a.store,tier,seed_source=lambda:7000+tier*100+seed)
    report=map_report(g)
    self.assertTrue(report['reachable'],(tier,seed));self.assertGreaterEqual(report['spawn_distance'],16)
 def test_blocked_swoop_stops_instead_of_sidestep(self):
  g=Session(self.a.store,1);bird,blocker=g.enemies
  pos=next(p for p in g.floors if len(list(neighbors(g.grid,p)))>=3 and p!=(1,1))
  nxt=next(iter(neighbors(g.grid,pos)))
  bird.pos=pos;bird.attack=[nxt];bird.timer=0;bird.attack_cd=5
  blocker.pos=nxt;blocker.timer=99;g.invulnerable=99
  g.update(.01)
  self.assertEqual(bird.pos,pos);self.assertEqual(bird.attack,[]);self.assertGreater(bird.recovery,0)
 def test_capture_names_actual_bird(self):
  g=Session(self.a.store,0);g.invulnerable=0;g.enemies[0].pos=g.player;g.enemies[0].mood='swoop'
  g.collision();self.assertIn(g.enemies[0].species,g.last_capture47);self.assertIn('swoop',g.last_capture47)
 def test_optional_tour_navigation_and_static_comfort(self):
  a=self.a;a.action('home_hub');a.action('home_tour')
  for i in range(4):
   a.draw();self.assertEqual(a.home_tour47,i)
   if i<3:a.action('tour_next')
  a.action('back');self.assertIsNone(a.home_tour47);self.assertEqual(a.screen,'home_hub')
  a.action('home_tour');self.assertEqual(a.home_tour47,0)
 def test_new_achievements_reported_once(self):
  before=home_snapshot(self.a.store);p=home_progress(self.a.store);c=care_state(p);c['harvests']=1
  self.a.store.set('sanctuary_v4',p);after=home_snapshot(self.a.store)
  self.assertIn('First harvest',home_feedback(before,after));self.assertEqual(home_feedback(after,after),'')
