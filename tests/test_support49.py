import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from main import App
from release_info import VERSION
from run_insights49 import summarize,guidance
from support49 import snapshot,export,check_setup

class Support49(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.a=App(self.tmp.name)
 def tearDown(self):self.a.close();self.tmp.cleanup()
 def add(self,outcome,seconds=10,mode='practice/Standard/solo/Leaf Slip',tier=0):
  self.a.store.db.execute('INSERT INTO runs VALUES(NULL,?,?,?,?,?,?,?,?,?,?)',('now',tier,outcome,seconds,20,1,2,50,'test',mode));self.a.store.db.commit()
 def test_insights_filters_and_averages(self):
  self.add('cleared',20);self.add('caught',90);self.add('abandoned');self.add('cleared',mode='tutorial/Standard/solo/Leaf Slip')
  self.add('cleared',mode='practice/Expert/solo/Leaf Slip');self.add('cleared',mode='practice/Standard/duo/Leaf Slip');self.add('cleared',mode='practice')
  r=summarize(self.a.store)[0]
  self.assertEqual(r['attempts'],2);self.assertEqual(r['clear_rate'],50);self.assertEqual(r['average_clear_seconds'],20)
  self.assertEqual(summarize(self.a.store,'Expert')[0]['attempts'],1)
  self.assertIsNone(summarize(self.a.store)[1]['clear_rate']);self.assertIn('Small samples',guidance(summarize(self.a.store)))
 def test_report_privacy_and_no_save_mutation(self):
  self.a.store.set('player_alias43','PRIVATE_ALIAS');before=self.a.store.db.total_changes
  self.assertEqual(snapshot(self.a)['save_integrity'],'ok');self.assertEqual(before,self.a.store.db.total_changes)
  text=export(self.a).read_text();self.assertNotIn('PRIVATE_ALIAS',text);self.assertNotIn(self.tmp.name,text)
  self.assertEqual(json.loads(text)['game_version'],VERSION)
 def test_navigation_and_button_geometry(self):
  a=self.a
  for action in ('support','run_insights'):
   a.action(action);a.draw()
   for i,(r,k) in enumerate(a.buttons):
    for r2,k2 in a.buttons[i+1:]:self.assertFalse(r.colliderect(r2),(k,k2))
   a.action('back');self.assertEqual(a.screen,'menu')
  a.action('run_insights');a.action('insights_skill');a.action('insights_players');a.draw()
 def test_setup_check_uses_temporary_progress(self):
  with tempfile.TemporaryDirectory() as out:
   with patch('model.default_save_dir',return_value=Path(out)):self.assertEqual(check_setup(),0)
   self.assertFalse((Path(out)/'progress.sqlite3').exists())
   data=json.loads((Path(out)/'exports/setup_check.json').read_text());self.assertEqual(len(data['checks']),6);self.assertTrue(data['passed'])
