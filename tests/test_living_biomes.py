import json
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'
import tempfile
import unittest
from unittest.mock import patch
import pygame
from model import Store, distances, path_to, neighbors
from expedition import Session, challenge_code, decode, encode
from controls import Controls, stick_direction
from main import App


class BiomeMechanics(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.store=Store(self.tmp.name)
    def tearDown(self): self.store.close(); self.tmp.cleanup()
    def game(self,tier=0,**kw): return Session(self.store,tier,**kw)

    def test_fruit_and_bells_lure_nearby_birds_and_cool_down(self):
        for tier in (0,2):
            g=self.game(tier); target=g.interactables[0]; g.player=target
            self.assertTrue(g.interact())
            e=g.enemies[0]; e.pos=next(neighbors(g.grid,target))
            self.assertIsNone(g.biome_enemy_target(e))
            g.update_biome_rules(1)
            self.assertEqual(g.biome_enemy_target(e),target)
            self.assertEqual(e.mood,'lured')
            uses=g.biome_uses; g.interact(); self.assertEqual(g.biome_uses,uses)
            g.update_biome_rules(20); g.interact(); self.assertEqual(g.biome_uses,uses+1)

    def test_tide_warns_waits_for_occupants_and_reopens(self):
        g=self.game(1,coop=True); tile=g.bridge[0]
        self.assertTrue(g.bridge_open)
        g.elapsed=9; g.update_biome_rules(0)
        self.assertEqual(g.tide_label,'CLOSING SOON')
        g.elapsed=11; g.partner['pos']=tile; g.update_biome_rules(0)
        self.assertTrue(g.bridge_open)
        self.assertEqual(g.tide_label,'WAITING FOR YOU')
        g.partner['pos']=(1,1); g.update_biome_rules(0)
        self.assertFalse(g.bridge_open)
        self.assertIn(g.exit,distances(g.grid,[(1,1)]))
        g.elapsed=16; g.update_biome_rules(0)
        self.assertTrue(g.bridge_open)

    def test_ruin_gate_swap_preserves_occupants_and_base_routes(self):
        g=self.game(3)
        self.assertEqual(len(g.ruin_gates),2)
        old,new=g.ruin_gates
        g.player=g.switch; self.assertTrue(g.interact())
        self.assertTrue(g.ruin_request)
        g.player=old; g.update_biome_rules(2)
        self.assertTrue(g.ruin_request)
        g.player=(1,1); g.update_biome_rules(.05)
        self.assertFalse(g.ruin_request)
        self.assertEqual(g.grid[old[1]][old[0]],1)
        self.assertEqual(g.grid[new[1]][new[0]],0)
        self.assertTrue(g.seeds <= distances(g.grid,[g.player]).keys())

    def test_wind_ride_has_cooldown_collects_and_handles_partner(self):
        g=self.game(4,coop=True)
        self.assertTrue(g.wind_lanes)
        lane=g.wind_lanes[0]; g.partner['pos']=lane['cells'][0]
        g.berries.add(lane['cells'][1]); old=g.player
        self.assertTrue(g.interact(partner=True))
        self.assertEqual(g.player,old)
        self.assertEqual(g.partner['pos'],lane['cells'][3])
        self.assertNotIn(lane['cells'][1],g.berries)
        self.assertGreater(g.partner['invulnerable'],0)
        uses=g.biome_uses
        g.interact(partner=True)
        self.assertEqual(g.biome_uses,uses)

    def test_generation_keeps_objectives_reachable_across_terrain_cycles(self):
        for tier in range(5):
            for seed in range(20):
                code=challenge_code(tier,seed,'Standard','Leaf Slip',False)
                g=self.game(code=code)
                for time in (0,9,11,16):
                    g.elapsed=time; g.update_biome_rules(.1)
                    reachable=distances(g.grid,[(1,1)])
                    self.assertTrue(g.seeds|g.rescues|{g.exit,g.switch} <= reachable.keys())
                if tier==4: self.assertTrue(g.wind_lanes)

    def test_exact_save_of_biome_timers_and_future_changes(self):
        for tier in range(5):
            g=self.game(tier); g.invulnerable=100
            if tier in (0,2): g.player=g.interactables[0]; g.interact()
            if tier==3: g.player=g.switch; g.interact()
            g.update(.1)
            h=Session.restore(self.store,json.loads(json.dumps(g.snapshot())))
            for _ in range(40): g.update(.05); h.update(.05)
            self.assertEqual(g.snapshot(),h.snapshot())

    def test_legacy_codes_and_saves_keep_old_rules(self):
        code=challenge_code(1,813,'Standard','Leaf Slip',False,legacy=True)
        g=self.game(code=code)
        self.assertEqual(g.rules_version,30)
        self.assertFalse(g.bridge_open)
        g.elapsed=16; g.update_biome_rules(2)
        self.assertFalse(g.bridge_open)
        data=g.snapshot(); attrs=decode(data['attrs'])
        for k in ('rules_version','lure_pos','lure_time','lure_pending','terrain_cooldowns','biome_uses',
                  'ruin_pending','ruin_turn','ruin_request','tide_label','interactables','ruin_gates','wind_lanes'):
            attrs.pop(k)
        data['attrs']=encode(attrs)
        for e in data['enemies']: e.pop('recovery')
        restored=Session.restore(self.store,data)
        self.assertEqual(restored.rules_version,30)
        self.assertEqual(restored.grid,g.grid)
        self.assertEqual(restored.code,code)
        restored.update(.05)

    def test_swoop_budget_recovery_and_respawn_reset(self):
        g=self.game(4); g.elapsed=10; g.invulnerable=99
        near=list(distances(g.grid,[g.player]))[3:8]
        for e,pos in zip(g.enemies,near): e.pos=pos; e.attack_cd=0; e.timer=0; e.role='TRACKER'
        g.update(.01)
        self.assertLessEqual(sum(bool(e.warning or e.attack) for e in g.enemies),1)
        e=g.enemies[0]; e.pos=next(neighbors(g.grid,g.player)); e.attack=[g.player]; e.warning=0; e.timer=0
        g.update(.01)
        self.assertGreater(e.recovery,0)
        g.invulnerable=0; e.pos=g.player
        self.assertTrue(g.collision())
        self.assertTrue(all(not e.attack and e.warning==0 for e in g.enemies))


class FakePad:
    def __init__(self): self.buttons=set(); self.axes={}; self.connected=True
    def attached(self): return self.connected
    def get_button(self,b): return b in self.buttons
    def get_axis(self,a): return self.axes.get(a,0)
    def quit(self): self.connected=False


class InputFlow(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.app=App(self.tmp.name)
    def tearDown(self): self.app.close(); self.tmp.cleanup()

    def test_keyboard_remap_persists_and_old_key_stops_moving(self):
        a=self.app; a.start(); g=a.game
        p=next(neighbors(g.grid,g.player)); direction=(p[0]-1,p[1]-1)
        index=1 if direction==(1,0) else 2
        old=a.controls.keys[0][index]
        self.assertEqual(a.controls.bind_key(0,index,pygame.K_j),'')
        a.move_timer=0; pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=old)); a.events()
        self.assertEqual(g.player,(1,1))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_j)); a.events()
        self.assertEqual(g.player,p)
        c=Controls(a.store)
        self.assertEqual(c.keys[0][index],pygame.K_j); c.close()
        self.assertTrue(a.controls.bind_key(0,4,pygame.K_p))
        self.assertTrue(a.controls.bind_key(0,4,pygame.K_UP))

    def test_binding_capture_and_back_navigation(self):
        a=self.app; a.action('settings'); a.action('controls'); a.action('bind:0:4')
        pygame.event.clear(); pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_q)); a.events()
        self.assertEqual(a.controls.keys[0][4],pygame.K_q)
        self.assertIsNone(a.binding)
        a.action('back'); self.assertEqual(a.screen,'settings')
        a.action('back'); self.assertEqual(a.screen,'menu')

    def test_stick_deadzone_cardinal_direction_and_pad_assignment(self):
        self.assertIsNone(stick_direction(.1,-.1,.3))
        self.assertEqual(stick_direction(.8,.3),(1,0))
        self.assertEqual(stick_direction(.2,-.9),(0,-1))
        c=self.app.controls; pad=FakePad(); c.pads={11:(pad,0)}; c.first_player=1
        pad.axes[pygame.CONTROLLER_AXIS_LEFTX]=30000
        self.assertEqual(c.pad_direction(1,True),(1,0))
        self.assertIsNone(c.pad_direction(0,True))
        self.assertEqual(c.pad_direction(0,False),(1,0))

    def test_gamepad_ability_interaction_menu_and_disconnect(self):
        a=self.app; a.ability='Camouflage'; a.start(0)
        pad=FakePad(); a.controls.pads={44:(pad,0)}
        g=a.game; pygame.event.clear()
        a.control_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,instance_id=44,button=pygame.CONTROLLER_BUTTON_A))
        self.assertGreater(g.camouflage,0)
        g.player=g.interactables[0]
        a.control_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,instance_id=44,button=pygame.CONTROLLER_BUTTON_X))
        self.assertEqual(g.biome_uses,1)
        with patch.object(a.controls,'refresh',return_value=True):
            a.control_event(pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED,instance_id=44))
        self.assertEqual(a.screen,'paused')
        a.draw()
        a.control_event(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,instance_id=44,button=pygame.CONTROLLER_BUTTON_A))
        self.assertEqual(a.screen,'play')

    def test_pad_button_rebind_validation_and_persistence(self):
        c=self.app.controls
        self.assertEqual(c.bind_button(0,pygame.CONTROLLER_BUTTON_Y),'')
        self.assertTrue(c.bind_button(1,pygame.CONTROLLER_BUTTON_Y))
        self.assertTrue(c.bind_button(0,pygame.CONTROLLER_BUTTON_START))
        new=Controls(self.app.store)
        self.assertEqual(new.pad_buttons[0],pygame.CONTROLLER_BUTTON_Y)
        new.close()

    def test_new_screens_render_and_comfort_is_still_stationary(self):
        a=self.app; a.action('controls'); a.draw()
        self.assertEqual(len(a.buttons),18)
        a.action('comfort')
        for tier in range(5):
            a.start(tier); a.draw(); old=pygame.image.tostring(a.canvas,'RGB')
            a.t+=1; a.draw()
            self.assertEqual(old,pygame.image.tostring(a.canvas,'RGB'))
            self.assertTrue(a.overview)


if __name__=='__main__': unittest.main()
