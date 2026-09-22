import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import tempfile
import unittest
from unittest.mock import patch
import pygame
from main import App
from expedition import Session,SKILLS,ABILITIES,challenge_code,parse_code
from challenge_hall import GOALS,TOTAL,goal_met
from home_activities import care_action,care_state
from home_progress import home_progress
from garden_timers import BERRIES,crop_action,crop_stage,migrate_crops


class Growth(unittest.TestCase):
    def test_four_varieties_have_saved_timers_and_one_water_boost(self):
        for kind,(_,duration,_) in enumerate(BERRIES):
            care={'beds':[0,0,0],'berries':0,'harvests':0}
            crop_action(care,'plant',0,kind,100)
            crop_action(care,'harvest',0,kind,101); self.assertEqual(care['berries'],0)
            crop_action(care,'water',0,kind,102); ready=care['crops'][0]['ready_at']
            for _ in range(4): crop_action(care,'water',0,kind,103)
            self.assertEqual(ready,care['crops'][0]['ready_at'])
            self.assertEqual(crop_stage(care['crops'][0],ready-1),2)
            crop_action(care,'harvest',0,kind,ready+10000)
            self.assertEqual(care['berries'],2); self.assertIsNone(care['crops'][0])
            self.assertEqual(care['grown_types'],[BERRIES[kind][0]])
    def test_legacy_ripe_crops_remain_ripe(self):
        care={'beds':[0,1,3],'berries':4,'harvests':1}
        crops=migrate_crops(care,50)
        self.assertEqual(crop_stage(crops[2],50),3)
        self.assertEqual(care['berry_types']['Oran'],4)


class Sanctuary43(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.a=App(self.tmp.name)
    def tearDown(self): self.a.close(); self.tmp.cleanup()
    def test_all_960_contract_codes_roundtrip(self):
        keys=set()
        for tier in range(5):
            for skill in SKILLS:
                for ability in ABILITIES:
                    for coop in (False,True):
                        for goal in range(len(GOALS)):
                            code=f'AC1-{goal}-'+challenge_code(tier,812,skill,ability,coop)
                            self.assertEqual(parse_code(code),(tier,812,skill,ability,coop)); keys.add(code)
        self.assertEqual(len(keys),TOTAL)
        with self.assertRaises(ValueError): parse_code('AC1-9-AE42-123')
    def test_contract_reward_goal_checks_replay_and_save(self):
        a=self.a
        for goal in GOALS:
            g=Session(a.store,contract=goal,mode='contract'); g.state='cleared'
            g.hits=1; g.rescued=0; g.escapes_used=1
            self.assertEqual(goal_met(g),goal=='Clear')
            g.hits=0; g.rescued=2; g.escapes_used=0
            self.assertTrue(goal_met(g)); g.state='playing'; g.finish('cleared')
            h=Session(a.store,code=g.code); self.assertEqual(h.contract,goal)
            restored=Session.restore(a.store,h.snapshot()); self.assertEqual(restored.contract,goal)
        self.assertEqual(len(a.store.get('contract_book43',{})),len(GOALS))
        self.assertIn('First mastery',a.store.get('achievements',[]))
    def test_hub_contract_retry_and_nested_record_navigation(self):
        a=self.a; a.action('sanctuary'); a.action('home_hub'); a.draw()
        a.action('records'); a.draw(); a.action('profile'); a.draw(); a.action('back')
        self.assertEqual(a.screen,'records'); a.action('back'); self.assertEqual(a.screen,'home_hub')
        a.action('challenge_hall'); a.contract_goal=2; a.action('contract_start')
        self.assertEqual(a.game.contract,'Rescue duo'); a.game.finish('caught'); a.consume_events(); a.action('retry')
        self.assertEqual(a.game.contract,'Rescue duo')
    def test_full_records_wheel_and_profile_export(self):
        a=self.a
        for _ in range(19):
            a.store.db.execute("INSERT INTO runs VALUES(NULL,'today',0,'cleared',12,35,0,0,150,'test','practice')")
        a.store.db.commit(); a.action('records'); a.draw()
        pygame.event.clear(); pygame.event.post(pygame.event.Event(pygame.MOUSEWHEEL,y=-1)); a.events()
        self.assertEqual(a.record_offset,8)
        for _ in range(5): a.action('record_next')
        self.assertEqual(a.record_offset,16); a.draw()
        a.action('profile'); a.name_input='Rafi_Trainer'; a.action('profile_share'); a.draw()
        self.assertEqual(a.store.get('player_alias43',''),'Rafi_Trainer')
        export=a.store.directory/'exports/player_card.txt'
        self.assertIn('Rafi_Trainer',export.read_text()); self.assertTrue(export.with_suffix('.png').exists())
    def test_collection_selects_last_combination_and_returns_to_hall(self):
        a=self.a; a.action('challenge_hall'); a.action('contract_collection')
        a.action('collection_previous'); a.draw(); self.assertEqual(a.collection_page,TOTAL//8-1)
        a.action(f'contract_pick:{TOTAL-1}')
        self.assertEqual(a.screen,'challenge_hall'); self.assertEqual(a.contract_goal,len(GOALS)-1)
        self.assertEqual(a.selected,4); self.assertTrue(a.coop)
        a.action('contract_start'); self.assertEqual(a.game.contract,'All three')

    def test_saved_crops_keep_deadline_after_reload(self):
        a=self.a
        with patch('garden_timers.time.time',return_value=1000): care_action(a.store,'plant',0,3)
        p=home_progress(a.store); deadline=care_state(p)['crops'][0]['ready_at']
        a.store.set('sanctuary_v4',p)
        with patch('garden_timers.time.time',return_value=1500):
            self.assertEqual(care_state(home_progress(a.store))['crops'][0]['ready_at'],deadline)
            care_action(a.store,'harvest',0,3)
        self.assertEqual(care_state(home_progress(a.store))['berries'],0)

if __name__=='__main__': unittest.main()
