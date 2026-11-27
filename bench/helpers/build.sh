#!/bin/sh
# Build the xlat and testwin helpers into bench/helpers/bin/<platform tag>/.
# The tag follows xtrp.platform.platform_tag(): el<major> on RHEL-family
# systems, otherwise "host". el8, el9 and the host share the bind-mounted
# tree, so each gets its own directory.
set -eu

here=$(cd "$(dirname "$0")" && pwd -P)

tag=host
if [ -r /etc/os-release ]; then
    os_id=$(. /etc/os-release && echo "${ID:-} ${ID_LIKE:-}")
    os_ver=$(. /etc/os-release && echo "${VERSION_ID:-}")
    case " $os_id " in
        *" rhel "*|*" centos "*)
            major=${os_ver%%.*}
            case "$major" in
                ''|*[!0-9]*) ;;
                *) tag="el$major" ;;
            esac
            ;;
    esac
fi

out="$here/bin/$tag"
mkdir -p "$out"
for prog in xlat testwin; do
    cc -std=c99 -O2 -Wall -Wextra -Werror -o "$out/$prog.tmp.$$" "$here/$prog.c" \
        -lX11 -lXtst -lXdamage -lXfixes -lXext
    mv -f "$out/$prog.tmp.$$" "$out/$prog"
done
