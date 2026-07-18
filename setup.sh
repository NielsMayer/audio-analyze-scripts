#!/usr/bin/env bash
# setup.sh — Quick dependency check and install helper

set -euo pipefail

echo "Checking dependencies for audio-analyze..."

missing=()

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    missing+=("ffmpeg")
fi

# Check ffprobe
if ! command -v ffprobe &> /dev/null; then
    missing+=("ffprobe")
fi

# Check jq
if ! command -v jq &> /dev/null; then
    missing+=("jq")
fi

# Check python3
if ! command -v python3 &> /dev/null; then
    missing+=("python3")
fi

# Check numpy/scipy
if ! python3 -c "import numpy, scipy" 2>/dev/null; then
    missing+=("python3-numpy scipy")
fi

if [[ ${#missing[@]} -eq 0 ]]; then
    echo "All dependencies satisfied."
    exit 0
fi

echo "Missing dependencies: ${missing[*]}"
echo ""

# Detect OS and suggest install command
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS detected. Install with:"
    echo "  brew install ffmpeg jq python3"
    echo "  pip3 install numpy scipy"
elif [[ -f /etc/debian_version ]]; then
    echo "Debian/Ubuntu detected. Install with:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install ffmpeg jq python3 python3-pip"
    echo "  pip3 install numpy scipy"
elif [[ -f /etc/fedora-release ]] || [[ -f /etc/redhat-release ]]; then
    echo "Fedora/RHEL detected. Install with:"
    echo "  sudo dnf install ffmpeg jq python3 python3-pip"
    echo "  pip3 install numpy scipy"
else
    echo "Please install the missing dependencies manually."
fi

exit 1
