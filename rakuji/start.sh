#!/bin/bash

echo ""
echo " ================================================"
echo "  ||   Rakuji Security Bot baslatiliyor...    ||"
echo " ================================================"
echo ""

# Script'in bulunduğu klasöre geç
cd "$(dirname "$0")"

# .env dosyası var mı kontrol et
if [ ! -f ".env" ]; then
    echo " [HATA] .env dosyasi bulunamadi!"
    echo " .env.example dosyasini kopyalayip duzenlemeyi unutma."
    echo ""
    exit 1
fi

# Python3 var mı kontrol et
if ! command -v python3 &> /dev/null; then
    echo " [HATA] Python3 bulunamadi! Kurmak icin:"
    echo " sudo apt install python3 python3-pip"
    exit 1
fi

# Botu başlat
python3 bot.py

echo ""
echo " Bot durdu."
