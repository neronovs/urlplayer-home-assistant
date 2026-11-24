#!/bin/sh
set -eu

# Auto-detect HA config dir
if [ -n "${1:-}" ]; then
    CONFIG_DIR="$1"
elif [ -d "/config" ]; then
    CONFIG_DIR="/config"
elif [ -d "/homeassistant" ]; then
    CONFIG_DIR="/homeassistant"
else
    echo "Error: Could not detect Home Assistant configuration directory." >&2
    echo "Please specify the path to your HA config directory as an argument." >&2
    exit 1
fi

echo "Detected Home Assistant config directory: $CONFIG_DIR"

# Create temporary directory for download
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Downloading UrlPlayer integration..."
curl -fsSL https://github.com/neronovs/urlplayer-home-assistant/archive/refs/heads/main.tar.gz | tar -xz -C "$TMPDIR"

# Extract the custom_components directory
echo "Installing UrlPlayer integration..."
mkdir -p "$CONFIG_DIR/custom_components"
rm -rf "$CONFIG_DIR/custom_components/urlplayer_media_player"
cp -r "$TMPDIR/urlplayer-home-assistant-main/custom_components/urlplayer_media_player" "$CONFIG_DIR/custom_components/"

echo "Installation complete!"
echo "Please restart Home Assistant and add UrlPlayer in Settings -> Devices & services."
