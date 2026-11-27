import json
import os
import socket
import unittest
from unittest import mock

from tests.xenv import XvfbFixture
from xtrp.diag import collect, display_transport, scrub


class ScrubTest(unittest.TestCase):

    def test_scrub_removes_planted_site_identifiers(self):
        planted = {"vendor": "Xvnc on build7.eng.example.corp", "display": "build7.eng.example.corp:3",
                   "path": "/vols/tools/x/bin/bash", "home": "/home/alice/x", "ip": "10.1.2.3", "v6": "fe80::1",
                   "note": "job PROJ:261:AE:debug"}
        out = json.dumps(scrub(planted, extra_terms=["PROJ:261:AE:debug"]))
        for s in ("example.corp", "build7", "/vols/", "alice", "10.1.2.3", "fe80::1", "PROJ:261"):
            self.assertNotIn(s, out)

    def test_scrub_removes_local_hostname_and_user(self):
        host = socket.gethostname()
        with mock.patch.dict(os.environ, {"USER": "zelda"}):
            out = json.dumps(scrub({"a": "%s:0 by zelda" % host, host: ["zelda"]}))
        self.assertNotIn(host, out)
        self.assertNotIn("zelda", out)
        self.assertIn("<host>", out)
        self.assertIn("<user>", out)

    def test_scrub_keeps_versions_times_and_vendor_names(self):
        keep = ["vte291-0.52.4-2.el8.x86_64", "18:14:53", "The X.Org Foundation", "3.32.2", "GNOME-Classic:GNOME",
                "CaskaydiaCove Nerd Font Mono", "rgba"]
        self.assertEqual(scrub(keep), keep)

    def test_scrub_does_not_mutate_input(self):
        planted = {"ip": ["10.9.8.7"]}
        scrub(planted)
        self.assertEqual(planted, {"ip": ["10.9.8.7"]})

    def test_display_transport(self):
        for display, want in ((":0", "unix"), (":0.0", "unix"), ("unix:3", "unix"), ("A:2", "tcp"),
                              ("build7.eng.example.corp:3", "tcp"), ("localhost:10.0", "tcp"), ("", None)):
            self.assertEqual(display_transport(display), want, display)


class CollectTest(XvfbFixture):

    def test_collect_is_scrubbed_and_has_sections(self):
        with mock.patch.dict(os.environ, {"DISPLAY": self.display}):
            d = collect()
        for section in ("xlat_info", "display_transport", "fonts", "font_rendering", "xft", "packages",
                        "session", "cpu"):
            self.assertIn(section, d)
        self.assertEqual(d["display_transport"], "unix")
        self.assertIn("DAMAGE", d["xlat_info"]["extensions"])
        self.assertIn("monospace", d["fonts"])
        # fc-match takes family names: "DejaVu Sans Mono 12" would silently fall back to another font
        self.assertIn('"DejaVu Sans Mono"', d["fonts"]["DejaVu Sans Mono"])
        self.assertIn('"CaskaydiaCove Nerd Font Mono"', d["fonts"]["CaskaydiaCove Nerd Font Mono"])
        self.assertEqual(sorted(d["font_rendering"]), ["gnome", "gnome-xsettings", "mate"])
        self.assertIn("vte291", d["packages"])
        self.assertGreater(d["cpu"]["nproc"], 0)
        self.assertNotIn(socket.gethostname(), json.dumps(d))


if __name__ == "__main__":
    unittest.main()
