/* Shared helpers for xlat.c and testwin.c: monotonic time, sleeping,
 * stop signals, and waiting for X events with a deadline. */
#ifndef XTRP_XCOMMON_H
#define XTRP_XCOMMON_H

#include <X11/Xlib.h>
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <string.h>
#include <sys/select.h>
#include <time.h>

static volatile sig_atomic_t g_stop = 0;

static void on_stop_signal(int sig)
{
    (void)sig;
    g_stop = 1;
}

/* SIGTERM/SIGINT set g_stop and interrupt select() (no SA_RESTART). */
static void install_stop_handlers(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_stop_signal;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);
}

static int64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static inline void sleep_ns(int64_t ns)
{
    struct timespec ts;
    if (ns <= 0)
        return;
    ts.tv_sec = (time_t)(ns / 1000000000LL);
    ts.tv_nsec = (long)(ns % 1000000000LL);
    while (nanosleep(&ts, &ts) != 0 && errno == EINTR && !g_stop)
        ;
}

/* Wait until an X event is queued or `deadline` (monotonic ns) passes.
 * Returns 1 when an event is pending, 0 on deadline or stop signal. */
static int wait_event(Display *dpy, int64_t deadline)
{
    int fd = ConnectionNumber(dpy);
    for (;;) {
        fd_set rfds;
        struct timeval tv;
        int64_t left;
        if (XPending(dpy))
            return 1;
        if (g_stop)
            return 0;
        left = deadline - now_ns();
        if (left <= 0)
            return 0;
        FD_ZERO(&rfds);
        FD_SET(fd, &rfds);
        tv.tv_sec = (time_t)(left / 1000000000LL);
        tv.tv_usec = (long)((left % 1000000000LL) / 1000);
        if (select(fd + 1, &rfds, NULL, NULL, &tv) < 0 && errno != EINTR)
            return 0;
    }
}

#endif
