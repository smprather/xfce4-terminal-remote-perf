import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest

from tests.xenv import XvfbFixture
from xtrp import platform

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUNDLE = os.path.join(REPO, "dist", "xtrp-live.tar.gz")


class BundleTest(XvfbFixture):
    """The live bundle is built on el8 (one xlat for EL8 and EL9); el9 and the host reuse it."""

    def setUp(self):
        if platform.platform_tag() == "el8":
            subprocess.run([os.path.join(REPO, "bench", "make-live-bundle")], check=True,
                           stdout=subprocess.DEVNULL, timeout=300)
        elif not os.path.exists(BUNDLE):
            raise unittest.SkipTest("build the bundle on el8 first (bench/container bench/make-live-bundle)")
        super(BundleTest, self).setUp()

    def test_bundle_runs_diag(self):
        dest = tempfile.mkdtemp(prefix="xtrp-bundle-")
        self.addCleanup(shutil.rmtree, dest, True)
        with tarfile.open(BUNDLE) as tar:
            names = tar.getnames()
            tar.extractall(dest)
        root = os.path.join(dest, "xtrp-live")
        for want in ("xtrp-live/run", "xtrp-live/bin/xlat", "xtrp-live/xtrp/diag.py", "xtrp-live/conf/tmux.conf"):
            self.assertIn(want, names)
        env = dict(platform.plain_env(), DISPLAY=self.display, HOME=self.tmp)
        r = subprocess.run([os.path.join(root, "run"), "diag"], env=env, cwd=dest,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr.decode()[-1000:])
        d = json.loads(r.stdout.decode())
        self.assertIn("DAMAGE", d["xlat_info"]["extensions"])


if __name__ == "__main__":
    unittest.main()
