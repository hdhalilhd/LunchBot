#!/usr/bin/env bash
# Kodu GitHub'dan ceker, gerekiyorsa bagimliliklari kurar, botu yeniden baslatir.
#
#   sudo /opt/menubot/deploy/update.sh
#
# Degisiklik yoksa hicbir sey yapmaz (botu bosuna yeniden baslatmaz).
# .env'e dokunmaz - o dosya git'te degil, VM'de kalir.

set -euo pipefail

APP_DIR=/opt/menubot
SERVICE=menubot

[ "$(id -u)" -eq 0 ] || { echo "root ile calistir: sudo $0"; exit 1; }

git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true

onceki=$(git -C "$APP_DIR" rev-parse HEAD)
git -C "$APP_DIR" fetch -q origin
dal=$(git -C "$APP_DIR" rev-parse --abbrev-ref HEAD)
sonraki=$(git -C "$APP_DIR" rev-parse "origin/$dal")

if [ "$onceki" = "$sonraki" ]; then
  echo "Degisiklik yok ($(echo "$onceki" | cut -c1-7)). Bot'a dokunulmadi."
  exit 0
fi

echo "Guncelleniyor: $(echo "$onceki" | cut -c1-7) -> $(echo "$sonraki" | cut -c1-7)"
git -C "$APP_DIR" merge --ff-only "origin/$dal"

# requirements degistiyse kur
if git -C "$APP_DIR" diff --name-only "$onceki" "$sonraki" | grep -q '^requirements.txt$'; then
  echo "requirements.txt degismis, bagimliliklar kuruluyor..."
  "$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
fi

# systemd dosyalari degistiyse yeniden yukle
if git -C "$APP_DIR" diff --name-only "$onceki" "$sonraki" | grep -q '^deploy/.*\.\(service\|timer\)$'; then
  echo "systemd dosyalari degismis, kopyalaniyor..."
  cp "$APP_DIR"/deploy/menubot*.service "$APP_DIR"/deploy/menubot*.timer /etc/systemd/system/
  systemctl daemon-reload
fi

chown -R menubot:menubot "$APP_DIR"
systemctl restart "$SERVICE"
sleep 2

if systemctl is-active --quiet "$SERVICE"; then
  echo "✔ Bot yeniden basladi."
else
  echo "✖ Bot baslamadi! Son loglar:"
  journalctl -u "$SERVICE" --no-pager --lines=30
  exit 1
fi
