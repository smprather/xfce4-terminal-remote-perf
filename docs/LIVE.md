# Running xtrp on a real VM

`xtrp-live.tar.gz` measures xfce4-terminal on a real desktop session, with
no root and no installs. It needs only the system Python 3 (EL8's
`platform-python` is enough).

Everything it prints has already been through `scrub`: host names, user
names, IP addresses, and site paths come out as `<host>`, `<user>`,
`<ip>`, and `<path>`. Still, read the output before pasting it anywhere.

## What it does to your desktop

`live latency` types only `a` and `BackSpace`, in equal numbers, and only
while the target window has keyboard focus. It checks focus before every
key. If focus is anywhere else, it stops, prints `refused`, and types
nothing. It never types Return.

`live startup` opens a new xfce4-terminal window five times, waits for each
to appear, and closes it again. Nothing is typed into those windows.

If `live latency` prints a note that some keys "painted twice", the
terminal's blinking cursor was probably repainting between keystrokes, which
can make the numbers look better than they are. Turn cursor blinking off in
that terminal's preferences and run it again.

## Setup (once per VM)

```sh
mkdir -p ~/xtrp && tar -C ~/xtrp -xzf xtrp-live.tar.gz
cd ~/xtrp/xtrp-live
```

## T1: the terminal runs on the remote-desktop VM (A)

Run these inside your desktop session (TigerVNC, NoMachine, or ETX), in an
xfce4-terminal window:

```sh
./run diag > diag.json
./run live latency            # measures this terminal; press Enter, then hands off for ~7 s
./run live startup            # opens and closes a new terminal window 5 times
```

For damage and X server CPU while you work, find the terminal's window id
with `echo $WINDOWID`. Then run this from a second terminal while you drive
the first (scroll in nvim, `cat` a big file, use tmux):

```sh
./run live watch --window $ID --seconds 30
```

Please do this once in a GNOME Classic session and once in a MATE session,
under each of TigerVNC, NoMachine, and ETX.

## T2: the terminal runs on a farm node (B), displaying on A

The terminal runs on B with `DISPLAY=A:n`. Unpack the bundle on B as well
(same Setup steps).

1. On B, so the link itself is measured (round-trip time from B to A's X
   server, and how long a terminal takes to open over it):

   ```sh
   DISPLAY=A:n ./run diag > diag-t2-b.json
   DISPLAY=A:n ./run live startup
   ```

2. On B: `DISPLAY=A:n xfce4-terminal &`, and run `cat` in it.
3. On A, in a terminal of that session (xtrp talks to the X server
   directly there):

   ```sh
   ./run diag > diag-t2.json
   ./run live latency --pick     # press Enter, click the B terminal, then click into it again within 5 s
   ./run live watch --window $ID --seconds 30   # $ID: the "window" value printed by live latency
   ```

## What to send back

For each setup, paste the following with a one-line label such as
`T1 MATE TigerVNC`:

- `diag.json` (for T2, both `diag-t2-b.json` from B and `diag-t2.json` from A);
- the JSON printed by `live latency`, and any note it printed;
- the JSON printed by `live startup`;
- the JSON printed by `live watch`.
