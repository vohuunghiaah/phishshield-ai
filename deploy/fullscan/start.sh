#!/bin/sh
set -eu
# Modifies only the dedicated container network namespace. Abort if any step fails.
# Both supported deployments use Docker bridge veth pairs. Fail before installing
# any rules if this entry point is launched on an ordinary host interface.
for device in /sys/class/net/*; do
    [ "${device##*/}" = lo ] && continue
    [ "$(cat "$device/type")" = 1 ] && [ "$(cat "$device/iflink")" != "$(cat "$device/ifindex")" ] || exit 1
done
[ -d /sys/class/net/eth0 ] || exit 1
nft -f /app/firewall.nft
# Deny the actual connected subnets as well, even with a custom Docker address pool.
python - <<'PY'
import ipaddress, struct, subprocess
with open("/proc/net/route") as routes:
    entries = [line.split() for line in routes.readlines()[1:]]
networks = set()
for row in entries:
    if int(row[1],16) and int(row[2],16) == 0:
        dest, mask = (str(ipaddress.IPv4Address(struct.pack("<I", int(x,16)))) for x in (row[1],row[7]))
        networks.add(str(ipaddress.IPv4Network((dest,mask),strict=False)))
if not networks:
    raise SystemExit("Missing dedicated network")
subprocess.run(["nft","add","element","inet","phishshield","attached_v4","{",", ".join(sorted(networks)),"}"],check=True)
PY
exec setpriv --reuid=65534 --regid=65534 --clear-groups --bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs python -m phishshield.inference.worker
