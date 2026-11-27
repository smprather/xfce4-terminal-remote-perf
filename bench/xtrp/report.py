"""Baseline-vs-candidate comparison with a noise-aware regression flag.

Rows are grouped by RunKey minus `build`, plus the metric name. List metrics
(latency samples) are pooled across iterations; scalar metrics are summarized
across iterations. A row regresses when the candidate is worse than the
baseline median by more than max(threshold, baseline noise band), where the
noise band is 100*(p90-p10)/median of the baseline.
"""

import collections

from xtrp.metrics import summarize

KEY_FIELDS = ("display_kind", "wm", "rtt_ms", "vnc_encoding", "size", "font", "variant", "workload")

# +1 higher is better, -1 lower is better, 0 informational (never flagged).
# Gated metrics are outcomes. Their components (elapsed_s + drain_s = total_s) and structure
# counters (how the encoder split frames into rects/updates, how many damage events) are
# informational: they move with timing phase from run to run while the outcome does not.
METRIC_DIRECTION = {m: -1 for m in (
    "startup_ms", "term_cpu_s", "xserver_cpu_s", "damage_area_px", "latency_ms", "e2e_latency_ms",
    "total_s", "vnc_bytes", "x11_c2s_bytes", "x11_s2c_bytes", "x11_replies", "x11_requests",
    "x11_image_bytes", "startup_x11_replies")}
METRIC_DIRECTION.update({
    "throughput_mb_s": 1,
    "frames": 1,                 # fullscreen-redraw frames written in its fixed time: more = kept up
    "vnc_copyrect_area": 0,      # more CopyRect is the goal of scroll-by-copy, not a regression
    "elapsed_s": 0, "drain_s": 0, "vnc_rects": 0, "vnc_updates": 0, "damage_events": 0,
})


class PlatformMismatch(ValueError):
    def __init__(self, base_tags, cand_tags):
        self.base_tags, self.cand_tags = base_tags, cand_tags
        ValueError.__init__(self, "refusing to compare %s with %s" % ("/".join(base_tags), "/".join(cand_tags)))


def _tags(records):
    return sorted({r.get("platform", {}).get("tag", "?") for r in records})


def _collect(records):
    """OrderedDict {group key tuple: {metric: [values]}}."""
    out = collections.OrderedDict()
    for r in records:
        bucket = out.setdefault(tuple(r["key"][f] for f in KEY_FIELDS), {})
        for metric, value in r.get("metrics", {}).items():
            if isinstance(value, list):
                bucket.setdefault(metric, []).extend(v for v in value if v is not None)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                bucket.setdefault(metric, []).append(value)
    return out


def _judge(row, metric, threshold_pct, cross_platform):
    b, c = row["base"]["median"], row["cand"]["median"]
    if b is None or c is None:
        row["note"] = "no data"
        return
    if b == 0:
        if c != 0:
            row["note"] = "base median 0"
        return
    direction = METRIC_DIRECTION.get(metric, 0)
    change = (c - b) / abs(b) * 100.0
    row["delta_pct"] = -change if direction < 0 else change
    row["noise_pct"] = 100.0 * (row["base"]["p90"] - row["base"]["p10"]) / abs(b)
    if direction != 0 and not cross_platform:
        row["regression"] = row["delta_pct"] < -max(threshold_pct, row["noise_pct"])


def compare(base, cand, threshold_pct=5.0, cross_platform=False):
    """Rows comparing two record sets; raises PlatformMismatch across platforms unless cross_platform."""
    base_tags, cand_tags = _tags(base), _tags(cand)
    if not cross_platform and len(set(base_tags) | set(cand_tags)) > 1:
        raise PlatformMismatch(base_tags, cand_tags)
    b_groups, c_groups = _collect(base), _collect(cand)
    order = list(b_groups) + [k for k in c_groups if k not in b_groups]
    rows = []
    for gk in order:
        bm, cm = b_groups.get(gk, {}), c_groups.get(gk, {})
        for metric in sorted(set(bm) | set(cm)):
            row = {"key": dict(zip(KEY_FIELDS, gk)), "metric": metric,
                   "base": summarize(bm.get(metric, [])), "cand": summarize(cm.get(metric, [])),
                   "delta_pct": None, "noise_pct": None, "regression": False}
            if metric not in bm:
                row["note"] = "missing in base"
            elif metric not in cm:
                row["note"] = "missing in cand"
            else:
                _judge(row, metric, threshold_pct, cross_platform)
            rows.append(row)
    return rows


def flag_summary(label, records):
    """One line: record count, records with errors, drain timeouts."""
    errors = sum(1 for r in records if r.get("flags", {}).get("errors"))
    drains = sum(1 for r in records if r.get("flags", {}).get("drain_timeout"))
    return "%s: %d records, %d with errors, %d drain timeouts" % (label, len(records), errors, drains)


def _fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return "%.4g" % v
    return str(v)


def _pct(v):
    return "-" if v is None else "%+.1f" % v


def _config(key):
    return " ".join(str(key[f]) for f in ("vnc_encoding", "size", "font", "variant") if key[f] is not None)


def render_markdown(rows, cross_platform=False, preamble=()):
    """Markdown: regression summary first, then one table per (display_kind, wm, rtt_ms)."""
    lines = ["# xtrp report", ""]
    if cross_platform:
        lines += ["> Cross-platform comparison: userland and libraries differ, so these numbers are "
                  "informational only. No regressions are flagged.", ""]
    lines += list(preamble) + ([""] if preamble else [])
    regressions = [r for r in rows if r["regression"]]
    lines += ["## Regressions", ""]
    if regressions:
        for r in regressions:
            k = r["key"]
            lines.append("- %s `%s` (%s/%s rtt=%s %s): %s -> %s (%s%%, noise %.1f%%)" % (
                k["workload"], r["metric"], k["display_kind"], k["wm"], k["rtt_ms"], _config(k),
                _fmt(r["base"]["median"]), _fmt(r["cand"]["median"]), _pct(r["delta_pct"]), r["noise_pct"]))
    else:
        lines.append("No regressions.")
    lines.append("")
    tables = collections.OrderedDict()
    for r in rows:
        k = r["key"]
        tables.setdefault((k["display_kind"], k["wm"], k["rtt_ms"]), []).append(r)
    for (display_kind, wm, rtt), trows in tables.items():
        lines += ["## %s / %s%s" % (display_kind, wm, "" if rtt is None else " / rtt %s ms" % rtt), "",
                  "| workload | config | metric | base median | cand median | Δ% | noise% | flag |",
                  "|---|---|---|---|---|---|---|---|"]
        for r in trows:
            flag = "REGRESSION" if r["regression"] else r.get("note", "")
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                r["key"]["workload"], _config(r["key"]), r["metric"], _fmt(r["base"]["median"]),
                _fmt(r["cand"]["median"]), _pct(r["delta_pct"]),
                "-" if r["noise_pct"] is None else "%.1f" % r["noise_pct"], flag))
        lines.append("")
    return "\n".join(lines)
