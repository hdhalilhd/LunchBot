#!/usr/bin/env bash
# MenuBot'u Ubuntu/Debian bir VM'e kurar.
#
# Kullanim (VM uzerinde, root ya da sudo ile):
#   sudo bash deploy/install-vm.sh
#
# Bu script proje klasorunun icinden calistirilmali.

set -euo pipefail

APP_DIR=/opt/menubot
SERVICE=menubot
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Paketler"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip rsync

echo "==> Saat dilimi"
timedatectl set-timezone Europe/Istanbul || true

echo "==> Kullanici: $SERVICE"
id -u "$SERVICE" &>/dev/null || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE"

echo "==> Dosyalar -> $APP_DIR"
mkdir -p "$APP_DIR"
rsync -a --delete \
  --exclude '.venv' --exclude '.git' --exclude '__pycache__' \
  --exclude '.env' \
  "$SRC_DIR/" "$APP_DIR/"

echo "==> Sanal ortam"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "!! $APP_DIR/.env olusturuldu - BOT_TOKEN ve GROUP_CHAT_ID'yi doldur, sonra:"
  echo "   sudo systemctl restart $SERVICE"
fi

chown -R "$SERVICE:$SERVICE" "$APP_DIR"
chmod 600 "$APP_DIR/.env"

echo "==> systemd"
cp "$APP_DIR/deploy/menubot.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"

sleep 2
systemctl --no-pager status "$SERVICE" || true

cat <<EOF

Bitti.
  Log     : journalctl -u $SERVICE -f
  Durdur  : sudo systemctl stop $SERVICE
  Yeniden : sudo systemctl restart $SERVICE
  Guncelle: (yerelden) rsync ile kopyala + sudo systemctl restart $SERVICE
EOF
