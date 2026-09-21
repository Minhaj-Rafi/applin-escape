"""Saved keyboard bindings and SDL-mapped gamepads; no device-specific button guesses."""
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
        self.enabled=False
        if sdl_controller:
            try:
                sdl_controller.init(); self.enabled=True; self.refresh()
            except pygame.error: pass

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
        names={pygame.CONTROLLER_BUTTON_A:'A / SOUTH',pygame.CONTROLLER_BUTTON_B:'B / EAST',
               pygame.CONTROLLER_BUTTON_X:'X / WEST',pygame.CONTROLLER_BUTTON_Y:'Y / NORTH',
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

    def refresh(self):
        if not self.enabled: return False
        removed=False
        for instance,(pad,slot) in list(self.pads.items()):
            if not pad.attached():
                pad.quit(); del self.pads[instance]; removed=True
        used={slot for _,slot in self.pads.values()}
        try:
            for index in range(sdl_controller.get_count()):
                if not sdl_controller.is_controller(index): continue
                joystick=pygame.joystick.Joystick(index)
                instance=joystick.get_instance_id()
                if instance in self.pads or len(used)>=2: continue
                slot=next(i for i in (0,1) if i not in used)
                self.pads[instance]=(sdl_controller.Controller(index),slot)
                used.add(slot)
        except pygame.error:
            pass
        return removed

    def player_for(self,instance,coop):
        if instance not in self.pads: return None
        return (self.first_player if self.pads[instance][1]==0 else 1-self.first_player) if coop else 0

    def pad_direction(self,player,coop):
        for instance,(pad,_) in self.pads.items():
            if self.player_for(instance,coop)!=player: continue
            try:
                for button,direction in zip((pygame.CONTROLLER_BUTTON_DPAD_UP,pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
                                            pygame.CONTROLLER_BUTTON_DPAD_DOWN,pygame.CONTROLLER_BUTTON_DPAD_LEFT),DIRS):
                    if pad.get_button(button): return direction
                direction=stick_direction(pad.get_axis(pygame.CONTROLLER_AXIS_LEFTX)/32768,
                                          pad.get_axis(pygame.CONTROLLER_AXIS_LEFTY)/32768,self.deadzone)
                if direction: return direction
            except pygame.error: continue
        return None

    def close(self):
        for pad,_ in self.pads.values():
            try: pad.quit()
            except pygame.error: pass
        self.pads.clear()


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
            elif self.screen in ('adventure','controls','journal','settings','help','records','challenge','sanctuary','story','biome_guide','accessibility','object_info','ending','home_activities','home_hub','challenge_hall','profile','records','contract_collection'): self.action('back')
        elif event.button in (pygame.CONTROLLER_BUTTON_DPAD_DOWN,pygame.CONTROLLER_BUTTON_DPAD_RIGHT,
                               pygame.CONTROLLER_BUTTON_DPAD_UP,pygame.CONTROLLER_BUTTON_DPAD_LEFT):
            step=1 if event.button in (pygame.CONTROLLER_BUTTON_DPAD_DOWN,pygame.CONTROLLER_BUTTON_DPAD_RIGHT) else -1
            self.focus=(self.focus+step)%max(1,len(self.buttons))
        return True

    def draw_controls(self):
        self.header('Choose how you play.', 'Keyboard and SDL-mapped gamepads. Bindings are saved on this computer.')
        for player in range(2):
            x=44+player*602
            self.text(f'PLAYER {player+1}',(x+18,142),15,(177,225,153),bold=True)
            for index,label in enumerate(('Move up','Move right','Move down','Move left','Escape ability','Interact / ledge')):
                y=174+index*57
                self.panel((x,y,584,50),radius=9)
                self.text(label,(x+18,y+14),18)
                self.button(self.controls.key_name(player,index),(x+305,y+7,258,36),f'bind:{player}:{index}',small=True)
        self.text(self.binding_notice,(48,529),15,(247,203,118))
        self.text(f'{len(self.controls.pads)} supported controller(s) connected. D-pad / left stick moves; Start pauses.',(48,563),15,(153,176,166))
        self.button('Ability: '+self.controls.button_name(self.controls.pad_buttons[0]),(48,594,370,43),'padbind:0',small=True)
        self.button('Interact: '+self.controls.button_name(self.controls.pad_buttons[1]),(432,594,370,43),'padbind:1',small=True)
        self.button(f'First pad: player {self.controls.first_player+1}',(816,594,416,43),'pad_player',small=True)
        self.button(f'Stick deadzone: {int(self.controls.deadzone*100)}%',(48,654,370,43),'deadzone',small=True)
        self.text('Solo accepts either keyboard set. Co-op uses separate sets; the second pad uses the other player.',(48,715),14,(153,176,166))
        self.button('Back',(48,766,170,44),'back')
        self.button('Reset bindings',(978,766,254,44),'reset_controls')
