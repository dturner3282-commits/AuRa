#!/data/data/com.termux/files/usr/bin/bash
# AuRA — Termux installer (no login required)
# Run: curl -sL https://raw.githubusercontent.com/dturner3282-commits/AuRa/main/scripts/install_termux.sh | bash

set -e

echo "=== AuRA — Termux Install ==="
echo "Installing dependencies..."

pkg update -y && pkg install -y python git

echo "Cloning AuRA..."
cd ~
if [ -d "AuRa" ]; then
    echo "AuRa directory exists, pulling latest..."
    cd AuRa && git pull
else
    git clone https://github.com/dturner3282-commits/AuRa.git
    cd AuRa
fi

echo "Installing Python packages..."
pip install torch pyyaml
pip install -e .

echo ""
echo "=== AuRA installed! ==="
echo "Commands:"
echo "  aura info              — Show system info"
echo "  aura detect <file>     — Find gaps/bugs"
echo "  aura fix <file>        — Fix broken code"
echo "  aura complete <file>   — Complete code"
echo "  aura translate <file> --to <lang>  — Translate code"
echo "  aura analyze <file>    — Full analysis"
echo "  aura train             — Train model"
echo ""
echo "Try: aura info"
