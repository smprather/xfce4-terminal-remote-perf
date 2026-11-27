#!/bin/sh
# Fetch, sha256-verify and install the artifacts pinned in pins.json:
# nvim (glibc-2.17 build) -> /opt/nvim, tmux (source) -> /usr/local,
# CaskaydiaCove Nerd Font Mono -> /usr/share/fonts/caskaydia.
# Runs once, during the bench image build:  install-pinned.sh <pins.json>
set -eu

pins=$1
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

pin() {
    python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]][sys.argv[3]])' \
        "$pins" "$1" "$2"
}

fetch() {
    url=$(pin "$1" url)
    sum=$(pin "$1" sha256)
    out="$work/$(basename "$url")"
    curl -fsSL --retry 3 -o "$out" "$url"
    echo "$sum  $out" | sha256sum -c - >&2
    echo "$out"
}

f=$(fetch nvim)
mkdir -p /opt/nvim
tar -xzf "$f" -C /opt/nvim --strip-components=1

f=$(fetch tmux)
mkdir "$work/tmux"
tar -xzf "$f" -C "$work/tmux" --strip-components=1
(
    cd "$work/tmux"
    ./configure --prefix=/usr/local >/dev/null
    make -j"$(nproc)" >/dev/null
    make install >/dev/null
)

f=$(fetch nerd-font-caskaydia)
mkdir -p /usr/share/fonts/caskaydia
unzip -q -j "$f" 'CaskaydiaCoveNerdFontMono-*.ttf' -d /usr/share/fonts/caskaydia
fc-cache -f >/dev/null
