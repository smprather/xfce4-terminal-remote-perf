"""Counting, delaying X11 proxy for the x11-remote topology (T2: X client on B, display on A).

X11StreamParser walks both directions of one X connection without decoding
payloads: it counts bytes, requests by name, replies, events, errors and
image-carrying requests. With hide_shm it rewrites the MIT-SHM QueryExtension
reply to "not present", as a real remote display would behave.

X11Proxy listens on localhost TCP 6000+M (M in 150..199), connects each client
to the upstream display's unix socket, and holds every forwarded chunk for
rtt_ms/2 in each direction, optionally rate-limited by a token bucket.
"""

import collections
import os
import selectors
import socket
import struct
import threading
import time

CORE_NAMES = dict(enumerate((
    None, "CreateWindow", "ChangeWindowAttributes", "GetWindowAttributes", "DestroyWindow", "DestroySubwindows",
    "ChangeSaveSet", "ReparentWindow", "MapWindow", "MapSubwindows", "UnmapWindow", "UnmapSubwindows",
    "ConfigureWindow", "CirculateWindow", "GetGeometry", "QueryTree", "InternAtom", "GetAtomName",
    "ChangeProperty", "DeleteProperty", "GetProperty", "ListProperties", "SetSelectionOwner",
    "GetSelectionOwner", "ConvertSelection", "SendEvent", "GrabPointer", "UngrabPointer", "GrabButton",
    "UngrabButton", "ChangeActivePointerGrab", "GrabKeyboard", "UngrabKeyboard", "GrabKey", "UngrabKey",
    "AllowEvents", "GrabServer", "UngrabServer", "QueryPointer", "GetMotionEvents", "TranslateCoordinates",
    "WarpPointer", "SetInputFocus", "GetInputFocus", "QueryKeymap", "OpenFont", "CloseFont", "QueryFont",
    "QueryTextExtents", "ListFonts", "ListFontsWithInfo", "SetFontPath", "GetFontPath", "CreatePixmap",
    "FreePixmap", "CreateGC", "ChangeGC", "CopyGC", "SetDashes", "SetClipRectangles", "FreeGC", "ClearArea",
    "CopyArea", "CopyPlane", "PolyPoint", "PolyLine", "PolySegment", "PolyRectangle", "PolyArc", "FillPoly",
    "PolyFillRectangle", "PolyFillArc", "PutImage", "GetImage", "PolyText8", "PolyText16", "ImageText8",
    "ImageText16", "CreateColormap", "FreeColormap", "CopyColormapAndFree", "InstallColormap",
    "UninstallColormap", "ListInstalledColormaps", "AllocColor", "AllocNamedColor", "AllocColorCells",
    "AllocColorPlanes", "FreeColors", "StoreColors", "StoreNamedColor", "QueryColors", "LookupColor",
    "CreateCursor", "CreateGlyphCursor", "FreeCursor", "RecolorCursor", "QueryBestSize", "QueryExtension",
    "ListExtensions", "ChangeKeyboardMapping", "GetKeyboardMapping", "ChangeKeyboardControl",
    "GetKeyboardControl", "Bell", "ChangePointerControl", "GetPointerControl", "SetScreenSaver",
    "GetScreenSaver", "ChangeHosts", "ListHosts", "SetAccessControl", "SetCloseDownMode", "KillClient",
    "RotateProperties", "ForceScreenSaver", "SetPointerMapping", "GetPointerMapping", "SetModifierMapping",
    "GetModifierMapping")))
CORE_NAMES[127] = "NoOperation"
del CORE_NAMES[0]

_QUERY_EXTENSION = 98
_IMAGE_REQUESTS = {("core", 72), ("MIT-SHM", 3), ("RENDER", 20)}


def _pad4(n):
    return (n + 3) & ~3


class _Side(object):
    def __init__(self):
        self.buf = bytearray()
        self.skip = 0
        self.setup = True


class X11StreamParser(object):
    """Incremental parser for one X11 connection (both directions)."""

    def __init__(self, hide_shm=True):
        self.hide_shm = hide_shm
        self.stats = {"c2s_bytes": 0, "s2c_bytes": 0, "requests": {}, "replies": 0, "events": 0,
                      "errors": 0, "image_bytes": 0}
        self._order = "<"
        self._c = _Side()
        self._s = _Side()
        self._seq = 0
        self._pending = {}       # reply sequence (16 bit) -> extension name queried
        self._ext = {}           # major opcode -> extension name

    # -- shared driver: buffer just enough for a header, stream the rest through `skip`
    def _drive(self, side, data, parse, out):
        pos, n = 0, len(data)
        while True:
            if side.skip:
                if pos >= n:
                    break
                take = min(side.skip, n - pos)
                if out is not None:
                    out.append(data[pos:pos + take])
                side.skip -= take
                pos += take
                continue
            need = parse(out)
            if need == 0:
                continue
            if pos >= n:
                break
            take = min(need - len(side.buf), n - pos)
            side.buf += data[pos:pos + take]
            pos += take

    def _finish(self, side, total, out, header):
        have = len(side.buf)
        if out is not None:
            out.append(bytes(header if header is not None else side.buf))
        side.skip = total - have
        side.buf = bytearray()
        return 0

    # -- client -> server
    def feed_c2s(self, data):
        self.stats["c2s_bytes"] += len(data)
        self._drive(self._c, data, self._parse_c2s, None)
        return data

    def _parse_c2s(self, out):
        buf = self._c.buf
        if self._c.setup:
            if len(buf) < 12:
                return 12
            self._order = "<" if buf[0] == 0x6c else ">"
            nlen, dlen = struct.unpack(self._order + "HH", bytes(buf[6:10]))
            self._c.setup = False
            return self._finish(self._c, 12 + _pad4(nlen) + _pad4(dlen), out, None)
        if len(buf) < 4:
            return 4
        major, minor, len16 = struct.unpack(self._order + "BBH", bytes(buf[:4]))
        if len16 == 0:
            if len(buf) < 8:
                return 8
            total = struct.unpack(self._order + "I", bytes(buf[4:8]))[0] * 4
        else:
            total = len16 * 4
        if major == _QUERY_EXTENSION and len(buf) < total:
            return total
        self._seq += 1
        if major == _QUERY_EXTENSION:
            nlen = struct.unpack(self._order + "H", bytes(buf[4:6]))[0]
            self._pending[self._seq & 0xffff] = bytes(buf[8:8 + nlen]).decode("latin-1")
        if major < 128:
            group, name = "core", "core:%s" % CORE_NAMES.get(major, major)
        else:
            group = self._ext.get(major)
            name = "%s:%d" % (group, minor) if group else "ext%d:%d" % (major, minor)
        req = self.stats["requests"]
        req[name] = req.get(name, 0) + 1
        if (group, major if group == "core" else minor) in _IMAGE_REQUESTS:
            self.stats["image_bytes"] += total
        return self._finish(self._c, total, out, None)

    # -- server -> client
    def feed_s2c(self, data):
        self.stats["s2c_bytes"] += len(data)
        out = []
        self._drive(self._s, data, self._parse_s2c, out)
        return b"".join(out)

    def _parse_s2c(self, out):
        buf = self._s.buf
        if self._s.setup:
            if len(buf) < 8:
                return 8
            self._s.setup = False
            return self._finish(self._s, 8 + 4 * struct.unpack(self._order + "H", bytes(buf[6:8]))[0], out, None)
        if len(buf) < 32:
            return 32
        kind = buf[0] & 0x7f
        total = 32
        if kind == 0:
            self.stats["errors"] += 1
        elif kind == 1:
            self.stats["replies"] += 1
            seq, extra = struct.unpack(self._order + "HI", bytes(buf[2:8]))
            total = 32 + 4 * extra
            name = self._pending.pop(seq, None)
            if name is not None:
                if name == "MIT-SHM" and self.hide_shm:
                    buf[8] = 0
                elif buf[8]:
                    self._ext[buf[9]] = name
        else:
            self.stats["events"] += 1
            if kind == 35:
                total = 32 + 4 * struct.unpack(self._order + "I", bytes(buf[4:8]))[0]
        return self._finish(self._s, total, out, buf)


class _Pipe(object):
    """One direction of one proxied connection: delay queue, token bucket, output buffer."""

    def __init__(self, dest):
        self.dest = dest
        self.queue = collections.deque()     # (release time, bytes)
        self.out = bytearray()
        self.tokens = 0.0
        self.refilled = time.monotonic()


class X11Proxy(object):
    """See module docstring. Context manager; .display is "localhost:M" once started."""

    def __init__(self, upstream_display, rtt_ms=0.0, bw_mbps=None, hide_shm=True):
        self.upstream_display = upstream_display
        self.delay_s = max(0.0, rtt_ms) / 2000.0
        self.rate = None if not bw_mbps else bw_mbps * 1e6 / 8.0
        self.burst = 64 * 1024
        self.hide_shm = hide_shm
        self.display = self.number = None
        self._parsers = []
        self._lock = threading.Lock()
        self._stop = False
        self._thread = None

    def _upstream_path(self):
        number = self.upstream_display.rsplit(":", 1)[1].split(".")[0]
        return "/tmp/.X11-unix/X%s" % number

    def start(self):
        for m in range(150, 200):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind(("127.0.0.1", 6000 + m))
            except OSError:
                s.close()
                continue
            s.listen(16)
            s.setblocking(False)
            self._listener, self.number = s, m
            break
        else:
            raise RuntimeError("no free TCP port in 6150..6199")
        self.display = "localhost:%d" % self.number
        self._wake_r, self._wake_w = socket.socketpair()
        self._wake_r.setblocking(False)
        self._sel = selectors.DefaultSelector()
        self._sel.register(self._listener, selectors.EVENT_READ, ("listen", None))
        self._sel.register(self._wake_r, selectors.EVENT_READ, ("wake", None))
        self._thread = threading.Thread(target=self._loop, name="x11proxy", daemon=True)
        self._thread.start()
        return self.display

    def stats(self):
        merged = {"c2s_bytes": 0, "s2c_bytes": 0, "requests": {}, "replies": 0, "events": 0,
                  "errors": 0, "image_bytes": 0}
        with self._lock:
            for p in self._parsers:
                for k, v in p.stats.items():
                    if k == "requests":
                        for name, n in v.items():
                            merged["requests"][name] = merged["requests"].get(name, 0) + n
                    else:
                        merged[k] += v
        return merged

    # -- event loop
    def _accept(self):
        try:
            client, _ = self._listener.accept()
        except OSError:
            return
        upstream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            upstream.connect(self._upstream_path())
        except OSError:
            client.close()
            upstream.close()
            return
        for s in (client, upstream):
            s.setblocking(False)
        client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        parser = X11StreamParser(self.hide_shm)
        with self._lock:
            self._parsers.append(parser)
        conn = {"client": client, "upstream": upstream, "parser": parser,
                "c2s": _Pipe(upstream), "s2c": _Pipe(client), "open": True}
        self._conns.append(conn)
        self._sel.register(client, selectors.EVENT_READ, ("read", (conn, "c2s")))
        self._sel.register(upstream, selectors.EVENT_READ, ("read", (conn, "s2c")))

    def _close(self, conn):
        if not conn["open"]:
            return
        conn["open"] = False
        for s in (conn["client"], conn["upstream"]):
            try:
                self._sel.unregister(s)
            except (KeyError, ValueError):
                pass
            s.close()
        self._conns.remove(conn)

    def _read(self, conn, direction):
        src = conn["client"] if direction == "c2s" else conn["upstream"]
        try:
            data = src.recv(65536)
        except (BlockingIOError, InterruptedError):
            return
        except OSError:
            data = b""
        if not data:
            self._close(conn)
            return
        parser = conn["parser"]
        out = parser.feed_c2s(data) if direction == "c2s" else parser.feed_s2c(data)
        if out:
            conn[direction].queue.append((time.monotonic() + self.delay_s, out))

    def _pump(self, conn, pipe, now):
        """Move due chunks into the output buffer (respecting the bucket) and write what we can."""
        if self.rate:
            pipe.tokens = min(self.burst, pipe.tokens + (now - pipe.refilled) * self.rate)
            pipe.refilled = now
        while pipe.queue and pipe.queue[0][0] <= now:
            release, chunk = pipe.queue[0]
            if self.rate:
                allowed = int(pipe.tokens)
                if allowed <= 0:
                    break
                if allowed < len(chunk):
                    pipe.queue[0] = (release, chunk[allowed:])
                    chunk = chunk[:allowed]
                else:
                    pipe.queue.popleft()
                pipe.tokens -= len(chunk)
            else:
                pipe.queue.popleft()
            pipe.out += chunk
        while pipe.out:
            try:
                sent = pipe.dest.send(pipe.out)
            except (BlockingIOError, InterruptedError):
                break
            except OSError:
                self._close(conn)
                return
            del pipe.out[:sent]

    def _next_timeout(self, now):
        best = None
        for conn in self._conns:
            for direction in ("c2s", "s2c"):
                pipe = conn[direction]
                if pipe.out:
                    t = 0.001
                elif pipe.queue:
                    t = max(0.0, pipe.queue[0][0] - now)
                    if self.rate and pipe.tokens < 1:
                        t = max(t, (1 - pipe.tokens) / self.rate)
                else:
                    continue
                best = t if best is None else min(best, t)
        return best

    def _loop(self):
        self._conns = []
        while not self._stop:
            for key, _ in self._sel.select(self._next_timeout(time.monotonic())):
                what, arg = key.data
                if what == "listen":
                    self._accept()
                elif what == "wake":
                    try:
                        self._wake_r.recv(64)
                    except OSError:
                        pass
                elif arg[0]["open"]:
                    self._read(*arg)
            now = time.monotonic()
            for conn in list(self._conns):
                for direction in ("c2s", "s2c"):
                    if conn["open"]:
                        self._pump(conn, conn[direction], now)
        for conn in list(self._conns):
            self._close(conn)

    def stop(self):
        if self._thread is None:
            return
        self._stop = True
        try:
            self._wake_w.send(b"x")
        except OSError:
            pass
        self._thread.join(5)
        self._thread = None
        for s in (self._listener, self._wake_r, self._wake_w):
            s.close()
        self._sel.close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()
        return False
