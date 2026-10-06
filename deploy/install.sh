#!/usr/bin/env bash
# Fresh Ubuntu VM provisioning only. Never deletes/moves existing operational data.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run with sudo bash deploy/install.sh' >&2; exit 1; }
ROOT=/opt/loderunner
DATA=/var/lib/loderunner/live-dashboard
[[ $(realpath "$(dirname "$0")/..") == "$ROOT" ]] || { echo "Clone into $ROOT first" >&2; exit 1; }
# shellcheck source=/dev/null
source /etc/os-release
[[ $ID == ubuntu && $VERSION_ID == 24.04 ]] || { echo 'Ubuntu 24.04 required' >&2; exit 1; }
[[ $(uname -m) == x86_64 ]] || { echo 'This deployment targets e2 x86_64' >&2; exit 1; }
if systemctl is-active --quiet loderunner; then
    echo 'Stop loderunner explicitly before provisioning/updating.' >&2; exit 1
fi
command -v nginx >/dev/null
[[ -x "$ROOT/backend/.venv/bin/python" ]] || { echo 'Install the venv and dependencies first' >&2; exit 1; }
if ! id loderunner >/dev/null 2>&1; then
    useradd --system --home-dir /var/lib/loderunner --shell /usr/sbin/nologin loderunner
fi
install -d -o loderunner -g loderunner -m 0750 /var/lib/loderunner "$DATA"
install -d -m 0755 "$ROOT/data"
LINK="$ROOT/data/live-dashboard"
if [[ -L $LINK ]]; then
    [[ $(readlink -f "$LINK") == "$DATA" ]] || { echo 'Unexpected data symlink; inspect manually' >&2; exit 1; }
elif [[ -e $LINK ]]; then
    echo "$LINK already exists. Back it up and migrate manually; not overwritten." >&2; exit 1
else
    ln -s "$DATA" "$LINK"
fi
install -d -m 0700 /etc/loderunner
if [[ ! -e /etc/loderunner/loderunner.env ]]; then
    install -m 0600 "$ROOT/deploy/loderunner.env.example" /etc/loderunner/loderunner.env
fi
install -m 0644 "$ROOT/deploy/loderunner.service" /etc/systemd/system/loderunner.service
install -m 0644 "$ROOT/deploy/nginx-loderunner.conf" /etc/nginx/sites-available/loderunner
if [[ -L /etc/nginx/sites-enabled/default && $(readlink -f /etc/nginx/sites-enabled/default) == /etc/nginx/sites-available/default ]]; then
    unlink /etc/nginx/sites-enabled/default
fi
if [[ -e /etc/nginx/sites-enabled/loderunner || -L /etc/nginx/sites-enabled/loderunner ]]; then
    [[ $(readlink -f /etc/nginx/sites-enabled/loderunner) == /etc/nginx/sites-available/loderunner ]] || { echo 'Unexpected nginx link' >&2; exit 1; }
else
    ln -s /etc/nginx/sites-available/loderunner /etc/nginx/sites-enabled/loderunner
fi
runuser -u loderunner -- test -r "$ROOT/frontend/analysis/index.html"
runuser -u loderunner -- test -w "$DATA"
runuser -u loderunner -- env PYTHONPATH="$ROOT/backend" PYTHONDONTWRITEBYTECODE=1 "$ROOT/backend/.venv/bin/python" -c 'import app.main; import sqlite3; print("App import and SQLite available")'
systemd-analyze verify /etc/systemd/system/loderunner.service
nginx -t
systemctl daemon-reload
echo 'Installed. Set /etc/loderunner/loderunner.env, then enable/start services as documented.'
echo 'No firewall rules, secrets, data migration, or cloud resources were changed.'
