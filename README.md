# UrlPlayer Home Assistant Integration

## Installation

### Option 1: HACS (Recommended)
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=neronovs&repository=urlplayer-home-assistant&category=integration)

Or manually add the repository:
1. In Home Assistant, go to Settings → Devices & Services → Integrations
2. Click the "+" button in the bottom right
3. Search for "UrlPlayer" or add the custom repository URL: `https://github.com/neronovs/urlplayer-home-assistant`

### Option 2: One-liner Terminal Install
```bash
curl -fsSL https://raw.githubusercontent.com/neronovs/urlplayer-home-assistant/main/install.sh | sh
```

## Setup Guide

### 1. Enable the Server in UrlPlayer
- Go to UrlPlayer Settings → Home Assistant
- Enable the Local HTTP server
- Copy the URL and token displayed

### 2. Add the Integration
The integration can be added automatically via Zeroconf discovery (`_urlplayer._tcp`) or manually by providing:
- Host/IP address
- Port number
- Bearer token

## Features Supported

- Play, stop, pause controls
- Next/previous track navigation
- Station source picker
- Media Browser support (Favourites, All Stations, AI Music tracks)
- Volume control
- Cover art proxy

## Dashboard Card Example

```yaml
type: media-control
entity: media_player.urlplayer
```

## Automation Examples

### Select Source
```yaml
automation:
  - alias: "Select Radio Station"
    trigger:
      - platform: state
        entity_id: input_select.radio_station
    action:
      - service: media_player.select_source
        target:
          entity_id: media_player.urlplayer
        data:
          source: "{{ trigger.to_state.state }}"
```

### Play Media
```yaml
automation:
  - alias: "Play Radio Station"
    trigger:
      - platform: state
        entity_id: input_select.radio_station
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.urlplayer
        data:
          media_content_id: "https://example.com/stream.mp3"
          media_content_type: "music"
```

### Play Station by ID
```yaml
automation:
  - alias: "Play Station by ID"
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.urlplayer
        data:
          media_content_id: "drive:12345"
          media_content_type: "music"
```

### Set Volume
```yaml
automation:
  - alias: "Set Volume"
    action:
      - service: media_player.volume_set
        target:
          entity_id: media_player.urlplayer
        data:
          volume_level: 0.65
```

## Security Notes

- This integration is designed for LAN-only use
- Authentication uses Bearer token (HTTP header)
- Station and track allow-lists are supported (opt-in)
- All communication is encrypted over HTTPS when enabled
