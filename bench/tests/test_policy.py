"""Repository policy checks for everything under bench/.

- tmux is only ever reached through workloads.tmux_argv(), which always passes
  a private `-L xtrp-...` socket; the shared default server is never touched.
- Processes are never stopped by name (no pkill/killall).
"""

import os
import re
import unittest

BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = os.path.abspath(__file__)
SKIP_DIRS = {"__pycache__", "bin"}

# tmux as the command word of a shell line: start of line, after exec, $( ` | ; && ||
SHELL_TMUX = re.compile(r"(?:^|\$\(|`|\||;|&&|\bexec\s)\s*(?:\S*/)?tmux(?:\s+([^\s)`;|&]+))?")
PY_TMUX_ARG = re.compile(r"""["']tmux["']\s*[,\]]""")
PY_TMUX_TOOL = re.compile(r"""(?<!\w)tool\(\s*["']tmux["']\s*\)""")
KILL_BY_NAME = re.compile(r"\b(pkill|killall)\b")


def bench_files():
    for root, dirs, files in os.walk(BENCH):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = os.path.join(root, name)
            if path == SELF:
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    yield path, f.read()
            except (UnicodeDecodeError, OSError):
                continue


class PolicyTest(unittest.TestCase):

    def test_no_kill_by_name(self):
        hits = ["%s: %s" % (os.path.relpath(p, BENCH), m.group(0))
                for p, text in bench_files() for m in KILL_BY_NAME.finditer(text)]
        self.assertEqual(hits, [])

    def test_tmux_only_through_tmux_argv(self):
        hits = []
        for path, text in bench_files():
            rel = os.path.relpath(path, BENCH)
            if path.endswith(".py"):
                for n, line in enumerate(text.splitlines(), 1):
                    if PY_TMUX_ARG.search(line):
                        hits.append("%s:%d literal tmux argv: %s" % (rel, n, line.strip()))
                    if PY_TMUX_TOOL.search(line) and not (rel == os.path.join("xtrp", "workloads.py")
                                                          and "def tmux_argv" in text):
                        hits.append("%s:%d tool('tmux') outside tmux_argv" % (rel, n))
                tool_uses = len(PY_TMUX_TOOL.findall(text))
                if rel == os.path.join("xtrp", "workloads.py") and tool_uses != 1:
                    hits.append("%s: tool('tmux') must appear exactly once (in tmux_argv)" % rel)
            else:
                for n, line in enumerate(text.splitlines(), 1):
                    if line.lstrip().startswith("#"):
                        continue
                    for m in SHELL_TMUX.finditer(line):
                        if m.group(1) not in ("-L", "-V"):
                            hits.append("%s:%d tmux without -L: %s" % (rel, n, line.strip()))
        self.assertEqual(hits, [])

    def test_kill_server_only_in_workloads(self):
        # Tests may name kill-server as data; they can only run it through tmux_argv (checked above).
        hits = [os.path.relpath(p, BENCH) for p, text in bench_files()
                if "kill-server" in text and not os.path.relpath(p, BENCH).startswith("tests" + os.sep)
                and os.path.relpath(p, BENCH) != os.path.join("xtrp", "workloads.py")]
        self.assertEqual(hits, [])

    def test_policy_patterns_catch_violations(self):
        self.assertTrue(KILL_BY_NAME.search("subprocess.run(['pkill', 'Xvfb'])"))
        self.assertTrue(KILL_BY_NAME.search("killall tmux"))
        self.assertTrue(PY_TMUX_ARG.search('subprocess.run(["tmux", "kill-server"])'))
        m = SHELL_TMUX.search("x=$(tmux kill-server)")
        self.assertEqual(m.group(1), "kill-server")
        self.assertEqual(SHELL_TMUX.search("tmux -L xtrp-1 ls").group(1), "-L")
        self.assertIsNone(SHELL_TMUX.search("need tmux tmux"))
        self.assertTrue(PY_TMUX_TOOL.search('exe = platform.tool("tmux")'))
        self.assertIsNone(PY_TMUX_TOOL.search('need_tool("tmux")'))


if __name__ == "__main__":
    unittest.main()
