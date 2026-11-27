"""Minimal RFB (VNC) client for measuring what a VNC viewer would receive.

It never decodes pixels: it only walks the stream to count bytes, updates,
and rectangles per encoding, and to time key-to-update round trips. It never
asks for the Cursor or JPEG-quality pseudo-encodings, so pointer shape and
lossy settings do not perturb the numbers.
"""

import socket
import struct
import threading
import time

ENCODINGS = {"raw": 0, "copyrect": 1, "tight": 7, "zrle": 16}
_ENC_NAMES = {v: k for k, v in ENCODINGS.items()}
ENC_LASTRECT = -224
ENC_DESKTOPSIZE = -223
_PSEUDO = (ENC_LASTRECT, ENC_DESKTOPSIZE)
_TPIXEL = 3      # Tight pixels for 32 bpp / depth 24 true colour


class RfbProtocolError(RuntimeError):
    pass


def _compact_length(read):
    n, used = 0, 0
    for shift in (0, 7, 14):
        b = read(1)[0]
        used += 1
        if shift == 14:
            n |= b << 14
            break
        n |= (b & 0x7f) << shift
        if not b & 0x80:
            break
    return n, used


def parse_rect_payload(enc, w, h, read):
    """Consume one rectangle's payload via `read(n) -> bytes`; return the bytes consumed."""
    if enc == ENCODINGS["raw"]:
        read(w * h * 4)
        return w * h * 4
    if enc == ENCODINGS["copyrect"]:
        read(4)
        return 4
    if enc == ENCODINGS["zrle"]:
        n = struct.unpack(">I", read(4))[0]
        read(n)
        return 4 + n
    if enc in _PSEUDO:
        return 0
    if enc == ENCODINGS["tight"]:
        return _parse_tight(w, h, read)
    raise RfbProtocolError("unsupported encoding %d" % enc)


def _parse_tight(w, h, read):
    ctl = read(1)[0]
    used = 1
    kind = ctl >> 4
    if kind == 0x8:                        # fill
        read(_TPIXEL)
        return used + _TPIXEL
    if kind == 0x9:
        raise RfbProtocolError("Tight JPEG rectangle, but no JPEG quality level was requested")
    if kind > 0x9:
        raise RfbProtocolError("bad Tight control byte 0x%02x" % ctl)
    bpp = 8 * _TPIXEL
    if ctl & 0x40:                         # explicit filter
        filt = read(1)[0]
        used += 1
        if filt == 1:                      # palette
            count = read(1)[0] + 1
            read(count * _TPIXEL)
            used += 1 + count * _TPIXEL
            bpp = 1 if count <= 2 else 8
        elif filt not in (0, 2):           # copy, gradient
            raise RfbProtocolError("bad Tight filter %d" % filt)
    raw_len = ((w * bpp + 7) // 8) * h
    if raw_len < 12:
        read(raw_len)
        return used + raw_len
    n, n_used = _compact_length(read)
    read(n)
    return used + n_used + n


class RfbClient(object):
    """RFB 3.8 client with a background reader; see module docstring."""

    def __init__(self, host, port, encodings):
        unknown = [e for e in encodings if e not in ENCODINGS]
        if unknown:
            raise ValueError("unknown encodings %s" % unknown)
        self.host, self.port, self.encodings = host, port, list(encodings)
        self.width = self.height = None
        self._sock = None
        self._thread = None
        self._closing = False
        self._lock = threading.Condition()
        self._error = None
        self._update_seq = 0
        self._last_visible = (0, 0.0)      # (update seq, monotonic time) of the last update with a real rect
        self.reset_stats()

    # -- socket helpers
    def _recv(self, n):
        data = b""
        while len(data) < n:
            chunk = self._sock.recv(n - len(data))
            if not chunk:
                raise EOFError("RFB server closed the connection")
            data += chunk
        with self._lock:
            self._stats["bytes"] += n
        return data

    def connect(self, timeout_s=10.0):
        self._sock = socket.create_connection((self.host, self.port), timeout=timeout_s)
        version = self._recv(12)
        if not version.startswith(b"RFB 003."):
            raise RfbProtocolError("not an RFB server: %r" % version)
        self._sock.sendall(b"RFB 003.008\n")
        n = self._recv(1)[0]
        if n == 0:
            reason = self._recv(struct.unpack(">I", self._recv(4))[0])
            raise RfbProtocolError("server refused: %s" % reason.decode("utf-8", "replace"))
        if 1 not in self._recv(n):
            raise RfbProtocolError("server does not offer security type None")
        self._sock.sendall(b"\x01")
        if struct.unpack(">I", self._recv(4))[0] != 0:
            raise RfbProtocolError("security handshake failed")
        self._sock.sendall(b"\x01")                                  # ClientInit: shared
        self.width, self.height = struct.unpack(">HH", self._recv(4))
        self._recv(16)                                               # server pixel format
        self._recv(struct.unpack(">I", self._recv(4))[0])            # desktop name
        pf = struct.pack(">BBBBHHHBBB3x", 32, 24, 0, 1, 255, 255, 255, 16, 8, 0)
        self._sock.sendall(b"\x00\x00\x00\x00" + pf)                 # SetPixelFormat
        codes = [ENCODINGS[e] for e in self.encodings] + [ENC_LASTRECT, ENC_DESKTOPSIZE]
        self._sock.sendall(struct.pack(">BxH", 2, len(codes)) + struct.pack(">%di" % len(codes), *codes))
        self._sock.settimeout(None)
        self.reset_stats()
        return self

    def _request(self, incremental):
        self._sock.sendall(struct.pack(">BBHHHH", 3, 1 if incremental else 0, 0, 0, self.width, self.height))

    def start(self):
        self._request(incremental=False)
        self._thread = threading.Thread(target=self._reader, name="rfb-reader", daemon=True)
        self._thread.start()
        return self

    def _reader(self):
        try:
            while True:
                kind = self._recv(1)[0]
                if kind == 0:
                    self._framebuffer_update()
                    self._request(incremental=True)
                elif kind == 1:                                      # SetColourMapEntries
                    _, _, n = struct.unpack(">BHH", self._recv(5))
                    self._recv(6 * n)
                elif kind == 2:                                      # Bell
                    pass
                elif kind == 3:                                      # ServerCutText
                    self._recv(3)
                    self._recv(struct.unpack(">I", self._recv(4))[0])
                else:
                    raise RfbProtocolError("unknown server message %d" % kind)
        except Exception as e:  # noqa: BLE001 - reported to waiters
            with self._lock:
                if not self._closing:
                    self._error = e
                self._lock.notify_all()

    def _framebuffer_update(self):
        n = struct.unpack(">xH", self._recv(3))[0]
        visible = False
        for _ in range(n):
            x, y, w, h, enc = struct.unpack(">HHHHi", self._recv(12))
            parse_rect_payload(enc, w, h, self._recv)
            if enc == ENC_LASTRECT:
                break
            if enc == ENC_DESKTOPSIZE:
                self.width, self.height = w, h
                continue
            visible = True
            with self._lock:
                name = _ENC_NAMES[enc]
                self._stats["rects"][name] = self._stats["rects"].get(name, 0) + 1
                if enc == ENCODINGS["copyrect"]:
                    self._stats["copyrect_area"] += w * h
        with self._lock:
            self._stats["updates"] += 1
            self._update_seq += 1
            if visible:
                self._last_visible = (self._update_seq, time.monotonic())
            self._lock.notify_all()

    def reset_stats(self):
        with self._lock:
            self._stats = {"bytes": 0, "updates": 0, "rects": {}, "copyrect_area": 0}

    def stats(self):
        with self._lock:
            st = dict(self._stats)
            st["rects"] = dict(self._stats["rects"])
            return st

    def key_roundtrip_ms(self, keysym, timeout_s=2.0):
        """Send key down+up; ms until the next complete update with a real rectangle, or None."""
        with self._lock:
            seq0 = self._update_seq
        t0 = time.monotonic()
        self._sock.sendall(struct.pack(">BBxxI", 4, 1, keysym) + struct.pack(">BBxxI", 4, 0, keysym))
        deadline = t0 + timeout_s
        with self._lock:
            while True:
                if self._error is not None:
                    raise RfbProtocolError("RFB reader failed: %s" % self._error)
                seq, t = self._last_visible
                if seq > seq0 and t >= t0:
                    return (t - t0) * 1000.0
                left = deadline - time.monotonic()
                if left <= 0:
                    return None
                self._lock.wait(left)

    def close(self):
        with self._lock:
            self._closing = True
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._sock.close()
        if self._thread is not None:
            self._thread.join(5)
