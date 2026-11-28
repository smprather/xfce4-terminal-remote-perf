"""Baseline-vs-candidate comparison with a noise-aware regression flag.

Rows are grouped by RunKey minus `build`, plus the metric name. Each run contributes one value per
metric: a list metric (latency samples) contributes its median, so the noise band is run-to-run spread
rather than keystroke jitter. Records with errors are left out of the medians and counted instead. A
row regresses when the candidate is worse than the baseline median by more than max(threshold,
baseline noise band), where the noise band is 100*(p90-p10)/median of the baseline. A zero baseline
regresses when the candidate rises above the baseline's p90; a gated metric the candidate lost, and
more failed runs or drain timeouts in the candidate, regress too.
"""

import collections

from xtrp.metrics import summarize

KEY_FIELDS = ("display_kind", "wm", "rtt_ms", "vnc_encoding", "size", "font", "variant", "workload")

# +1 higher is better, -1 lower is better, 0 informational (never flagged).
# Gated metrics are outcomes. Their components (elapsed_s + drain_s = total_s) and structure
# counters (how the encoder split frames into rects/updates, how many damage events) are
# informational: they move with timing phase from run to run while the outcome does not.
METRIC_DIRECTION = {m: -1 for m in (
    "term_cpu_s", "xserver_cpu_s", "damage_area_px", "latency_ms", "e2e_latency_ms",
    "total_s", "vnc_bytes", "x11_c2s_bytes", "x11_s2c_bytes", "x11_replies", "x11_requests",
    "x11_image_bytes", "startup_x11_replies",
    # keys followed by a separate later paint: the first damage may not be the echo, so more of them
    # in the candidate means its latency_ms needs checking before it is believed
    "latency_multi_paint")}
METRIC_DIRECTION.update({
    "throughput_mb_s": 1,
    "frames": 1,                 # fullscreen-redraw frames written in its fixed time: more = kept up
    "vnc_copyrect_area": 0,      # more CopyRect is the goal of scroll-by-copy, not a regression
    "elapsed_s": 0, "drain_s": 0, "vnc_rects": 0, "vnc_updates": 0, "damage_events": 0,
    # Launch time is bimodal (about 1 in 4 launches lands ~40 ms later, whatever the build), so a
    # median of a few samples cannot hold 5%; startup is not a goal of this project either.
    # startup_x11_replies (deterministic, matters over a remote X link) stays gated.
    "startup_ms": 0,
    "failed_runs": -1, "drain_timeouts": -1,     # health rows: any increase in the candidate regresses
})
HEALTH = ("failed_runs", "drain_timeouts")




def direction(metric, workload):
    """METRIC_DIRECTION, except that damage_area_px is informational for throughput workloads:
    during bulk output it is frames x window area, so one frame of phase moves it ~6%."""
    if metric == "damage_area_px" and _kind(workload) == "throughput":
        return 0
    return METRIC_DIRECTION.get(metric, 0)


def _kind(workload):
    from xtrp.workloads import WORKLOADS
    w = WORKLOADS.get(workload)
    return w.kind if w else None


class PlatformMismatch(ValueError):
    def __init__(self, base_tags, cand_tags):
        self.base_tags, self.cand_tags = base_tags, cand_tags
        ValueError.__init__(self, "refusing to compare %s with %s" % ("/".join(base_tags), "/".join(cand_tags)))


def _tags(records):
    return sorted({r.get("platform", {}).get("tag", "?") for r in records})


def _group(r):
    return tuple(r["key"][f] for f in KEY_FIELDS)


def _collect(records):
    """OrderedDict {group key tuple: {metric: [one value per run]}}, errored runs left out."""
    out = collections.OrderedDict()
    for r in records:
        if r.get("flags", {}).get("errors"):
            continue
        bucket = out.setdefault(_group(r), {})
        for metric, value in r.get("metrics", {}).items():
            if isinstance(value, list):
                med = summarize([v for v in value if v is not None])["median"]
                if med is not None:
                    bucket.setdefault(metric, []).append(med)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                bucket.setdefault(metric, []).append(value)
    return out


def _health(records):
    """OrderedDict {group key tuple: {"failed_runs": n, "drain_timeouts": n}} over every record."""
    out = collections.OrderedDict()
    for r in records:
        h = out.setdefault(_group(r), dict.fromkeys(HEALTH, 0))
        flags = r.get("flags", {})
        h["failed_runs"] += 1 if flags.get("errors") else 0
        h["drain_timeouts"] += 1 if flags.get("drain_timeout") else 0
    return out


def _judge(row, metric, threshold_pct, cross_platform):
    b, c = row["base"]["median"], row["cand"]["median"]
    if b is None or c is None:
        row["note"] = "no data"
        return
    sign = direction(metric, row["key"]["workload"])
    if b == 0:
        if c != 0:
            row["note"] = "base median 0"
            if sign < 0 and not cross_platform:
                row["regression"] = c > max(0, row["base"]["p90"])
        return
    change = (c - b) / abs(b) * 100.0
    row["delta_pct"] = -change if sign < 0 else change
    row["noise_pct"] = 100.0 * (row["base"]["p90"] - row["base"]["p10"]) / abs(b)
    if sign != 0 and not cross_platform:
        row["regression"] = row["delta_pct"] < -max(threshold_pct, row["noise_pct"])


def compare(base, cand, threshold_pct=5.0, cross_platform=False):
    """Rows comparing two record sets; raises PlatformMismatch across platforms unless cross_platform."""
    base_tags, cand_tags = _tags(base), _tags(cand)
    if not cross_platform and len(set(base_tags) | set(cand_tags)) > 1:
        raise PlatformMismatch(base_tags, cand_tags)
    b_groups, c_groups = _collect(base), _collect(cand)
    b_health, c_health = _health(base), _health(cand)
    order = []
    for gk in list(b_groups) + list(c_groups) + list(b_health) + list(c_health):
        if gk not in order:
            order.append(gk)
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
                row["regression"] = direction(metric, gk[-1]) != 0 and not cross_platform
            else:
                _judge(row, metric, threshold_pct, cross_platform)
            rows.append(row)
        bh = b_health.get(gk, dict.fromkeys(HEALTH, 0))
        ch = c_health.get(gk, dict.fromkeys(HEALTH, 0))
        for metric in HEALTH:
            if bh[metric] or ch[metric]:
                rows.append({"key": dict(zip(KEY_FIELDS, gk)), "metric": metric,
                             "base": summarize([bh[metric]]), "cand": summarize([ch[metric]]),
                             "delta_pct": None, "noise_pct": None, "note": "run health",
                             "regression": ch[metric] > bh[metric] and not cross_platform})
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
            lines.append("- %s `%s` (%s/%s rtt=%s %s): %s -> %s (%s%%, noise %s%%)%s" % (
                k["workload"], r["metric"], k["display_kind"], k["wm"], k["rtt_ms"], _config(k),
                _fmt(r["base"]["median"]), _fmt(r["cand"]["median"]), _pct(r["delta_pct"]),
                "-" if r["noise_pct"] is None else "%.1f" % r["noise_pct"],
                " [%s]" % r["note"] if r.get("note") else ""))
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
