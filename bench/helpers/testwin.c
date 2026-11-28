/* testwin: deterministic X client for the xtrp helper/RFB/proxy tests.
 *
 *   testwin --title T --delay-ms D --rect WxH [--damage-forever] [--second-paint-ms M]
 *
 * Maps a 400x300 window titled T. D ms after each KeyPress it fills a WxH rect
 * at (0,0), alternating black and white; with --second-paint-ms it fills the
 * same size at (0,100) M ms after that. Paints are scheduled, never slept on,
 * so the --damage-forever ticker (a 10x10 rect at (200,200) every 50 ms) keeps
 * running meanwhile. On SIGTERM/SIGINT it prints {"keys":count} and exits 0.
 */
#define _POSIX_C_SOURCE 200809L

#include <X11/Xatom.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "xcommon.h"

static void die(const char *msg)
{
    fprintf(stderr, "testwin: %s\n", msg);
    exit(1);
}

int main(int argc, char **argv)
{
    const char *title = NULL;
    long delay_ms = 0, second_ms = -1;
    unsigned int rw = 10, rh = 10;
    int damage_forever = 0, i, scr, keys = 0, phase = 0, tick_phase = 0;
    Display *dpy;
    Window w;
    GC gc;
    unsigned long black, white;
    int64_t next_tick, paint_at = -1, second_at = -1;

    setvbuf(stdout, NULL, _IOLBF, 0);
    for (i = 1; i < argc; i++) {
        const char *a = argv[i], *v = i + 1 < argc ? argv[i + 1] : NULL;
        if (strcmp(a, "--title") == 0 && v) {
            title = v;
            i++;
        } else if (strcmp(a, "--delay-ms") == 0 && v) {
            delay_ms = strtol(v, NULL, 10);
            i++;
        } else if (strcmp(a, "--rect") == 0 && v) {
            if (sscanf(v, "%ux%u", &rw, &rh) != 2)
                die("--rect wants WxH");
            i++;
        } else if (strcmp(a, "--damage-forever") == 0) {
            damage_forever = 1;
        } else if (strcmp(a, "--second-paint-ms") == 0 && v) {
            second_ms = strtol(v, NULL, 10);
            i++;
        } else {
            die("usage: testwin --title T --delay-ms D --rect WxH [--damage-forever] [--second-paint-ms M]");
        }
    }
    if (!title)
        die("--title is required");

    install_stop_handlers();
    dpy = XOpenDisplay(NULL);
    if (!dpy)
        die("cannot open display");
    scr = DefaultScreen(dpy);
    black = BlackPixel(dpy, scr);
    white = WhitePixel(dpy, scr);
    w = XCreateSimpleWindow(dpy, RootWindow(dpy, scr), 0, 0, 400, 300, 0, black, white);
    XStoreName(dpy, w, title);
    XChangeProperty(dpy, w, XInternAtom(dpy, "_NET_WM_NAME", False),
                    XInternAtom(dpy, "UTF8_STRING", False), 8, PropModeReplace,
                    (const unsigned char *)title, (int)strlen(title));
    XSelectInput(dpy, w, KeyPressMask | ExposureMask | StructureNotifyMask);
    gc = XCreateGC(dpy, w, 0, NULL);
    XMapWindow(dpy, w);
    XFlush(dpy);

    next_tick = now_ns() + 50000000LL;
    while (!g_stop) {
        int64_t deadline = damage_forever ? next_tick : now_ns() + 100000000LL;
        if (paint_at >= 0 && paint_at < deadline)
            deadline = paint_at;
        if (second_at >= 0 && second_at < deadline)
            deadline = second_at;
        if (wait_event(dpy, deadline)) {
            XEvent ev;
            XNextEvent(dpy, &ev);
            if (ev.type == KeyPress) {
                keys++;
                paint_at = now_ns() + (int64_t)delay_ms * 1000000LL;
            }
        }
        if (paint_at >= 0 && now_ns() >= paint_at) {
            XSetForeground(dpy, gc, phase ? white : black);
            phase ^= 1;
            XFillRectangle(dpy, w, gc, 0, 0, rw, rh);
            XFlush(dpy);
            paint_at = -1;
            if (second_ms >= 0)
                second_at = now_ns() + (int64_t)second_ms * 1000000LL;
        }
        if (second_at >= 0 && now_ns() >= second_at) {
            XFillRectangle(dpy, w, gc, 0, 100, rw, rh);
            XFlush(dpy);
            second_at = -1;
        }
        if (damage_forever && now_ns() >= next_tick) {
            XSetForeground(dpy, gc, tick_phase ? white : black);
            tick_phase ^= 1;
            XFillRectangle(dpy, w, gc, 200, 200, 10, 10);
            XFlush(dpy);
            next_tick += 50000000LL;
        }
    }
    printf("{\"keys\":%d}\n", keys);
    XFreeGC(dpy, gc);
    XCloseDisplay(dpy);
    return 0;
}
