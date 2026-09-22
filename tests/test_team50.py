import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile,unittest
from main import App
from expedition import Session
from team_beacons50 import initialize,update,credit
from model import distances

class Team50(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.a=App(self.tmp.name)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def game(self,tier=0):return Session(self.a.store,tier,coop=True)
 def test_locations_are_reachable_and_do_not_change_rng_or_collectibles(self):
  for tier in range(5):
   for _ in range(3):
    g=self.game(tier);rng=g.rng.getstate();grid=[r[:] for r in g.grid];seeds=set(g.seeds);dew=set(g.dew)
    initialize(g);self.assertEqual(g.rng.getstate(),rng);self.assertEqual(grid,g.grid);self.assertEqual(seeds,g.seeds);self.assertEqual(dew,g.dew)
    self.assertEqual(len(g.team_beacons),2);a,b=g.team_beacons
    self.assertTrue(8<=distances(g.grid,[a])[b]<=22)
    self.assertFalse(set(g.team_beacons)&(g.seeds|g.berries|g.rescues|set(g.interactables)))
 def test_requires_both_players_and_resets_on_departure_or_down(self):
  g=self.game();a,b=g.team_beacons;g.player=a;g.partner['pos']=b
  update(g,.8);self.assertAlmostEqual(g.team_hold,.8)
  g.partner['down']=True;update(g,.2);self.assertEqual(g.team_hold,0)
  g.partner['down']=False;update(g,.8);g.player=(1,1);update(g,.2);self.assertEqual(g.team_hold,0)
  g.player=a;update(g,1.5);self.assertTrue(g.team_complete)
  g.player=(1,1);update(g,.2);self.assertTrue(g.team_complete)
 def test_no_stamp_until_clear_and_only_once(self):
  g=self.game();g.team_complete=True;self.assertFalse(credit(g));g.state='caught';self.assertFalse(credit(g))
  g.state='cleared';self.assertTrue(credit(g));self.assertFalse(credit(g));self.assertEqual(len(g.store.get('team_beacons50',{})),1)
 def test_saved_state_and_legacy_runs(self):
  g=self.game();g.player,g.partner['pos']=g.team_beacons;update(g,.5)
  restored=Session.restore(self.a.store,g.snapshot());self.assertEqual(restored.team_beacons,g.team_beacons);self.assertEqual(restored.team_hold,.5)
  data=g.snapshot()
  for name in ('team_beacons','team_hold','team_complete','team_stamp_new'):data['attrs'].pop(name)
  old=Session.restore(self.a.store,data);self.assertEqual(old.team_beacons,[])
  solo=Session(self.a.store,0);self.assertEqual(solo.team_beacons,[])
 def test_pause_and_journal_navigation(self):
  a=self.a;a.coop=True;a.start(0);g=a.game;g.player,g.partner['pos']=g.team_beacons;g.team_hold=.5
  a.action('pause');a.update(.05);self.assertEqual(g.team_hold,.5)
  a.draw();a.action('team_journal');a.draw();a.action('back');self.assertEqual(a.screen,'paused')
