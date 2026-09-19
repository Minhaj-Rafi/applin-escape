"""Game rules and persistence, independent of the graphics/audio layer."""
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import secrets
import sqlite3

DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))


@dataclass(frozen=True)
class Difficulty:
    name: str
    biome: str
    width: int
    height: int
    enemies: int
    enemy_delay: float
    escapes: int
    hearts: int
    seeds: int
    detection: int
    patrol_seconds: float
    color: tuple


TIERS = (
    Difficulty('BREEZY', 'Bramblebrook Orchard', 21, 17, 1, .28, 3, 3, 3, 12, 4, (129, 221, 167)),
    Difficulty('WATCHFUL', 'Tideglass Wetlands', 25, 19, 2, .23, 2, 3, 4, 16, 3, (94, 210, 195)),
    Difficulty('DARING', 'Bellfern Shrine', 29, 21, 3, .19, 2, 3, 5, 20, 2.5, (239, 184, 106)),
    Difficulty('RELENTLESS', 'Copperleaf Ruins', 33, 23, 4, .17, 1, 2, 6, 24, 2, (179, 159, 242)),
    Difficulty('APEX', 'Starfall Highlands', 37, 25, 5, .155, 1, 2, 7, 30, 1.5, (123, 181, 251)),
)


def default_save_dir():
    base = Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local' / 'share'))
    return base / 'ApplinEscape'


class Store:
    """Local SQLite transactions protect history and run records across launches."""
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory else default_save_dir()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / 'progress.sqlite3')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS mazes (
                fingerprint TEXT PRIMARY KEY, layout TEXT UNIQUE NOT NULL,
                seed TEXT NOT NULL, tier INTEGER NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY, created TEXT NOT NULL, tier INTEGER,
                outcome TEXT, seconds REAL, steps INTEGER, escapes INTEGER,
                hits INTEGER, score INTEGER, fingerprint TEXT, mode TEXT);
            CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value TEXT);
        ''')
        self.db.commit()

    def claim(self, layout, seed, tier):
        digest = hashlib.sha256(layout.encode()).hexdigest()
        try:
            with self.db:
                self.db.execute('INSERT INTO mazes VALUES (?, ?, ?, ?, ?)',
                                (digest, layout, str(seed), tier, datetime.now(timezone.utc).isoformat()))
            return digest
        except sqlite3.IntegrityError:
            return None

    def record(self, game, outcome):
        with self.db:
            self.db.execute('INSERT INTO runs VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (datetime.now(timezone.utc).isoformat(), game.tier, outcome,
                             game.elapsed, game.steps, game.escapes_used, game.hits,
                             game.score, game.fingerprint, game.mode))

    def get(self, key, default):
        row = self.db.execute('SELECT value FROM settings WHERE name=?', (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row[0])
        except (ValueError, TypeError):
            return default

    def set(self, key, value):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO settings VALUES (?, ?)', (key, json.dumps(value)))

    def records(self):
        return self.db.execute('SELECT tier, outcome, seconds, steps, escapes, score FROM runs ORDER BY id DESC LIMIT 8').fetchall()

    def summary(self):
        count = self.db.execute('SELECT COUNT(*) FROM mazes').fetchone()[0]
        wins, score = self.db.execute("SELECT COUNT(*), COALESCE(MAX(score),0) FROM runs WHERE outcome='cleared'").fetchone()
        return count, wins, score

    def close(self):
        self.db.close()


def neighbors(grid, cell):
    x, y = cell
    for dx, dy in DIRS:
        nx, ny = x + dx, y + dy
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == 0:
            yield nx, ny


def distances(grid, starts):
    found = {cell: 0 for cell in starts}
    queue = deque(found)
    while queue:
        cell = queue.popleft()
        for nxt in neighbors(grid, cell):
            if nxt not in found:
                found[nxt] = found[cell] + 1
                queue.append(nxt)
    return found


def path_to(grid, start, goal):
    parents = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            route = []
            while cell is not None:
                route.append(cell)
                cell = parents[cell]
            return route[::-1]
        for nxt in neighbors(grid, cell):
            if nxt not in parents:
                parents[nxt] = cell
                queue.append(nxt)
    return []


def water_channel(tier, x, y, width, height):
    if tier == 1:
        return abs(x-(width*.52+math.sin(y*.37)*3)) < 2.4 or (x > width*.78 and y > height*.58)
    if tier == 2:
        return x > width*.72 and y < height*.30
    if tier == 4:
        return abs(y-(height*.58+math.sin(x*.32)*2)) < 1.3
    return False


def carve_clearings(grid, tier, rng):
    """Connect small route clearings to existing paths, preserving reachability."""
    width, height = len(grid[0]), len(grid)
    centers = [(x,y) for y in range(3,height-3,2) for x in range(3,width-3,2) if not grid[y][x]]
    rng.shuffle(centers)
    for x,y in centers[:(3,4,3,5,4)[tier]]:
        rx, ry = ((2,1),(1,2),(2,2),(2,1),(1,2))[tier]
        for cy in range(max(1,y-ry),min(height-1,y+ry+1)):
            for cx in range(max(1,x-rx),min(width-1,x+rx+1)):
                grid[cy][cx] = 0
    return grid


ROSTERS = (
    ('Pidgeotto',),
    ('Cramorant', 'Spearow'),
    ('Murkrow', 'Pidgeotto', 'Spearow'),
    ('Talonflame', 'Murkrow', 'Pidgeotto', 'Cramorant'),
    ('Talonflame', 'Murkrow', 'Spearow', 'Pidgeotto', 'Cramorant'),
)
SPECIES_ROLES = {'Pidgeotto':'TRACKER', 'Cramorant':'WARDEN', 'Spearow':'AMBUSHER', 'Murkrow':'ROAMER', 'Talonflame':'TRACKER'}


def canonical_layout(grid):
    """Treat mirrored and rotated copies as repeats, including rectangular maps."""
    variations = []
    current = grid
    for _ in range(4):
        for candidate in (current, [list(reversed(row)) for row in current]):
            variations.append(f'{len(candidate[0])}x{len(candidate)}:' +
                              ''.join(''.join(map(str, row)) for row in candidate))
        current = [list(row) for row in zip(*current[::-1])]
    return min(variations)


def generate(width, height, rng):
    """Randomized DFS plus braided corridors: always connected, with escape loops."""
    grid = [[1] * width for _ in range(height)]
    grid[1][1] = 0
    stack = [(1, 1)]
    while stack:
        x, y = stack[-1]
        choices = [(x + dx * 2, y + dy * 2) for dx, dy in DIRS
                   if 0 < x + dx * 2 < width - 1 and 0 < y + dy * 2 < height - 1
                   and grid[y + dy * 2][x + dx * 2]]
        if not choices:
            stack.pop()
            continue
        nx, ny = rng.choice(choices)
        grid[(ny + y) // 2][(nx + x) // 2] = 0
        grid[ny][nx] = 0
        stack.append((nx, ny))
    # Break most dead ends to allow circling around pursuers.
    rooms = [(x, y) for y in range(1, height - 1, 2) for x in range(1, width - 1, 2)]
    rng.shuffle(rooms)
    for x, y in rooms:
        if len(list(neighbors(grid, (x, y)))) == 1 and rng.random() < .82:
            walls = [(x + dx, y + dy) for dx, dy in DIRS
                     if 0 < x + dx * 2 < width - 1 and 0 < y + dy * 2 < height - 1
                     and grid[y + dy][x + dx]]
            if walls:
                nx, ny = rng.choice(walls)
                grid[ny][nx] = 0
    return grid


@dataclass
class Enemy:
    pos: tuple
    spawn: tuple
    role: str
    target: tuple
    delay: float
    timer: float = 0
    stunned: float = 0
    direction: tuple = (1, 0)
    mood: str = 'patrol'
    species: str = 'Cramorant'


class Session:
    PLAYER_DELAY = .135

    def __init__(self, store, tier=0, mode='practice', seed_source=None):
        self.store, self.tier, self.mode = store, tier, mode
        self.config = TIERS[tier]
        self.rng = random.Random()
        for _ in range(256):
            self.seed = seed_source() if seed_source else secrets.randbits(64)
            self.rng.seed(self.seed)
            self.grid = carve_clearings(generate(self.config.width, self.config.height, self.rng), tier, self.rng)
            self.fingerprint = store.claim(canonical_layout(self.grid), self.seed, tier)
            if self.fingerprint:
                break
        else:
            raise RuntimeError('Could not create an unseen maze. Your history has been preserved.')
        self.player = (1, 1)
        self.direction = (1, 0)
        start_dist = distances(self.grid, [self.player])
        self.floors = list(start_dist)
        self.hidden_cells = {p for p in self.floors if len(list(neighbors(self.grid,p))) >= 3 and (p[0]*7+p[1]*3)%4
                             and not water_channel(tier,*p,self.config.width,self.config.height)}
        self.exit = max(self.floors, key=start_dist.get)
        available = [p for p in self.floors if start_dist[p] > 7 and p != self.exit]
        self.seeds = set()
        # Spread the objectives across the maze, instead of clustering randomly.
        chosen = [self.player, self.exit]
        for _ in range(self.config.seeds):
            separation = distances(self.grid, chosen)
            top = sorted(available, key=lambda p: separation[p], reverse=True)[:max(4, len(available) // 8)]
            cell = self.rng.choice(top)
            available.remove(cell)
            chosen.append(cell)
            self.seeds.add(cell)
        self.enemies = []
        for i in range(self.config.enemies):
            candidates = [p for p in available if start_dist[p] >= 16]
            cell = self.rng.choice(candidates or available)
            available.remove(cell)
            species = ROSTERS[tier][i]
            speed = self.config.enemy_delay + i*.012
            if species == 'Talonflame':
                speed *= .90
            self.enemies.append(Enemy(cell, cell, SPECIES_ROLES[species], self.rng.choice(self.floors), speed,
                                      timer=1.8+i*.3, species=species))
        remaining = [p for p in available if p not in self.seeds]
        self.rng.shuffle(remaining)
        self.berries = set(remaining[:3])
        self.dew = set(remaining[3::3])
        self.initial_dew = len(self.dew)
        self.health = self.config.hearts
        self.escapes = self.config.escapes
        self.escapes_used = self.hits = self.steps = self.dew_collected = 0
        self.elapsed = 0.0
        self.state = 'playing'
        self.invulnerable = 2.2
        self.slow_time = self.escape_cooldown = self.decoy_time = 0.0
        self.decoy = self.player
        self.visited = {self.player}
        self.events = []
        self.score = 0
        self.recorded = False
        self.notice = 'Collect the sun seeds. Reach the sanctuary gate.'
        self.notice_time = 5.0

    def notify(self, message):
        self.notice, self.notice_time = message, 4.0

    def finish(self, outcome):
        if self.recorded:
            return
        self.state = outcome
        if outcome == 'cleared':
            self.score += max(0, 1800 - int(self.elapsed) * 3) + self.health * 250 + self.escapes * 150
        self.store.record(self, outcome)
        self.recorded = True
        self.events.append((outcome, self.player))

    def abandon(self):
        if not self.recorded:
            self.finish('abandoned')

    def collect(self):
        if self.player in self.seeds:
            self.seeds.remove(self.player)
            self.score += 500
            self.events.append(('seed', self.player))
            self.notify('Sanctuary unlocked! Follow the exit marker.' if not self.seeds else 'Sun seed rescued. Keep going!')
        if self.player in self.dew:
            self.dew.remove(self.player)
            self.dew_collected += 1
            self.score += 10
            self.events.append(('dew', self.player))
        if self.player in self.berries:
            self.berries.remove(self.player)
            self.slow_time = 6.0
            self.score += 75
            self.events.append(('berry', self.player))
            self.notify('Chill berry! The flock slows down for 6 seconds.')
        if self.player == self.exit:
            if self.seeds:
                self.notify(f'Gate locked: {len(self.seeds)} sun seeds still out there.')
            else:
                self.finish('cleared')

    def collision(self):
        if self.invulnerable > 0 or self.state != 'playing':
            return False
        if any(e.pos == self.player and e.stunned <= 0 for e in self.enemies):
            self.health -= 1
            self.hits += 1
            self.events.append(('hit', self.player))
            if self.health <= 0:
                self.finish('caught')
            else:
                self.player = (1, 1)
                self.invulnerable = 3.0
                for enemy in self.enemies:
                    enemy.pos = enemy.spawn
                    enemy.timer = 1.6
                self.notify('Close call! Back at the nest with a short safety shield.')
                self.events.append(('respawn', self.player))
            return True
        return False

    def move(self, direction):
        if self.state != 'playing':
            return False
        nxt = (self.player[0] + direction[0], self.player[1] + direction[1])
        if nxt not in neighbors(self.grid, self.player):
            return False
        self.direction = direction
        self.player = nxt
        self.steps += 1
        self.visited.add(nxt)
        if not self.collision():
            self.collect()
        return True

    def escape(self):
        """Leaf Slip: hop to a safer floor cell, leave a decoy, gain a shield."""
        if self.state != 'playing':
            return False
        if self.escapes <= 0:
            self.notify('No Leaf Slips left. Use loops and chill berries!')
            return False
        if self.escape_cooldown > 0:
            self.notify('Leaf Slip is cooling down.')
            return False
        player_dist = distances(self.grid, [self.player])
        threat_dist = distances(self.grid, [e.pos for e in self.enemies])
        candidates = [p for p in self.floors if 5 <= player_dist[p] <= 14 and threat_dist.get(p, 999) >= 5]
        if not candidates:
            candidates = [p for p in self.floors if player_dist[p] >= 5 and threat_dist.get(p, 999) >= 3]
        if not candidates:
            self.notify('No safe landing found. Charge preserved.')
            return False
        target = max(candidates, key=lambda p: (min(threat_dist.get(p, 999), 18), -player_dist[p]))
        old = self.player
        for enemy in self.enemies:
            if player_dist[enemy.pos] <= 7:
                enemy.stunned = 2.0
        self.player = target
        self.visited.add(target)
        self.escapes -= 1
        self.escapes_used += 1
        self.escape_cooldown = 1.5
        self.invulnerable = 2.0
        self.decoy, self.decoy_time = old, 3.5
        self.events.extend([('escape', old), ('land', target)])
        self.notify('Leaf Slip! Safe landing, decoy and a 2-second shield.')
        self.collect()
        return True

    def enemy_target(self, enemy, player_dist):
        if self.decoy_time > 0:
            enemy.mood = 'decoy'
            return self.decoy
        cycle = self.elapsed % (self.config.patrol_seconds + 14)
        detection = max(3,self.config.detection//2) if self.player in self.hidden_cells else self.config.detection
        aware = player_dist.get(enemy.pos, 999) <= detection
        if cycle < self.config.patrol_seconds or not aware:
            enemy.mood = 'patrol'
            if enemy.pos == enemy.target:
                enemy.target = self.rng.choice(self.floors)
            return enemy.target
        enemy.mood = 'chase'
        if enemy.role == 'AMBUSHER':
            target = self.player
            for _ in range(4):
                nxt = (target[0] + self.direction[0], target[1] + self.direction[1])
                if nxt in neighbors(self.grid, target):
                    target = nxt
                else:
                    break
            return target
        if enemy.role == 'WARDEN' and player_dist[enemy.pos] > 5:
            goals = sorted(self.seeds) if self.seeds else [self.exit]
            return min(goals, key=lambda p: player_dist[p])
        if enemy.role == 'ROAMER' and self.rng.random() < .4:
            return enemy.target
        return self.player

    def update(self, dt):
        if self.state != 'playing':
            return
        self.elapsed += dt
        for attr in ('invulnerable', 'slow_time', 'escape_cooldown', 'decoy_time', 'notice_time'):
            setattr(self, attr, max(0, getattr(self, attr) - dt))
        player_dist = distances(self.grid, [self.player])
        for enemy in self.enemies:
            enemy.stunned = max(0, enemy.stunned - dt)
            if enemy.stunned > 0:
                continue
            enemy.timer -= dt
            if enemy.timer > 0:
                continue
            enemy.timer = enemy.delay * (2.2 if self.slow_time > 0 else 1.0)
            target = self.enemy_target(enemy, player_dist)
            route = path_to(self.grid, enemy.pos, target)
            if len(route) > 1:
                nxt = route[1]
                if not any(other is not enemy and other.pos == nxt for other in self.enemies):
                    enemy.direction = (nxt[0] - enemy.pos[0], nxt[1] - enemy.pos[1])
                    enemy.pos = nxt
                else:
                    # Avoid a permanent two-bird corridor deadlock.
                    alternatives = [p for p in neighbors(self.grid, enemy.pos)
                                    if not any(other is not enemy and other.pos == p for other in self.enemies)]
                    if alternatives:
                        nxt = self.rng.choice(alternatives)
                        enemy.direction = (nxt[0] - enemy.pos[0], nxt[1] - enemy.pos[1])
                        enemy.pos = nxt
            if self.collision():
                break
