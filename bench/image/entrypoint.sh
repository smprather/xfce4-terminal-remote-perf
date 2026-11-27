#!/bin/sh
# Give the arbitrary runtime uid (docker run --user) a passwd entry, so
# dbus-daemon, GLib and Python's getpass can resolve it. Throwaway
# containers only: the image makes /etc/passwd writable for this.
if ! id -un >/dev/null 2>&1; then
    echo "xtrp:x:$(id -u):$(id -g):xtrp:${HOME:-/tmp/xtrp-home}:/bin/sh" >> /etc/passwd
fi
exec "$@"
