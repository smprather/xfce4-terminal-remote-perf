"""Data model: terminal builds (and, from Task 7, run keys and records)."""

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
