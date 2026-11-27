"""Data model: terminal builds, run keys, and schema-1 run records."""

import collections
import glob
import hashlib
import json
import os

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_BUILDS = os.path.join(_REPO, "bench", "builds.json")


class Build(object):
    """A terminal build under test: its executable and extra environment."""

    def __init__(self, name, exec_path, env):
        self.name = name
        self.exec_path = exec_path
        self.env = dict(env)

    def __repr__(self):
        return "Build(%r, %r, %r)" % (self.name, self.exec_path, self.env)


def load_builds(path=None):
    """{name: Build} from bench/builds.json (or `path`)."""
    with open(path or DEFAULT_BUILDS) as f:
        raw = json.load(f)
    return {name: Build(name, spec["exec"], spec.get("env", {})) for name, spec in raw.items()}


RunKey = collections.namedtuple("RunKey", "build display_kind wm rtt_ms vnc_encoding size font variant workload")
SCHEMA = 1


def key_id(key):
    """sha1 of the canonical JSON of a RunKey dict."""
    return hashlib.sha1(json.dumps(dict(key), sort_keys=True).encode()).hexdigest()


def write_record(out_dir, rec):
    """Write `rec` to <out_dir>/<sha1(key)>-<iteration>.json (atomically); return the path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "%s-%d.json" % (key_id(rec["key"]), rec["iteration"]))
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(rec, f, indent=1, sort_keys=True)
    os.rename(tmp, path)
    return path


def load_records(directory):
    """Every run record in `directory`, in file-name order."""
    out = []
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        with open(path) as f:
            out.append(json.load(f))
    return out
