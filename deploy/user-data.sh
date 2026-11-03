#!/bin/bash
set -eux
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx rsync sqlite3
id helga || useradd --system --home /opt/helga --shell /usr/sbin/nologin helga
mkdir -p /opt/helga/uploads /opt/helga/instance
chown -R ubuntu:helga /opt/helga
chmod 775 /opt/helga /opt/helga/uploads /opt/helga/instance
usermod -aG helga www-data
rm -f /etc/nginx/sites-enabled/default
