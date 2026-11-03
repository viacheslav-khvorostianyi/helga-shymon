#!/usr/bin/env bash
# Push code to the server and restart. Usage: deploy/deploy.sh [host]
set -euo pipefail
HOST="${1:-helga-shymon.com}"
KEY="${KEY:-$HOME/.ssh/helga-shymon.pem}"
SSH="ssh -i $KEY -o StrictHostKeyChecking=accept-new"
cd "$(dirname "$0")/.."

rsync -az --delete -e "$SSH" \
  --exclude .venv --exclude instance --exclude uploads --exclude .env \
  --exclude .idea --exclude __pycache__ --exclude '*.pyc' --exclude .git \
  ./ "ubuntu@$HOST:/opt/helga/"

$SSH "ubuntu@$HOST" bash -s <<'REMOTE'
set -euo pipefail
cd /opt/helga
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
chmod -R g+rX /opt/helga
sudo cp deploy/helga.service /etc/systemd/system/helga.service
sudo systemctl daemon-reload
sudo systemctl enable helga >/dev/null 2>&1
sudo systemctl restart helga
REMOTE
echo "Deployed to $HOST"
