"""Touch controls and nearby two-device co-op screens."""
from __future__ import annotations

import queue
import threading
import time
import base64
import json
import zlib

import pygame

from expedition import Session
from mobile_platform import is_android, request_nearby_permissions, safe_insets, screen_density
from network_coop import (BluetoothClient, BluetoothHost, LanClient, LanHost,
                          android_bluetooth_available, bonded_bluetooth_devices,
                          discover_lan)

TEXT = (243, 237, 216)
MUTED = (153, 176, 166)
GREEN = (177, 225, 153)
GOLD = (247, 203, 118)
RED = (239, 143, 133)
W, H = 1280, 840  # logical canvas size, matching main.py


class TouchPad:
    """Large controls laid out in physical units on the real window.

    Wide phones get the buttons in the space beside the game picture; narrower
    phones and tablets get the same physical size floating over its corners.
    """
    PAD_DP = 48       # one arrow; Android's recommended minimum touch target
    USE_DP = 60
    ESCAPE_DP = 72
    PAUSE_DP = 48
    MARGIN_DP = 10
    MIN_SIDE_SCALE = .85  # side columns may shrink the game picture by at most 15%

    def __init__(self, enabled=False):
        self.enabled = enabled
        self.held = {}
        self._cache_key = None
        self._layout = None
        self._sprites = {}

    def active(self, app):
        return self.enabled and app.screen == "play"

    def direction(self):
        return next(iter(self.held.values()), None)

    @classmethod
    def build_layout(cls, width, height, dp, insets=(0, 0, 0, 0)):
        """Window-pixel rects for every control plus the area left for the game."""
        inset_l, inset_t, inset_r, inset_b = insets
        pad, use, esc, pause, margin = (max(1, round(size*dp)) for size in
                                        (cls.PAD_DP, cls.USE_DP, cls.ESCAPE_DP, cls.PAUSE_DP, cls.MARGIN_DP))
        column = margin*2 + max(pad*3, esc)
        side_l, side_r = inset_l + column, inset_r + column
        full_scale = min(width/W, height/H)
        side_scale = min((width-side_l-side_r)/W, height/H) if width > side_l+side_r else 0
        sidebars = side_scale >= full_scale*cls.MIN_SIDE_SCALE
        if sidebars:
            area = pygame.Rect(side_l, 0, width-side_l-side_r, height)
        else:
            # Push the picture to the top right so any spare space collects under
            # the arrows at the bottom left, where they would otherwise cover the maze.
            fit_w, fit_h = int(W*full_scale), int(H*full_scale)
            area = pygame.Rect(width-inset_r-fit_w, inset_t, fit_w, fit_h)
            if area.x < 0 or area.bottom > height:
                area = pygame.Rect(0, 0, width, height)

        bottom = height - inset_b - margin*(3 if sidebars else 1)
        left = inset_l + margin
        if sidebars:
            left = inset_l + (column - pad*3)//2
        directions = {
            "up": (pygame.Rect(left+pad, bottom-pad*3, pad, pad), (0, -1)),
            "left": (pygame.Rect(left, bottom-pad*2, pad, pad), (-1, 0)),
            "right": (pygame.Rect(left+pad*2, bottom-pad*2, pad, pad), (1, 0)),
            "down": (pygame.Rect(left+pad, bottom-pad, pad, pad), (0, 1)),
        }
        right = width - inset_r - margin
        if sidebars:
            right = width - inset_r - (column - esc)//2
        escape = pygame.Rect(right-esc, bottom-esc, esc, esc)
        if sidebars:
            interact = pygame.Rect(escape.centerx-use//2, escape.y-margin-use, use, use)
        else:
            interact = pygame.Rect(escape.x-margin-use, bottom-use, use, use)
        actions = {
            "interact": interact,
            "escape": escape,
            "pause": pygame.Rect(width-inset_r-margin-pause, inset_t+margin, pause, pause),
        }
        return {"directions": directions, "actions": actions, "area": area,
                "sidebars": sidebars, "dp": dp}

    def layout(self, app):
        size = app.window.get_size()
        if size != self._cache_key:
            self._cache_key = size
            self._layout = self.build_layout(*size, screen_density(*size), safe_insets())
        return self._layout

    def canvas_area(self, app, width, height):
        """The window area the game picture is fitted into."""
        if self.active(app):
            return self.layout(app)["area"]
        return pygame.Rect(0, 0, width, height)

    def _point(self, app, event):
        if event.type in (pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION):
            width, height = app.window.get_size()
            return (event.x * width, event.y * height)
        return event.pos

    def _direction_at(self, layout, point):
        for rect, direction in layout["directions"].values():
            if rect.collidepoint(point):
                return direction
        return None

    def handle(self, app, event):
        if not self.active(app):
            return None
        downs = (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN)
        ups = (pygame.MOUSEBUTTONUP, pygame.FINGERUP)
        if event.type not in downs + ups + (pygame.FINGERMOTION,):
            return None
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and getattr(event, "button", 1) != 1:
            return None
        identity = getattr(event, "finger_id", "mouse")
        if event.type in ups:
            self.held.pop(identity, None)
            return "consumed"
        layout = self.layout(app)
        point = self._point(app, event)
        if event.type == pygame.FINGERMOTION:
            # Sliding a thumb across the arrows changes direction without lifting it.
            if identity not in self.held:
                return None
            direction = self._direction_at(layout, point)
            if direction and direction != self.held[identity]:
                self.held[identity] = direction
                return ("move", direction)
            return "consumed"
        direction = self._direction_at(layout, point)
        if direction:
            self.held[identity] = direction
            return ("move", direction)
        for name, rect in layout["actions"].items():
            if rect.collidepoint(point):
                return (name, None)
        return None

    def _sprite(self, app, name, size, active):
        key = name, size, active
        if key not in self._sprites:
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            rect = surface.get_rect()
            labels = {"up": "▲", "left": "◀", "down": "▼", "right": "▶",
                      "interact": "USE", "escape": "ESC", "pause": "Ⅱ"}
            if name in ("up", "left", "down", "right"):
                inner = rect.inflate(-4, -4)
                radius = max(6, size//4)
                pygame.draw.rect(surface, (177, 225, 153, 130 if active else 78), inner, border_radius=radius)
                pygame.draw.rect(surface, (243, 237, 216, 160), inner, 2, border_radius=radius)
                font = app.font(max(12, size*9//20), bold=True)
            else:
                color = (247, 203, 118, 115) if name == "escape" else (177, 225, 153, 95)
                pygame.draw.ellipse(surface, color, rect)
                pygame.draw.ellipse(surface, (243, 237, 216, 175), rect, 2)
                font = app.font(max(11, size*5//18), bold=True)
            label = font.render(labels[name], True, (14, 24, 27))
            surface.blit(label, label.get_rect(center=rect.center))
            self._sprites[key] = surface
        return self._sprites[key]

    def draw(self, app):
        """Draw onto the window, after the game picture has been scaled into place."""
        if not self.active(app):
            return
        layout = self.layout(app)
        for name, (rect, direction) in layout["directions"].items():
            active = direction in self.held.values()
            app.window.blit(self._sprite(app, name, rect.w, active), rect)
        for name, rect in layout["actions"].items():
            app.window.blit(self._sprite(app, name, rect.w, False), rect)


class MobileUI:
    def init_mobile(self):
        self.android = is_android()
        self.touch = TouchPad(self.android)
        self.remote = None
        self.remote_role = None
        self.remote_transport = None
        self.remote_status = "Choose how the two Android devices will connect."
        self.remote_code = ""
        self.remote_results = []
        self.remote_selected = None
        self.remote_search = None
        self.remote_last_sync = 0.0
        self.remote_touch_repeat = 0.0
        self.remote_last_revision = None
        self.remote_seen_connection = False
        self.remote_bt_devices = []
        self.remote_inbox = queue.Queue()
        if self.android:
            request_nearby_permissions()

    def _player_name(self):
        return self.store.get("player_name", "Orchard host") or "Orchard host"

    def _close_remote(self, keep_status=False):
        if self.remote_transport:
            self.remote_transport.close()
        self.remote_transport = None
        self.remote_role = None
        self.remote_selected = None
        self.remote_seen_connection = False
        if not keep_status:
            self.remote_status = "Nearby session closed."

    def mobile_action(self, action):
        if action == "nearby_coop":
            self.navigation.append((self.screen, self.return_screen))
            self.return_screen = self.screen
            self.screen = "nearby_coop"
            self.remote_status = "Use the same Wi-Fi, or pair both phones in Android Settings first."
            return True
        if action == "remote_back" or action == "back" and self.screen in ("nearby_coop", "remote_lobby", "remote_code"):
            self._close_remote()
            self.screen, self.return_screen = self.navigation.pop() if self.navigation else ("menu", "menu")
            return True
        if action == "wifi_host":
            self._close_remote(True)
            try:
                self.remote_transport = LanHost(self._player_name())
                self.remote_role = "host"
                self.screen = "remote_lobby"
                self.remote_status = self.remote_transport.status
            except OSError as exc:
                self.remote_status = "Could not host on Wi-Fi: " + str(exc)
            return True
        if action == "wifi_find":
            self.remote_results = []
            self.remote_status = "Looking for nearby games..."
            if not self.remote_search or not self.remote_search.is_alive():
                self.remote_search = threading.Thread(target=self._search_wifi, daemon=True)
                self.remote_search.start()
            return True
        if action.startswith("wifi_pick:"):
            index = int(action.split(":", 1)[1])
            if 0 <= index < len(self.remote_results):
                self.remote_selected = ("wifi", self.remote_results[index])
                self.remote_code = ""
                self.screen = "remote_code"
            return True
        if action == "bluetooth_host":
            self._close_remote(True)
            try:
                self.remote_transport = BluetoothHost(self._player_name())
                self.remote_role = "host"
                self.screen = "remote_lobby"
                self.remote_status = self.remote_transport.status
            except Exception as exc:
                self.remote_status = "Bluetooth host unavailable: " + str(exc)
            return True
        if action == "bluetooth_find":
            self.remote_bt_devices = bonded_bluetooth_devices()
            self.remote_status = ("Choose the host phone below."
                                  if self.remote_bt_devices else
                                  "No paired phones found. Pair them in Android Settings, then refresh.")
            return True
        if action.startswith("bluetooth_pick:"):
            index = int(action.split(":", 1)[1])
            if 0 <= index < len(self.remote_bt_devices):
                self.remote_selected = ("bluetooth", self.remote_bt_devices[index])
                self.remote_code = ""
                self.screen = "remote_code"
            return True
        if action.startswith("code_digit:"):
            if len(self.remote_code) < 4:
                self.remote_code += action.rsplit(":", 1)[1]
            return True
        if action == "code_delete":
            self.remote_code = self.remote_code[:-1]
            return True
        if action == "code_connect":
            if len(self.remote_code) != 4 or not self.remote_selected:
                self.remote_status = "Enter the four digits shown on the host phone."
                return True
            kind, choice = self.remote_selected
            self._close_remote(True)
            try:
                if kind == "wifi":
                    self.remote_transport = LanClient(choice["address"], choice["port"], self.remote_code)
                else:
                    self.remote_transport = BluetoothClient(choice["address"], self.remote_code)
                self.remote_role = "guest"
                self.screen = "remote_lobby"
                self.remote_status = self.remote_transport.status
            except Exception as exc:
                self.remote_status = "Could not connect: " + str(exc)
            return True
        if action == "remote_start":
            if self.remote_role == "host" and self.remote_transport and self.remote_transport.connected:
                self.coop = True
                self.campaign_results = []
                self.start(self.selected, "practice")
                self.remote_last_sync = 0
                self._send_remote_state(force_start=True)
            else:
                self.remote_status = "Player 2 must connect before the adventure starts."
            return True
        if action == "remote_campaign":
            if self.remote_role == "host" and self.remote_transport and self.remote_transport.connected:
                self.coop = True
                self.campaign_results = []
                self.start(0, "campaign")
                self.remote_last_sync = 0
                self._send_remote_state(force_start=True)
            else:
                self.remote_status = "Player 2 must connect before the expedition starts."
            return True
        if action == "remote_disconnect":
            self._close_remote()
            self.game = None
            self.screen = "menu"
            self.audio.set_biome(None)
            return True
        if self.remote_role == "host" and action in ("menu", "save_menu", "sanctuary", "end"):
            if self.remote_transport:
                self.remote_transport.send("session_end", reason="The host ended the nearby session.")
            self._close_remote(True)
            return False
        if self.remote_role == "guest" and action in ("pause", "resume", "escape", "end", "retry", "next", "menu", "sanctuary"):
            if action in ("pause", "resume", "escape") and self.remote_transport:
                self.remote_transport.send("command", action=action)
            return True
        if self.remote_role == "guest" and action.startswith("ping:"):
            if self.remote_transport:
                self.remote_transport.send("command", action="ping")
            return True
        return False

    def _search_wifi(self):
        try:
            self.remote_inbox.put(("discovery", discover_lan()))
        except OSError as exc:
            self.remote_inbox.put(("discovery_error", str(exc)))

    def mobile_event(self, event):
        result = self.touch.handle(self, event)
        if not result:
            return False
        if result == "consumed":
            return True
        command, value = result
        self._mobile_command(command, value)
        return True

    def _mobile_command(self, command, value=None):
        if self.screen != "play" or not self.game:
            return
        if self.remote_role == "guest":
            if self.remote_transport:
                payload = {"action": command}
                if value is not None:
                    payload["direction"] = list(value)
                self.remote_transport.send("command", **payload)
            return
        if command == "move":
            if self.move_timer <= 0:
                self.game.move(value)
                self.move_timer = Session.PLAYER_DELAY
        elif command == "escape":
            self.game.escape()
        elif command == "interact":
            self.game.interact()
        elif command == "pause":
            self.action("pause")
        self.consume_events()

    def _handle_host_command(self, message):
        if not self.game:
            return
        action = message.get("action")
        direction = tuple(message.get("direction", ()))
        if action == "move" and direction in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            if self.partner_timer <= 0:
                self.game.move_partner(direction)
                self.partner_timer = Session.PLAYER_DELAY
        elif action == "escape":
            self.game.escape_partner()
        elif action == "interact":
            self.game.interact(partner=True)
        elif action == "ping":
            self.action("ping:1")
        elif action == "pause" and self.screen == "play":
            self.action("pause")
        elif action == "resume" and self.screen == "paused":
            self.action("resume")
        self.consume_events()

    def _apply_remote_state(self, message):
        try:
            packed = base64.b64decode(message["snapshot"].encode("ascii"), validate=True)
            snapshot = json.loads(zlib.decompress(packed).decode("utf-8"))
            game = Session.restore(self.store, snapshot)
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError, zlib.error):
            self.remote_status = "The host sent an incompatible game state."
            return
        first = self.game is None or getattr(self.game, "stage_id", None) != game.stage_id
        revision = game.board_revision
        self.game = game
        self.screen = message.get("screen", "play")
        if self.screen not in ("play", "paused", "result"):
            self.screen = "play"
        if first:
            self.campaign_results = []
            self.audio.set_biome(game.tier)
            self.visual_player = list(map(float, game.player))
            self.visual_partner = list(map(float, game.partner["pos"]))
            self.visual_enemies = [list(map(float, e.pos)) for e in game.enemies]
            self.particles = []
            self.render_revision = revision
            self.prepare_board()
        elif revision != self.remote_last_revision:
            self.prepare_board()
        else:
            self.visual_player = list(map(float, game.player))
            self.visual_partner = list(map(float, game.partner["pos"]))
            self.visual_enemies = [list(map(float, e.pos)) for e in game.enemies]
        self.remote_last_revision = revision

    def _send_remote_state(self, force_start=False):
        if not self.remote_transport or not self.remote_transport.connected or not self.game:
            return
        raw = json.dumps(self.game.snapshot(), separators=(",", ":")).encode("utf-8")
        snapshot = base64.b64encode(zlib.compress(raw, 3)).decode("ascii")
        self.remote_transport.send("start" if force_start else "state",
                                   screen=self.screen, snapshot=snapshot)

    def mobile_update(self, dt):
        while True:
            try:
                kind, value = self.remote_inbox.get_nowait()
            except queue.Empty:
                break
            if kind == "discovery":
                self.remote_results = value
                self.remote_status = (f"Found {len(value)} nearby game(s)." if value else
                                      "No game found. Keep the host lobby open and use the same Wi-Fi.")
            else:
                self.remote_status = "Wi-Fi search failed: " + value
        transport = self.remote_transport
        if not transport:
            return False
        self.remote_status = transport.status
        if transport.connected:
            self.remote_seen_connection = True
        elif self.remote_seen_connection:
            transport.status = "The other device disconnected."
            self.remote_status = transport.status
            if self.screen == "play" and self.remote_role == "host":
                self.action("pause")
            elif self.remote_role == "guest" and self.screen in ("play", "paused", "result"):
                self.game = None
                self.screen = "remote_lobby"
            self.remote_seen_connection = False
        for message in transport.poll():
            kind = message.get("type")
            if kind == "accepted":
                transport.status = "Connected to " + str(message.get("host", "the host")) + ". Waiting to start."
                self.remote_status = transport.status
            elif kind == "rejected":
                transport.status = str(message.get("reason", "Connection rejected."))
                self.remote_status = transport.status
                transport.close()
            elif kind == "command" and self.remote_role == "host":
                self._handle_host_command(message)
            elif kind in ("start", "state") and self.remote_role == "guest":
                self._apply_remote_state(message)
            elif kind == "session_end" and self.remote_role == "guest":
                transport.status = str(message.get("reason", "The host ended the nearby session."))
                self.remote_status = transport.status
                self.game = None
                self.screen = "remote_lobby"
        now = time.monotonic()
        if self.remote_role == "guest" and self.screen == "play" and self.touch.direction() and now >= self.remote_touch_repeat:
            transport.send("command", action="move", direction=list(self.touch.direction()))
            self.remote_touch_repeat = now + Session.PLAYER_DELAY
        if self.remote_role == "host" and self.game and transport.connected and now-self.remote_last_sync >= .15:
            self.remote_last_sync = now
            self._send_remote_state()
        # A remote guest never advances enemies locally.
        return self.remote_role == "guest" and self.game is not None and self.screen in ("play", "paused", "result")

    def draw_mobile_screen(self):
        if self.screen == "nearby_coop":
            self.header("Nearby co-op", "Two Android devices. The host owns the maze; Player 2 joins nearby.")
            self.panel((48, 144, 560, 238))
            self.text("SAME WI-FI", (76, 169), 15, GREEN, bold=True)
            self.text("Automatic discovery; no IP address needed.", (76, 205), 17, MUTED)
            self.button("Host a Wi-Fi game", (76, 254, 238, 54), "wifi_host", True)
            self.button("Find Wi-Fi games", (330, 254, 238, 54), "wifi_find")
            self.panel((624, 144, 608, 238))
            self.text("BLUETOOTH", (652, 169), 15, GOLD, bold=True)
            self.text("Pair both phones in Android Settings first.", (652, 205), 17, MUTED)
            enabled = android_bluetooth_available()
            self.button("Host by Bluetooth" if enabled else "Bluetooth: Android only",
                        (652, 254, 254, 54), "bluetooth_host" if enabled else "none", enabled)
            self.button("Paired devices", (922, 254, 270, 54), "bluetooth_find")
            y = 418
            combined = [("wifi", item) for item in self.remote_results] + [("bluetooth", item) for item in self.remote_bt_devices]
            for index, (kind, item) in enumerate(combined[:4]):
                label = ("Wi-Fi: " if kind == "wifi" else "Bluetooth: ") + item["name"]
                action_index = self.remote_results.index(item) if kind == "wifi" else self.remote_bt_devices.index(item)
                action = f"{kind}_pick:{action_index}"
                self.button(label, (72, y+index*62, 1136, 48), action, small=True)
            self.text(self.remote_status, (64, 704), 16, GOLD if "No " in self.remote_status or "failed" in self.remote_status else MUTED)
            self.button("Back", (48, 766, 170, 44), "remote_back")
        elif self.screen == "remote_code":
            self.header("Enter the lobby code", "Type the four digits displayed on the host phone.")
            shown = "  ".join(self.remote_code + "_" * (4-len(self.remote_code)))
            self.panel((384, 142, 512, 112))
            self.text(shown, (640, 198), 48, GOLD, serif=True, center=True)
            for number in range(10):
                row, col = divmod(number, 5)
                self.button(str(number), (246+col*164, 304+row*88, 140, 66), f"code_digit:{number}")
            self.button("Delete", (328, 514, 296, 54), "code_delete")
            self.button("Connect", (656, 514, 296, 54), "code_connect", True)
            self.text(self.remote_status, (640, 628), 16, MUTED, center=True)
            self.button("Back", (48, 766, 170, 44), "remote_back")
        elif self.screen == "remote_lobby":
            role = "HOST" if self.remote_role == "host" else "PLAYER 2"
            self.header("Nearby lobby", role + " / keep this screen open until both devices are connected.")
            self.panel((176, 154, 928, 318))
            if self.remote_role == "host" and self.remote_transport:
                self.text("LOBBY CODE", (640, 190), 14, GREEN, bold=True, center=True)
                self.text(self.remote_transport.code, (640, 254), 62, GOLD, serif=True, center=True)
                self.text("Tell Player 2 these four digits.", (640, 315), 17, MUTED, center=True)
            else:
                self.text("PLAYER 2", (640, 220), 18, GREEN, bold=True, center=True)
                self.text("The host will choose the biome and start the run.", (640, 286), 20, TEXT, center=True)
            self.text(self.remote_status, (640, 404), 17, MUTED, center=True)
            if self.remote_role == "host":
                connected = bool(self.remote_transport and self.remote_transport.connected)
                self.button("Start selected biome" if connected else "Waiting for Player 2...",
                            (230, 520, 390, 58), "remote_start" if connected else "none", connected)
                self.button("Five-stage expedition", (660, 520, 390, 58),
                            "remote_campaign" if connected else "none")
                self.text(f"Biome {self.selected+1} / {self.skill} / {self.ability}", (640, 610), 16, MUTED, center=True)
            self.button("Cancel nearby session", (432, 714, 416, 48), "remote_back")

    def draw_mobile_overlay(self):
        if self.remote_role and self.screen == "play":
            label = "HOST • P1" if self.remote_role == "host" else "CONNECTED • P2"
            self.text(label, (945, 106), 12, GREEN, bold=True)

    def close_mobile(self):
        self._close_remote(True)
