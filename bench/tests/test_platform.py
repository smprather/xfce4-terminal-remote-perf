import os
import shutil
import tempfile
import unittest
from unittest import mock

from xtrp import platform
from xtrp.platform import child_env, helper_env, platform_tag


ALMA8 = 'NAME="AlmaLinux"\nVERSION="8.10 (Cerulean Leopard)"\nID="almalinux"\nID_LIKE="rhel centos fedora"\nVERSION_ID="8.10"\n'
ALMA9 = 'NAME="AlmaLinux"\nID="almalinux"\nID_LIKE="rhel centos fedora"\nVERSION_ID="9.9"\n'
RHEL8 = 'NAME="Red Hat Enterprise Linux"\nID="rhel"\nID_LIKE="fedora"\nVERSION_ID="8.10"\n'
CACHY = 'NAME="CachyOS Linux"\nID=cachyos\nID_LIKE=arch\nBUILD_ID=rolling\n'
FEDORA = 'NAME="Fedora Linux"\nID=fedora\nVERSION_ID=41\n'


class PlatformTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="xtrp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _os_release(self, text):
        path = os.path.join(self.tmp, "os-release")
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_child_env_is_built_not_inherited(self):
        planted = {"WAYLAND_DISPLAY": "wayland-9", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/x",
                   "XDG_RUNTIME_DIR": "/run/user/1", "XDG_SESSION_TYPE": "wayland", "FOO": "1",
                   "XAUTHORITY": "/home/u/.Xauthority", "SESSION_MANAGER": "local/x:@/tmp/.ICE-unix/1"}
        with mock.patch.dict(os.environ, planted):
            e = child_env(":57", self.tmp)
        for k in ("WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "XDG_SESSION_TYPE", "FOO",
                  "XAUTHORITY", "SESSION_MANAGER"):
            self.assertNotIn(k, e)
        self.assertEqual(e["DISPLAY"], ":57")
        self.assertEqual(e["GDK_BACKEND"], "x11")
        self.assertEqual(e["NO_AT_BRIDGE"], "1")
        self.assertEqual(e["XDG_RUNTIME_DIR"], os.path.join(self.tmp, "run"))
        self.assertEqual(os.stat(e["XDG_RUNTIME_DIR"]).st_mode & 0o777, 0o700)
        self.assertTrue(e["HOME"].startswith(self.tmp))
        for k in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
            self.assertTrue(e[k].startswith(e["HOME"]), k)

    def test_child_env_extra_is_applied_last(self):
        e = child_env(":57", self.tmp, {"GDK_BACKEND": "x11", "VTE_PROFILE": "local"})
        self.assertEqual(e["VTE_PROFILE"], "local")

    def test_helper_env_carries_only_display_and_auth(self):
        planted = {"WAYLAND_DISPLAY": "wayland-9", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/x",
                   "XAUTHORITY": "/home/u/.Xauthority", "HOME": "/home/u", "FOO": "1"}
        with mock.patch.dict(os.environ, planted):
            e = helper_env(":3")
        self.assertEqual(e["DISPLAY"], ":3")
        self.assertEqual(e["XAUTHORITY"], "/home/u/.Xauthority")
        self.assertEqual(e["HOME"], "/home/u")
        for k in ("WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "FOO"):
            self.assertNotIn(k, e)

    def test_platform_tag_from_os_release(self):
        self.assertEqual(platform_tag(self._os_release(ALMA8)), "el8")
        self.assertEqual(platform_tag(self._os_release(ALMA9)), "el9")
        self.assertEqual(platform_tag(self._os_release(RHEL8)), "el8")
        self.assertEqual(platform_tag(self._os_release(CACHY)), "host")
        self.assertEqual(platform_tag(self._os_release(FEDORA)), "host")
        self.assertEqual(platform_tag(os.path.join(self.tmp, "missing")), "host")

    def test_platform_tag_of_this_machine(self):
        tag = platform_tag()
        self.assertIn(tag, ("el8", "el9", "host"))
        if tag != "host":
            with open("/etc/os-release") as f:
                self.assertIn('VERSION_ID="%s.' % tag[2:], f.read())

    def test_tool_resolution(self):
        self.assertIsNone(platform.tool("no-such-tool-xtrp"))
        self.assertTrue(os.path.isabs(platform.tool("sh")))

    def test_packages_reports_terminal_and_vte(self):
        pk = platform.packages()
        self.assertIn("xfce4-terminal", pk)
        self.assertIn("vte", pk)


if __name__ == "__main__":
    unittest.main()
