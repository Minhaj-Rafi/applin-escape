"""Saved keyboard bindings plus safely polled mapped and fallback gamepads."""
import os
import pygame
from model import DIRS
try:
    from pygame._sdl2 import controller as sdl_controller
except ImportError:
    sdl_controller=None

ACTIONS=('up','right','down','left','escape','interact')
DEFAULT_KEYS=((pygame.K_w,pygame.K_d,pygame.K_s,pygame.K_a,pygame.K_SPACE,pygame.K_e),
              (pygame.K_UP,pygame.K_RIGHT,pygame.K_DOWN,pygame.K_LEFT,pygame.K_RSHIFT,pygame.K_RCTRL))
RESERVED={pygame.K_ESCAPE,pygame.K_RETURN,pygame.K_TAB,pygame.K_F1,pygame.K_F11,pygame.K_m,pygame.K_p,pygame.K_t,pygame.K_v}


def stick_direction(x,y,deadzone=.3):
    if max(abs(x),abs(y))<deadzone: return None
    return ((1 if x>0 else -1),0) if abs(x)>abs(y) else (0,(1 if y>0 else -1))


class RawPad:
    """Polling fallback for pads SDL does not expose through GameController."""
    def __init__(self,joystick):
        self.joystick=joystick
        name=(joystick.get_name() or '').lower()
        # Windows exposes an unmapped DualSense in PlayStation face-button order.
        self.mapping={0:1,1:2,2:0,3:3} if 'dualsense' in name or 'wireless controller' in name else {}

    def attached(self): return self.joystick.get_attached()
    def quit(self): pass  # Controls owns and closes the retained Joystick.
    def get_axis(self,axis):
        index={pygame.CONTROLLER_AXIS_LEFTX:0,pygame.CONTROLLER_AXIS_LEFTY:1}.get(axis)
        if index is None or index>=self.joystick.get_numaxes(): return 0
        return int(self.joystick.get_axis(index)*32767)
    def get_button(self,button):
        if button in (pygame.CONTROLLER_BUTTON_DPAD_UP,pygame.CONTROLLER_BUTTON_DPAD_DOWN,
                      pygame.CONTROLLER_BUTTON_DPAD_LEFT,pygame.CONTROLLER_BUTTON_DPAD_RIGHT):
            direct={pygame.CONTROLLER_BUTTON_DPAD_UP:11,pygame.CONTROLLER_BUTTON_DPAD_DOWN:12,
                    pygame.CONTROLLER_BUTTON_DPAD_LEFT:13,pygame.CONTROLLER_BUTTON_DPAD_RIGHT:14}[button]
            if direct<self.joystick.get_numbuttons() and self.joystick.get_button(direct): return True
            if self.joystick.get_numhats():
                x,y=self.joystick.get_hat(0)
                return {pygame.CONTROLLER_BUTTON_DPAD_UP:y>0,pygame.CONTROLLER_BUTTON_DPAD_DOWN:y<0,
                        pygame.CONTROLLER_BUTTON_DPAD_LEFT:x<0,pygame.CONTROLLER_BUTTON_DPAD_RIGHT:x>0}[button]
            return False
        index=self.mapping.get(button,button)
        return index<self.joystick.get_numbuttons() and bool(self.joystick.get_button(index))


class Controls:
    def __init__(self,store):
        self.store=store
        self.keys=[list(row) for row in DEFAULT_KEYS]
        saved=store.get('key_bindings31',None)
        if isinstance(saved,list) and len(saved)==2 and all(isinstance(row,list) and len(row)==6 for row in saved):
            flat=[k for row in saved for k in row]
            if all(isinstance(k,int) and k not in RESERVED for k in flat) and len(set(flat))==12:
                self.keys=saved
        self.deadzone=store.get('stick_deadzone31',.3)
        if self.deadzone not in (.2,.3,.4): self.deadzone=.3
        self.first_player=store.get('first_pad31',0)
        if self.first_player not in (0,1): self.first_player=0
        self.pad_buttons=store.get('pad_buttons31',[pygame.CONTROLLER_BUTTON_A,pygame.CONTROLLER_BUTTON_X])
        if not isinstance(self.pad_buttons,list) or len(self.pad_buttons)!=2 or len(set(self.pad_buttons))!=2 or not all(isinstance(b,int) and 0<=b<15 and b not in self.reserved_buttons() for b in self.pad_buttons):
            self.pad_buttons=[pygame.CONTROLLER_BUTTON_A,pygame.CONTROLLER_BUTTON_X]
        self.pads={}
        self.joysticks={}
        self.button_states={}
        self.last_removed=[]
        self.device_names={}
        self.last_input='No controller input detected yet.'
        self.enabled=False
        from event_safety import configure_events
        configure_events()
        if os.environ.get("APPLIN_KEYBOARD_ONLY")=="1" or os.environ.get("APPLIN_TEST_MODE")=="1":
            self.disable_gamepads()
            return
        try:
            pygame.joystick.init()
            if sdl_controller: sdl_controller.init()
            self.enabled=True
            self.refresh(force=True)
        except pygame.error: pass

    def disable_gamepads(self):
        from event_safety import RAW_JOYSTICK_EVENTS,CONTROLLER_EVENTS
        pygame.event.set_blocked(RAW_JOYSTICK_EVENTS+CONTROLLER_EVENTS)
        self.close()
        self.enabled=False
        if sdl_controller:
            try: sdl_controller.quit()
            except pygame.error: pass
        pygame.joystick.quit()

    @staticmethod
    def reserved_buttons():
        return {pygame.CONTROLLER_BUTTON_B,pygame.CONTROLLER_BUTTON_START,pygame.CONTROLLER_BUTTON_GUIDE,
                pygame.CONTROLLER_BUTTON_DPAD_UP,pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
                pygame.CONTROLLER_BUTTON_DPAD_DOWN,pygame.CONTROLLER_BUTTON_DPAD_LEFT}

    def bind_key(self,player,action,key):
        if key in RESERVED or key==pygame.K_UNKNOWN:
            return 'That key is reserved for menus or shared shortcuts.'
        for p,row in enumerate(self.keys):
            for i,current in enumerate(row):
                if current==key and (p,i)!=(player,action): return 'That key is already assigned. Choose another key.'
        self.keys[player][action]=key
        self.store.set('key_bindings31',self.keys)
        return ''

    def bind_button(self,action,button):
        if button in self.reserved_buttons(): return 'D-pad, B, Start and Guide stay available for navigation.'
        if button==self.pad_buttons[1-action]: return 'That button is already assigned to the other action.'
        self.pad_buttons[action]=button
        self.store.set('pad_buttons31',self.pad_buttons)
        return ''

    def reset(self):
        self.keys=[list(row) for row in DEFAULT_KEYS]
        self.pad_buttons=[pygame.CONTROLLER_BUTTON_A,pygame.CONTROLLER_BUTTON_X]
        self.store.set('key_bindings31',self.keys)
        self.store.set('pad_buttons31',self.pad_buttons)

    def key_name(self,player,action): return pygame.key.name(self.keys[player][action]).upper()

    @staticmethod
    def button_name(button):
        names={pygame.CONTROLLER_BUTTON_A:'CROSS / SOUTH',pygame.CONTROLLER_BUTTON_B:'CIRCLE / EAST',
               pygame.CONTROLLER_BUTTON_X:'SQUARE / WEST',pygame.CONTROLLER_BUTTON_Y:'TRIANGLE / NORTH',
               pygame.CONTROLLER_BUTTON_LEFTSHOULDER:'LEFT SHOULDER',pygame.CONTROLLER_BUTTON_RIGHTSHOULDER:'RIGHT SHOULDER',
               pygame.CONTROLLER_BUTTON_BACK:'BACK',pygame.CONTROLLER_BUTTON_LEFTSTICK:'LEFT STICK',
               pygame.CONTROLLER_BUTTON_RIGHTSTICK:'RIGHT STICK'}
        return names.get(button,f'BUTTON {button}')

    def key_command(self,key,coop):
        for p,row in enumerate(self.keys):
            if key in row: return (p if coop else 0,row.index(key))
        return None

    def held(self,keys,player,coop):
        rows=[self.keys[player]] if coop else self.keys if player==0 else []
        found=[]
        for row in rows:
            for k,d in zip(row[:4],DIRS):
                if keys[k] and d not in found: found.append(d)
        direction=self.pad_direction(player,coop)
        if direction and direction not in found: found.append(direction)
        return found

    def refresh(self,force=False):
        if not self.enabled: return False
        removed=False
        self.last_removed=[]
        for instance,(pad,slot) in list(self.pads.items()):
            try: attached=pad.attached()
            except pygame.error: attached=False
            if not attached:
                try: pad.quit()
                except pygame.error: pass
                joy=self.joysticks.pop(instance,None)
                if joy:
                    try: joy.quit()
                    except pygame.error: pass
                del self.pads[instance]; removed=True
                self.button_states.pop(instance,None)
                self.device_names.pop(instance,None)
                self.last_removed.append(instance)
        used={slot for _,slot in self.pads.values()}
        try:
            count=pygame.joystick.get_count()
            if not (force or removed or count>len(self.pads)): return removed
            for index in range(count):
                joystick=pygame.joystick.Joystick(index)
                if not joystick.get_init(): joystick.init()
                instance=joystick.get_instance_id()
                if instance in self.pads or len(used)>=2: continue
                slot=next(i for i in (0,1) if i not in used)
                mapped=bool(sdl_controller and sdl_controller.is_controller(index))
                pad=sdl_controller.Controller(index) if mapped else RawPad(joystick)
                self.pads[instance]=(pad,slot)
                self.joysticks[instance]=joystick
                self.device_names[instance]=joystick.get_name() or 'Controller'
                self.button_states[instance]={b for b in range(15) if pad.get_button(b)}
                used.add(slot)
        except pygame.error:
            pass
        return removed

    def poll_events(self):
        """Return safe edge events without converting SDL controller events."""
        if not self.enabled:return []
        removed=self.refresh()
        events=[pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED,instance_id=i) for i in self.last_removed]
        for instance,(pad,_) in list(self.pads.items()):
            try: pressed={b for b in range(15) if pad.get_button(b)}
            except pygame.error: continue
            before=self.button_states.get(instance,set())
            for button in sorted(pressed-before):
                events.append(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN,instance_id=instance,button=button))
                self.last_input=f'Controller {self.pads[instance][1]+1}: {self.button_name(button)}'
            direction=self._pad_direction(pad)
            if direction:
                words={(0,-1):'UP',(1,0):'RIGHT',(0,1):'DOWN',(-1,0):'LEFT'}
                self.last_input=f'Controller {self.pads[instance][1]+1}: stick {words[direction]}'
            self.button_states[instance]=pressed
        return events

    def player_for(self,instance,coop):
        if instance not in self.pads: return None
        return (self.first_player if self.pads[instance][1]==0 else 1-self.first_player) if coop else 0

    def pad_direction(self,player,coop):
        for instance,(pad,_) in self.pads.items():
            if self.player_for(instance,coop)!=player: continue
            try:
                direction=self._pad_direction(pad)
                if direction: return direction
            except pygame.error: continue
        return None

    def _pad_direction(self,pad):
        for button,direction in zip((pygame.CONTROLLER_BUTTON_DPAD_UP,pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
                                     pygame.CONTROLLER_BUTTON_DPAD_DOWN,pygame.CONTROLLER_BUTTON_DPAD_LEFT),DIRS):
            if pad.get_button(button): return direction
        return stick_direction(pad.get_axis(pygame.CONTROLLER_AXIS_LEFTX)/32768,
                               pad.get_axis(pygame.CONTROLLER_AXIS_LEFTY)/32768,self.deadzone)

    def close(self):
        for pad,_ in self.pads.values():
            try: pad.quit()
            except pygame.error: pass
        self.pads.clear()
        for joy in self.joysticks.values():
            try: joy.quit()
            except pygame.error: pass
        self.joysticks.clear()
        self.button_states.clear();self.device_names.clear();self.last_removed=[]


class ControlUI:
    def init_controls(self):
        self.controls=Controls(self.store)
        self.binding=None
        self.binding_notice='Click a key or gamepad action to change it. Esc cancels.'

    def controls_action(self,action):
        if action=='controls':
            self.navigation.append((self.screen,self.return_screen))
            self.return_screen=self.screen
            self.screen='controls'
        elif action.startswith('bind:'):
            _,player,index=action.split(':')
            self.binding=('key',int(player),int(index))
            self.binding_notice='Press the replacement key. Esc cancels.'
        elif action.startswith('padbind:'):
            self.binding=('pad',int(action.split(':')[1]))
            self.binding_notice='Press a gamepad button for this action. Esc cancels.'
        elif action=='reset_controls':
            self.controls.reset(); self.binding=None; self.binding_notice='Default controls restored.'
        elif action=='pad_player':
            self.controls.first_player=1-self.controls.first_player
            self.store.set('first_pad31',self.controls.first_player)
        elif action=='deadzone':
            values=(.2,.3,.4)
            self.controls.deadzone=values[(values.index(self.controls.deadzone)+1)%3]
            self.store.set('stick_deadzone31',self.controls.deadzone)
        else: return False
        return True

    def control_event(self,event):
        if event.type in (pygame.CONTROLLERDEVICEADDED,pygame.CONTROLLERDEVICEREMOVED,pygame.CONTROLLERDEVICEREMAPPED):
            removed=self.controls.refresh()
            if (removed or event.type==pygame.CONTROLLERDEVICEREMOVED) and self.screen=='play':
                self.action('pause')
                self.game.notify('Controller disconnected. Reconnect it or continue with the keyboard.')
            return True
        if self.screen=='controls' and self.binding:
            error=None
            if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                self.binding=None; self.binding_notice='Binding cancelled.'; return True
            if self.binding[0]=='key' and event.type==pygame.KEYDOWN:
                error=self.controls.bind_key(self.binding[1],self.binding[2],event.key)
            elif self.binding[0]=='pad' and event.type==pygame.CONTROLLERBUTTONDOWN:
                error=self.controls.bind_button(self.binding[1],event.button)
            if error is not None:
                self.binding_notice=error or 'Binding saved.'
                if not error: self.binding=None
                return True
            if event.type in (pygame.KEYDOWN,pygame.CONTROLLERBUTTONDOWN): return True
        if event.type!=pygame.CONTROLLERBUTTONDOWN: return False
        if self.screen=='sanctuary' and event.button==self.controls.pad_buttons[1]:
            self.home_interact()
            return True
        if self.screen=='play':
            player=self.controls.player_for(event.instance_id,self.game.coop)
            if player is None: return True
            if event.button==pygame.CONTROLLER_BUTTON_BACK and self.game.coop and event.button not in self.controls.pad_buttons:
                self.action('ping:'+str(player))
            elif event.button==pygame.CONTROLLER_BUTTON_START: self.action('pause')
            elif event.button==self.controls.pad_buttons[0]:
                (self.game.escape_partner if player else self.game.escape)(); self.consume_events()
            elif event.button==self.controls.pad_buttons[1]:
                self.game.interact(partner=bool(player)); self.consume_events()
        elif event.button==pygame.CONTROLLER_BUTTON_A:
            if self.buttons:
                index=self.focus if 0<=self.focus<len(self.buttons) else 0
                self.action(self.buttons[index][1])
        elif event.button==pygame.CONTROLLER_BUTTON_START and self.screen=='paused': self.action('resume')
        elif event.button==pygame.CONTROLLER_BUTTON_B:
            if self.screen=='paused': self.action('resume')
            elif self.screen in ('adventure','controls','journal','settings','help','records','challenge','sanctuary','story','biome_guide','accessibility','object_info','ending','home_activities','home_hub','challenge_hall','profile','records','contract_collection','garden_collection','reward_room','completion_film','run_insights','support','team_journal'): self.action('back')
        elif event.button in (pygame.CONTROLLER_BUTTON_DPAD_DOWN,pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
                               pygame.CONTROLLER_BUTTON_DPAD_UP,pygame.CONTROLLER_BUTTON_DPAD_LEFT):
            step=1 if event.button in (pygame.CONTROLLER_BUTTON_DPAD_DOWN,pygame.CONTROLLER_BUTTON_DPAD_RIGHT) else -1
            self.focus=(self.focus+step)%max(1,len(self.buttons))
        return True

    def draw_controls(self):
        self.header('Choose how you play.', 'Keyboard, DualSense and compatible gamepads. Bindings are saved on this computer.')
        for player in range(2):
            x=44+player*602
            self.text(f'PLAYER {player+1}',(x+18,142),15,(177,225,153),bold=True)
            for index,label in enumerate(('Move up','Move right','Move down','Move left','Escape ability','Interact / ledge')):
                y=174+index*57
                self.panel((x,y,584,50),radius=9)
                self.text(label,(x+18,y+14),18)
                self.button(self.controls.key_name(player,index),(x+305,y+7,258,36),f'bind:{player}:{index}',small=True)
        self.text(self.binding_notice,(48,529),15,(247,203,118))
        names=', '.join(dict.fromkeys(self.controls.device_names.values()))
        label=f'{len(self.controls.pads)} controller(s) connected'+(f': {names}' if names else '')
        self.text(label+'. D-pad / left stick moves; Start pauses.',(48,563),15,(153,176,166))
        self.button('Ability: '+self.controls.button_name(self.controls.pad_buttons[0]),(48,594,370,43),'padbind:0',small=True)
        self.button('Interact: '+self.controls.button_name(self.controls.pad_buttons[1]),(432,594,370,43),'padbind:1',small=True)
        self.button(f'First pad: player {self.controls.first_player+1}',(816,594,416,43),'pad_player',small=True)
        self.button(f'Stick deadzone: {int(self.controls.deadzone*100)}%',(48,654,370,43),'deadzone',small=True)
        self.text('Solo accepts either keyboard set. Co-op uses separate sets; the second pad uses the other player.',(48,715),14,(153,176,166))
        self.text('INPUT TEST: '+self.controls.last_input,(48,741),14,(247,203,118))
        self.button('Back',(48,766,170,44),'back')
        self.button('Reset bindings',(978,766,254,44),'reset_controls')
