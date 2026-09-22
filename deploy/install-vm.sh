#!/usr/bin/env bash
# MenuBot'u Ubuntu/Debian bir VM'e GitHub'dan kurar.
#
# Ilk kurulum:
#   sudo apt update && sudo apt install -y git
#   sudo git clone https://github.com/hdhalilhd/LunchBot /opt/menubot
#   sudo bash /opt/menubot/deploy/install-vm.sh
#
# Tekrar calistirmak zararsiz: mevcut kurulumu gunceller, .env'e dokunmaz.

set -euo pipefail

APP_DIR=/opt/menubot
SERVICE=menubot
REPO_URL="${1:-}"

[ "$(id -u)" -eq 0 ] || { echo "Bu script root ile calismali: sudo bash $0"; exit 1; }

echo "==> Paketler"
apt-get update -qq
apt-get install -y -qq git python3 python3-venv python3-pip

echo "==> Saat dilimi"
timedatectl set-timezone Europe/Istanbul || true

echo "==> Kod"
if [ -d "$APP_DIR/.git" ]; then
  git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true
  git -C "$APP_DIR" pull --ff-only
else
  if [ -z "$REPO_URL" ]; then
    echo "Repo adresi lazim:  sudo bash $0 https://github.com/hdhalilhd/LunchBot"
    exit 1
  fi
  git clone "$REPO_URL" "$APP_DIR"
  git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true
fi

echo "==> Kullanici: $SERVICE"
id -u "$SERVICE" &>/dev/null || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE"

echo "==> Sanal ortam"
[ -d "$APP_DIR/.venv" ] || python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

YENI_ENV=0
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  YENI_ENV=1
fi

chown -R "$SERVICE:$SERVICE" "$APP_DIR"
chmod 600 "$APP_DIR/.env"

echo "==> systemd"
cp "$APP_DIR/deploy/menubot.service" /etc/systemd/system/
cp "$APP_DIR/deploy/menubot-update.service" /etc/systemd/system/
cp "$APP_DIR/deploy/menubot-update.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE" -q

if [ "$YENI_ENV" -eq 1 ]; then
  cat <<EOF

================================================================
  $APP_DIR/.env olusturuldu ama BOS.
  Doldur:   sudo nano $APP_DIR/.env
  Sonra  :  sudo systemctl start $SERVICE
================================================================
EOF
  exit 0
fi

systemctl restart "$SERVICE"
sleep 2
systemctl --no-pager --lines=15 status "$SERVICE" || true

cat <<EOF

Bitti.
  Log         : journalctl -u $SERVICE -f
  Yeniden bas : sudo systemctl restart $SERVICE
  Guncelle    : sudo /opt/menubot/deploy/update.sh
  Oto-guncelle: sudo systemctl enable --now menubot-update.timer
EOF
