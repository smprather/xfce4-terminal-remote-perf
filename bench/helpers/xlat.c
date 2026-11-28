/* xlat: X-side timing helper for the xtrp harness.
 *
 * Every output line is one JSON object; all times are CLOCK_MONOTONIC ns.
 *   xlat info
 *   xlat wait-window --title T --timeout-ms N        (exit 3 on timeout)
 *   xlat focus --window W
 *   xlat latency --window W --samples N --interval-ms M --timeout-ms T [--require-focus]
 *                [--region X,Y,W,H]                  (exit 2 when not focused)
 *   xlat damage --window W     ({"ready":..} once armed, then rects until SIGTERM/SIGINT)
 *   xlat pick
 *   xlat geometry --window W  (position on the root, size, and the root's size)
 *   xlat fill --window W      (move to 0,0 and resize to the whole root; for the no-WM case)
 * The display comes from $DISPLAY. Other failures exit 1.
 */
#define _POSIX_C_SOURCE 200809L

#include <X11/Xatom.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/cursorfont.h>
#include <X11/extensions/XTest.h>
#include <X11/extensions/Xdamage.h>
#include <X11/keysym.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "xcommon.h"

static int g_xerr = 0;

static int on_xerror(Display *dpy, XErrorEvent *e)
{
    (void)dpy;
    g_xerr = e->error_code;
    return 0;
}

static void die(const char *msg)
{
    fprintf(stderr, "xlat: %s\n", msg);
    exit(1);
}

static void json_str(const char *s)
{
    const unsigned char *p;
    if (!s) {
        fputs("null", stdout);
        return;
    }
    putchar('"');
    for (p = (const unsigned char *)s; *p; p++) {
        if (*p == '"' || *p == '\\')
            printf("\\%c", *p);
        else if (*p < 0x20)
            printf("\\u%04x", *p);
        else
            putchar(*p);
    }
    putchar('"');
}

/* Property data (caller XFrees) or NULL; *n = item count. */
static unsigned char *get_prop(Display *dpy, Window w, Atom prop, Atom type, unsigned long *n)
{
    Atom actual = None;
    int fmt = 0;
    unsigned long nitems = 0, after = 0;
    unsigned char *data = NULL;
    *n = 0;
    g_xerr = 0;
    if (XGetWindowProperty(dpy, w, prop, 0, 1L << 20, False, type, &actual, &fmt,
                           &nitems, &after, &data) != Success || g_xerr) {
        return NULL;
    }
    if (actual == None || !data) {
        if (data)
            XFree(data);
        return NULL;
    }
    *n = nitems;
    return data;
}

/* malloc'd _NET_WM_NAME (UTF-8) or WM_NAME, or NULL. */
static char *window_name(Display *dpy, Window w)
{
    Atom net = XInternAtom(dpy, "_NET_WM_NAME", False);
    Atom utf8 = XInternAtom(dpy, "UTF8_STRING", False);
    unsigned long n;
    unsigned char *d = get_prop(dpy, w, net, utf8, &n);
    char *s;
    if (!d)
        d = get_prop(dpy, w, XA_WM_NAME, AnyPropertyType, &n);
    if (!d)
        return NULL;
    s = strndup((const char *)d, n);
    XFree(d);
    return s;
}

static int is_viewable(Display *dpy, Window w)
{
    XWindowAttributes a;
    g_xerr = 0;
    if (!XGetWindowAttributes(dpy, w, &a) || g_xerr)
        return 0;
    return a.map_state == IsViewable;
}

/* Depth-first search of viewable windows for one titled `title`. */
static Window find_titled(Display *dpy, Window w, const char *title, int is_root)
{
    Window root_ret, parent, *kids = NULL, found = None;
    unsigned int nk = 0, i;
    if (!is_root) {
        char *name;
        if (!is_viewable(dpy, w))
            return None;
        name = window_name(dpy, w);
        if (name && strcmp(name, title) == 0) {
            free(name);
            return w;
        }
        free(name);
    }
    g_xerr = 0;
    if (!XQueryTree(dpy, w, &root_ret, &parent, &kids, &nk) || g_xerr)
        return None;
    for (i = 0; i < nk && found == None; i++)
        found = find_titled(dpy, kids[i], title, 0);
    if (kids)
        XFree(kids);
    return found;
}

static Window parent_of(Display *dpy, Window w)
{
    Window root_ret, parent = None, *kids = NULL;
    unsigned int nk = 0;
    g_xerr = 0;
    if (!XQueryTree(dpy, w, &root_ret, &parent, &kids, &nk) || g_xerr)
        return None;
    if (kids)
        XFree(kids);
    return parent;
}

/* 1 if `a` is `b` or an ancestor of `b`, stopping below the root. */
static int is_ancestor_or_self(Display *dpy, Window a, Window b, Window root)
{
    while (b != None && b != root) {
        if (b == a)
            return 1;
        b = parent_of(dpy, b);
    }
    return 0;
}

/* Keyboard focus is on `w`, a descendant of it, or a non-root ancestor (WM frame). */
static int has_focus(Display *dpy, Window w)
{
    Window root = DefaultRootWindow(dpy), f = None;
    int revert;
    XGetInputFocus(dpy, &f, &revert);
    if (f == None || f == PointerRoot || f == root)
        return 0;
    return is_ancestor_or_self(dpy, w, f, root) || is_ancestor_or_self(dpy, f, w, root);
}

static int cmp_double(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

static int mode_info(Display *dpy)
{
    Window root = DefaultRootWindow(dpy);
    int scr = DefaultScreen(dpy), next = 0, i, frame_drawn = 0;
    char **exts = XListExtensions(dpy, &next);
    char cm_name[32];
    Atom check = XInternAtom(dpy, "_NET_SUPPORTING_WM_CHECK", False);
    Atom supported = XInternAtom(dpy, "_NET_SUPPORTED", False);
    Atom frame_atom = XInternAtom(dpy, "_NET_WM_FRAME_DRAWN", False);
    unsigned long n;
    unsigned char *d;
    char *wm_name = NULL;
    double rtt[20];

    d = get_prop(dpy, root, check, XA_WINDOW, &n);
    if (d && n >= 1) {
        Window wm = (Window)((unsigned long *)d)[0];
        wm_name = window_name(dpy, wm);
        if (!wm_name)
            wm_name = strdup("");
    }
    if (d)
        XFree(d);

    d = get_prop(dpy, root, supported, XA_ATOM, &n);
    if (d) {
        unsigned long k;
        for (k = 0; k < n; k++)
            if ((Atom)((unsigned long *)d)[k] == frame_atom)
                frame_drawn = 1;
        XFree(d);
    }

    snprintf(cm_name, sizeof cm_name, "_NET_WM_CM_S%d", scr);

    for (i = 0; i < 20; i++) {
        Window f;
        int revert;
        int64_t t0 = now_ns();
        XGetInputFocus(dpy, &f, &revert);
        rtt[i] = (double)(now_ns() - t0) / 1000.0;
    }
    qsort(rtt, 20, sizeof rtt[0], cmp_double);

    fputs("{\"vendor\":", stdout);
    json_str(ServerVendor(dpy));
    printf(",\"release\":%d,\"extensions\":[", VendorRelease(dpy));
    for (i = 0; i < next; i++) {
        if (i)
            putchar(',');
        json_str(exts[i]);
    }
    fputs("],\"wm_name\":", stdout);
    json_str(wm_name);
    printf(",\"frame_drawn\":%s,\"cm_owner\":%s,\"depth\":%d,\"width\":%d,\"height\":%d,"
           "\"rtt_us_median\":%.3f}\n",
           frame_drawn ? "true" : "false",
           XGetSelectionOwner(dpy, XInternAtom(dpy, cm_name, False)) != None ? "true" : "false",
           DefaultDepth(dpy, scr), DisplayWidth(dpy, scr), DisplayHeight(dpy, scr),
           (rtt[9] + rtt[10]) / 2.0);
    free(wm_name);
    if (exts)
        XFreeExtensionList(exts);
    return 0;
}

static int mode_wait_window(Display *dpy, const char *title, long timeout_ms)
{
    int64_t deadline = now_ns() + (int64_t)timeout_ms * 1000000LL;
    Window root = DefaultRootWindow(dpy);
    for (;;) {
        Window w = find_titled(dpy, root, title, 1);
        if (w != None) {
            printf("{\"window\":%lu,\"t_ns\":%lld}\n", (unsigned long)w, (long long)now_ns());
            return 0;
        }
        if (now_ns() >= deadline)
            return 3;
        sleep_ns(5000000LL);
    }
}

static int mode_focus(Display *dpy, Window w)
{
    g_xerr = 0;
    XSetInputFocus(dpy, w, RevertToParent, CurrentTime);
    XSync(dpy, False);
    if (g_xerr)
        die("XSetInputFocus failed");
    return 0;
}

static int mode_geometry(Display *dpy, Window w)
{
    XWindowAttributes wa, ra;
    Window child;
    int x = 0, y = 0;
    g_xerr = 0;
    if (!XGetWindowAttributes(dpy, w, &wa) || g_xerr)
        die("XGetWindowAttributes failed (bad window?)");
    XGetWindowAttributes(dpy, DefaultRootWindow(dpy), &ra);
    XTranslateCoordinates(dpy, w, DefaultRootWindow(dpy), 0, 0, &x, &y, &child);
    printf("{\"x\":%d,\"y\":%d,\"width\":%d,\"height\":%d,\"root_width\":%d,\"root_height\":%d}\n",
           x, y, wa.width, wa.height, ra.width, ra.height);
    return 0;
}

static int mode_fill(Display *dpy, Window w)
{
    XWindowAttributes ra;
    XGetWindowAttributes(dpy, DefaultRootWindow(dpy), &ra);
    g_xerr = 0;
    XMoveResizeWindow(dpy, w, 0, 0, (unsigned)ra.width, (unsigned)ra.height);
    XSync(dpy, False);
    if (g_xerr)
        die("XMoveResizeWindow failed (bad window?)");
    return 0;
}

static Damage damage_on(Display *dpy, Window w, int *event_base)
{
    int err_base;
    Damage dmg;
    if (!XDamageQueryExtension(dpy, event_base, &err_base))
        die("DAMAGE extension missing");
    g_xerr = 0;
    dmg = XDamageCreate(dpy, w, XDamageReportRawRectangles);
    XSync(dpy, False);
    if (g_xerr)
        die("XDamageCreate failed (bad window?)");
    /* DamageCreate on a window reports its whole visible area once; that is
     * not drawing, so drop it before measuring. */
    while (XPending(dpy)) {
        XEvent ev;
        XNextEvent(dpy, &ev);
    }
    return dmg;
}

/* Damage from separate paints is at least this far apart; one paint's rectangles arrive together. */
#define PAINT_GAP_NS 2000000LL

typedef struct {
    int on;
    int x, y, w, h;
} WatchArea;

static int relevant(const XDamageNotifyEvent *de, const WatchArea *r)
{
    if (!r->on)
        return 1;
    return de->area.x < r->x + r->w && r->x < de->area.x + (int)de->area.width &&
           de->area.y < r->y + r->h && r->y < de->area.y + (int)de->area.height;
}

/* Per key: the first damage (in `region`, if given) is the sample. Damage keeps being read until the
 * next key is due, and "paints" counts the separate bursts: more than one means the first damage may
 * not be the echo (e.g. a cursor repaint first), which the caller reports instead of trusting it. */
static int mode_latency(Display *dpy, Window w, long samples, long interval_ms, long timeout_ms,
                        int require_focus, const WatchArea *region)
{
    int ev_base, maj, min, evb, errb;
    long i;
    Damage dmg;
    KeyCode keys[2];
    if (!XTestQueryExtension(dpy, &evb, &errb, &maj, &min))
        die("XTEST extension missing");
    if (require_focus && !has_focus(dpy, w)) {
        printf("{\"error\":\"not-focused\"}\n");
        return 2;
    }
    dmg = damage_on(dpy, w, &ev_base);
    keys[0] = XKeysymToKeycode(dpy, XK_a);
    keys[1] = XKeysymToKeycode(dpy, XK_BackSpace);
    for (i = 0; i < samples && !g_stop; i++) {
        int64_t t_inject, t_damage = -1, t_last = -1, t_paint = -1, deadline, collect_until;
        int paints = 0;
        KeyCode kc = keys[i % 2];
        XEvent ev;
        XSync(dpy, False);
        while (XPending(dpy))
            XNextEvent(dpy, &ev);
        if (require_focus && !has_focus(dpy, w)) {
            printf("{\"error\":\"not-focused\"}\n");
            XDamageDestroy(dpy, dmg);
            return 2;
        }
        t_inject = now_ns();
        XTestFakeKeyEvent(dpy, kc, True, CurrentTime);
        XTestFakeKeyEvent(dpy, kc, False, CurrentTime);
        XFlush(dpy);
        deadline = t_inject + (int64_t)timeout_ms * 1000000LL;
        collect_until = t_inject + (int64_t)interval_ms * 1000000LL;
        while (wait_event(dpy, t_damage < 0 ? deadline : collect_until)) {
            int64_t t;
            XNextEvent(dpy, &ev);
            if (ev.type != ev_base + XDamageNotify || !relevant((XDamageNotifyEvent *)&ev, region))
                continue;
            t = now_ns();
            if (t_damage < 0) {
                t_damage = t_paint = t;
                paints = 1;
                if (collect_until < t + 20000000LL)
                    collect_until = t + 20000000LL;
            } else if (t - t_last > PAINT_GAP_NS) {
                paints++;
                t_paint = t;
            }
            t_last = t;
        }
        if (t_damage < 0)
            printf("{\"i\":%ld,\"inject_ns\":%lld,\"damage_ns\":null,\"paints\":0}\n", i,
                   (long long)t_inject);
        else
            printf("{\"i\":%ld,\"inject_ns\":%lld,\"damage_ns\":%lld,\"paints\":%d,\"last_ns\":%lld}\n", i,
                   (long long)t_inject, (long long)t_damage, paints, (long long)t_paint);
        sleep_ns(t_inject + (int64_t)interval_ms * 1000000LL - now_ns());
    }
    XDamageDestroy(dpy, dmg);
    XSync(dpy, False);
    return 0;
}

static int mode_damage(Display *dpy, Window w)
{
    int ev_base;
    Damage dmg = damage_on(dpy, w, &ev_base);
    printf("{\"ready\":true,\"t_ns\":%lld}\n", (long long)now_ns());
    while (!g_stop) {
        if (!wait_event(dpy, now_ns() + 100000000LL))
            continue;
        while (XPending(dpy)) {
            XEvent ev;
            XNextEvent(dpy, &ev);
            if (ev.type == ev_base + XDamageNotify) {
                XDamageNotifyEvent *de = (XDamageNotifyEvent *)&ev;
                printf("{\"t_ns\":%lld,\"x\":%d,\"y\":%d,\"w\":%u,\"h\":%u}\n",
                       (long long)now_ns(), de->area.x, de->area.y,
                       (unsigned)de->area.width, (unsigned)de->area.height);
            }
        }
    }
    XDamageDestroy(dpy, dmg);
    XSync(dpy, False);
    return 0;
}

/* `w` if it carries WM_STATE, else the first descendant that does, else `w`. */
static Window client_window(Display *dpy, Window w, Atom wm_state, int depth)
{
    Window root_ret, parent, *kids = NULL, found = None;
    unsigned int nk = 0, i;
    unsigned long n;
    unsigned char *d = get_prop(dpy, w, wm_state, AnyPropertyType, &n);
    if (d) {
        XFree(d);
        return w;
    }
    if (depth > 8)
        return None;
    g_xerr = 0;
    if (!XQueryTree(dpy, w, &root_ret, &parent, &kids, &nk) || g_xerr)
        return None;
    for (i = 0; i < nk && found == None; i++)
        found = client_window(dpy, kids[i], wm_state, depth + 1);
    if (kids)
        XFree(kids);
    return found;
}

static int mode_pick(Display *dpy)
{
    Window root = DefaultRootWindow(dpy), target, client;
    Cursor cursor = XCreateFontCursor(dpy, XC_crosshair);
    XEvent ev;
    if (XGrabPointer(dpy, root, False, ButtonPressMask, GrabModeAsync, GrabModeAsync, root,
                     cursor, CurrentTime) != GrabSuccess)
        die("cannot grab the pointer");
    do {
        XNextEvent(dpy, &ev);
    } while (ev.type != ButtonPress);
    XUngrabPointer(dpy, CurrentTime);
    XFreeCursor(dpy, cursor);
    target = ev.xbutton.subwindow != None ? ev.xbutton.subwindow : root;
    client = client_window(dpy, target, XInternAtom(dpy, "WM_STATE", False), 0);
    printf("{\"window\":%lu}\n", (unsigned long)(client != None ? client : target));
    return 0;
}

static long arg_long(const char *flag, const char *value)
{
    char *end;
    long v;
    if (!value)
        die("missing value for an option");
    v = strtol(value, &end, 0);
    if (*end || v < 0) {
        fprintf(stderr, "xlat: bad value for %s: %s\n", flag, value);
        exit(1);
    }
    return v;
}

int main(int argc, char **argv)
{
    const char *mode, *title = NULL;
    long window = 0, samples = 40, interval_ms = 120, timeout_ms = 2000;
    int require_focus = 0, i, rc;
    WatchArea region = {0, 0, 0, 0, 0};
    Display *dpy;

    setvbuf(stdout, NULL, _IOLBF, 0);
    if (argc < 2)
        die("usage: xlat info|wait-window|focus|latency|damage|pick|geometry|fill [options]");
    mode = argv[1];
    for (i = 2; i < argc; i++) {
        const char *a = argv[i], *v = i + 1 < argc ? argv[i + 1] : NULL;
        if (strcmp(a, "--window") == 0) {
            window = arg_long(a, v);
            i++;
        } else if (strcmp(a, "--samples") == 0) {
            samples = arg_long(a, v);
            i++;
        } else if (strcmp(a, "--interval-ms") == 0) {
            interval_ms = arg_long(a, v);
            i++;
        } else if (strcmp(a, "--timeout-ms") == 0) {
            timeout_ms = arg_long(a, v);
            i++;
        } else if (strcmp(a, "--title") == 0) {
            if (!v)
                die("missing value for --title");
            title = v;
            i++;
        } else if (strcmp(a, "--require-focus") == 0) {
            require_focus = 1;
        } else if (strcmp(a, "--region") == 0) {
            if (!v || sscanf(v, "%d,%d,%d,%d", &region.x, &region.y, &region.w, &region.h) != 4 ||
                region.w <= 0 || region.h <= 0)
                die("--region wants X,Y,W,H");
            region.on = 1;
            i++;
        } else {
            fprintf(stderr, "xlat: unknown option %s\n", a);
            return 1;
        }
    }

    install_stop_handlers();
    dpy = XOpenDisplay(NULL);
    if (!dpy)
        die("cannot open display");
    XSetErrorHandler(on_xerror);

    if (strcmp(mode, "info") == 0) {
        rc = mode_info(dpy);
    } else if (strcmp(mode, "wait-window") == 0) {
        if (!title)
            die("wait-window needs --title");
        rc = mode_wait_window(dpy, title, timeout_ms);
    } else if (strcmp(mode, "focus") == 0) {
        if (!window)
            die("focus needs --window");
        rc = mode_focus(dpy, (Window)window);
    } else if (strcmp(mode, "latency") == 0) {
        if (!window)
            die("latency needs --window");
        rc = mode_latency(dpy, (Window)window, samples, interval_ms, timeout_ms, require_focus, &region);
    } else if (strcmp(mode, "damage") == 0) {
        if (!window)
            die("damage needs --window");
        rc = mode_damage(dpy, (Window)window);
    } else if (strcmp(mode, "pick") == 0) {
        rc = mode_pick(dpy);
    } else if (strcmp(mode, "geometry") == 0) {
        if (!window)
            die("geometry needs --window");
        rc = mode_geometry(dpy, (Window)window);
    } else if (strcmp(mode, "fill") == 0) {
        if (!window)
            die("fill needs --window");
        rc = mode_fill(dpy, (Window)window);
    } else {
        fprintf(stderr, "xlat: unknown mode %s\n", mode);
        rc = 1;
    }
    XCloseDisplay(dpy);
    return rc;
}
