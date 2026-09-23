"""Nearby two-device co-op transports.

The host owns the simulation.  A guest sends Player 2 commands and receives
authoritative snapshots, so timers and enemies cannot drift between phones.
"""
from __future__ import annotations

from collections import deque
import json
import queue
import secrets
import socket
import threading
import time

DISCOVERY_PORT = 38473
GAME_PORT = 38474
PROTOCOL = 1
SERVICE_UUID = "a6410bb1-5af2-4ac6-8e22-a4355b6881ad"


def _packet(kind, **values):
    return json.dumps({"protocol": PROTOCOL, "type": kind, **values},
                      separators=(",", ":"), ensure_ascii=True)


class SocketPeer:
    """Newline-delimited JSON over one TCP socket."""
    def __init__(self, connection):
        self.connection = connection
        self.connection.settimeout(.25)
        self.inbox = queue.Queue()
        self.alive = True
        self._send_lock = threading.Lock()
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()

    def _read(self):
        pending = b""
        try:
            while self.alive:
                try:
                    block = self.connection.recv(65536)
                except socket.timeout:
                    continue
                if not block:
                    break
                pending += block
                while b"\n" in pending:
                    raw, pending = pending.split(b"\n", 1)
                    if not raw:
                        continue
                    try:
                        value = json.loads(raw.decode("utf-8"))
                        if value.get("protocol") == PROTOCOL:
                            self.inbox.put(value)
                    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                        continue
        except OSError:
            pass
        self.alive = False

    def send(self, kind, **values):
        if not self.alive:
            return False
        try:
            data = (_packet(kind, **values) + "\n").encode("utf-8")
            with self._send_lock:
                self.connection.sendall(data)
            return True
        except OSError:
            self.alive = False
            return False

    def poll(self):
        found = []
        while True:
            try:
                found.append(self.inbox.get_nowait())
            except queue.Empty:
                return found

    def close(self):
        self.alive = False
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.connection.close()
        except OSError:
            pass


class LanHost:
    """TCP host plus a tiny UDP discovery responder for the current LAN."""
    def __init__(self, player_name="Orchard host", port=GAME_PORT, code=None):
        self.name = player_name[:24] or "Orchard host"
        self.code = code or f"{secrets.randbelow(10000):04d}"
        self.port = port
        self.peer = None
        self.status = "Opening a nearby game..."
        self.running = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("", port))
        self.port = self._server.getsockname()[1]
        self._server.listen(1)
        self._server.settimeout(.25)
        self._accept_thread = threading.Thread(target=self._accept, daemon=True)
        self._accept_thread.start()
        self._discovery_thread = threading.Thread(target=self._discovery, daemon=True)
        self._discovery_thread.start()

    @property
    def connected(self):
        return bool(self.peer and self.peer.alive)

    def _accept(self):
        self.status = "Waiting for Player 2 on the same Wi-Fi..."
        while self.running:
            try:
                connection, address = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            candidate = SocketPeer(connection)
            deadline = time.monotonic() + 8
            accepted = False
            attempted = False
            while candidate.alive and time.monotonic() < deadline:
                for message in candidate.poll():
                    if message.get("type") == "join":
                        attempted = True
                        accepted = message.get("code") == self.code
                        break
                if attempted:
                    break
                if accepted:
                    break
                time.sleep(.03)
            if not accepted:
                candidate.send("rejected", reason="The lobby code did not match.")
                candidate.close()
                continue
            if self.peer:
                self.peer.close()
            self.peer = candidate
            self.status = f"Player 2 connected from {address[0]}."
            candidate.send("accepted", host=self.name)

    def _discovery(self):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp.bind(("", DISCOVERY_PORT))
            udp.settimeout(.25)
            while self.running:
                try:
                    data, address = udp.recvfrom(1024)
                except socket.timeout:
                    continue
                except OSError:
                    break
                if data == b"APPLIN_ESCAPE_DISCOVER_1":
                    response = _packet("offer", name=self.name, port=self.port)
                    try:
                        udp.sendto(response.encode("utf-8"), address)
                    except OSError:
                        pass
        except OSError:
            # A TCP game still works if another local process owns discovery.
            pass
        finally:
            udp.close()

    def send(self, kind, **values):
        return self.peer.send(kind, **values) if self.connected else False

    def poll(self):
        return self.peer.poll() if self.peer else []

    def close(self):
        self.running = False
        if self.peer:
            self.peer.close()
        try:
            self._server.close()
        except OSError:
            pass


class LanClient:
    def __init__(self, address, port, code):
        self.address, self.port, self.code = address, int(port), code
        self.peer = None
        self.status = "Connecting..."
        self.running = True
        threading.Thread(target=self._connect, daemon=True).start()

    @property
    def connected(self):
        return bool(self.peer and self.peer.alive)

    def _connect(self):
        try:
            connection = socket.create_connection((self.address, self.port), timeout=8)
            self.peer = SocketPeer(connection)
            self.peer.send("join", code=self.code)
            self.status = "Checking lobby code..."
        except OSError as exc:
            self.status = "Could not connect: " + str(exc)

    def send(self, kind, **values):
        return self.peer.send(kind, **values) if self.connected else False

    def poll(self):
        return self.peer.poll() if self.peer else []

    def close(self):
        self.running = False
        if self.peer:
            self.peer.close()


def discover_lan(timeout=1.1):
    """Return unique nearby hosts. Safe to run in a worker thread."""
    found = {}
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp.settimeout(.12)
    try:
        udp.bind(("", 0))
        udp.sendto(b"APPLIN_ESCAPE_DISCOVER_1", ("255.255.255.255", DISCOVERY_PORT))
        # Loopback makes desktop tests and hotspot edge cases discoverable too.
        udp.sendto(b"APPLIN_ESCAPE_DISCOVER_1", ("127.0.0.1", DISCOVERY_PORT))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                raw, address = udp.recvfrom(2048)
                value = json.loads(raw.decode("utf-8"))
                if value.get("protocol") == PROTOCOL and value.get("type") == "offer":
                    key = address[0], int(value["port"])
                    found[key] = {"address": key[0], "port": key[1],
                                  "name": str(value.get("name", "Nearby host"))[:24]}
            except socket.timeout:
                continue
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                continue
    finally:
        udp.close()
    return list(found.values())


class BluetoothPeer:
    """A JSON peer backed by Android BluetoothSocket streams."""
    def __init__(self, bt_socket):
        from jnius import autoclass
        BufferedReader = autoclass("java.io.BufferedReader")
        InputStreamReader = autoclass("java.io.InputStreamReader")
        PrintWriter = autoclass("java.io.PrintWriter")
        self.socket = bt_socket
        self.reader = BufferedReader(InputStreamReader(bt_socket.getInputStream()))
        self.writer = PrintWriter(bt_socket.getOutputStream(), True)
        self.inbox = queue.Queue()
        self.alive = True
        self._send_lock = threading.Lock()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            while self.alive:
                raw = self.reader.readLine()
                if raw is None:
                    break
                value = json.loads(str(raw))
                if value.get("protocol") == PROTOCOL:
                    self.inbox.put(value)
        except Exception:
            pass
        self.alive = False

    def send(self, kind, **values):
        if not self.alive:
            return False
        try:
            with self._send_lock:
                self.writer.println(_packet(kind, **values))
                self.writer.flush()
            return True
        except Exception:
            self.alive = False
            return False

    def poll(self):
        found = []
        while True:
            try:
                found.append(self.inbox.get_nowait())
            except queue.Empty:
                return found

    def close(self):
        self.alive = False
        try:
            self.socket.close()
        except Exception:
            pass


def android_bluetooth_available():
    try:
        from jnius import autoclass
        return autoclass("android.bluetooth.BluetoothAdapter").getDefaultAdapter() is not None
    except Exception:
        return False


def bonded_bluetooth_devices():
    """Return paired Android devices; pairing remains in Android Settings."""
    if not android_bluetooth_available():
        return []
    try:
        from jnius import autoclass
        adapter = autoclass("android.bluetooth.BluetoothAdapter").getDefaultAdapter()
        devices = adapter.getBondedDevices().toArray()
        return [{"name": str(d.getName() or "Paired device"), "address": str(d.getAddress())}
                for d in devices]
    except Exception:
        return []


class BluetoothHost:
    def __init__(self, player_name="Orchard host", code=None):
        from jnius import autoclass
        adapter = autoclass("android.bluetooth.BluetoothAdapter").getDefaultAdapter()
        UUID = autoclass("java.util.UUID")
        self.name = player_name[:24] or "Orchard host"
        self.code = code or f"{secrets.randbelow(10000):04d}"
        self.peer = None
        self.running = True
        self.status = "Waiting for a paired Bluetooth device..."
        self.server = adapter.listenUsingRfcommWithServiceRecord("Applin Escape", UUID.fromString(SERVICE_UUID))
        threading.Thread(target=self._accept, daemon=True).start()

    @property
    def connected(self):
        return bool(self.peer and self.peer.alive)

    def _accept(self):
        try:
            while self.running:
                candidate = BluetoothPeer(self.server.accept())
                deadline = time.monotonic() + 12
                accepted = False
                attempted = False
                while candidate.alive and time.monotonic() < deadline:
                    for message in candidate.poll():
                        if message.get("type") == "join":
                            attempted = True
                            accepted = message.get("code") == self.code
                            break
                    if attempted:
                        break
                    if accepted:
                        break
                    time.sleep(.04)
                if accepted:
                    if self.peer:
                        self.peer.close()
                    self.peer = candidate
                    self.status = "Player 2 connected by Bluetooth."
                    candidate.send("accepted", host=self.name)
                else:
                    candidate.send("rejected", reason="The lobby code did not match.")
                    candidate.close()
        except Exception as exc:
            if self.running:
                self.status = "Bluetooth host stopped: " + str(exc)

    def send(self, kind, **values):
        return self.peer.send(kind, **values) if self.connected else False

    def poll(self):
        return self.peer.poll() if self.peer else []

    def close(self):
        self.running = False
        if self.peer:
            self.peer.close()
        try:
            self.server.close()
        except Exception:
            pass


class BluetoothClient:
    def __init__(self, address, code):
        self.address, self.code = address, code
        self.peer = None
        self.running = True
        self.status = "Connecting by Bluetooth..."
        threading.Thread(target=self._connect, daemon=True).start()

    @property
    def connected(self):
        return bool(self.peer and self.peer.alive)

    def _connect(self):
        try:
            from jnius import autoclass
            adapter = autoclass("android.bluetooth.BluetoothAdapter").getDefaultAdapter()
            UUID = autoclass("java.util.UUID")
            device = adapter.getRemoteDevice(self.address)
            sock = device.createRfcommSocketToServiceRecord(UUID.fromString(SERVICE_UUID))
            adapter.cancelDiscovery()
            sock.connect()
            self.peer = BluetoothPeer(sock)
            self.peer.send("join", code=self.code)
            self.status = "Checking lobby code..."
        except Exception as exc:
            self.status = "Bluetooth connection failed: " + str(exc)

    def send(self, kind, **values):
        return self.peer.send(kind, **values) if self.connected else False

    def poll(self):
        return self.peer.poll() if self.peer else []

    def close(self):
        self.running = False
        if self.peer:
            self.peer.close()
