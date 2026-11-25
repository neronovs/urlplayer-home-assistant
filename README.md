# UrlPlayer Home Assistant Integration

## Installation

### Option 1: HACS 1-click badge + manual HACS instructions
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=neronovs&repository=urlplayer-home-assistant&category=integration)

Or manually add the repository in HACS / Marketplace:
1. In Home Assistant, open **HACS** (or **Marketplace**) → top-right menu (`⋮`) → **Custom repositories** (or **Add from link**)
2. Paste `https://github.com/neronovs/urlplayer-home-assistant` and choose category **Integration**
3. Open **UrlPlayer** and click **Install** (or **Download**)
4. Restart Home Assistant if prompted

### Option 2: One-liner Terminal Install with curl
```bash
curl -fsSL https://raw.githubusercontent.com/neronovs/urlplayer-home-assistant/main/install.sh | sh
```
Then restart Home Assistant.

## Setup Guide

### 1. Enable the Server in UrlPlayer
- Go to UrlPlayer Settings → Home Assistant
- Enable the Local HTTP server
- Copy the URL and token displayed

### 2. Add the Integration

#### Automatic discovery (Zeroconf _urlplayer._tcp)
In Settings → Devices & services, click Add on the discovered UrlPlayer card and paste your Bearer token.

#### Manual setup
Click Add integration → search for UrlPlayer → paste your URL (or Host IP) and Bearer token (port 8765 is pre-filled and auto-extracted if you paste the full http://host:port URL).

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
entity: media_player.urlplayer_192_168_2_175
```

> Note: Home Assistant names the entity after your phone's IP (e.g. `media_player.urlplayer_192_168_2_175`, or `media_player.urlplayer` if renamed during setup).

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
          entity_id: media_player.urlplayer_192_168_2_175
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
          entity_id: media_player.urlplayer_192_168_2_175
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
          entity_id: media_player.urlplayer_192_168_2_175
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
          entity_id: media_player.urlplayer_192_168_2_175
        data:
          volume_level: 0.65
```

## Security Notes

- Traffic stays strictly on your local Wi-Fi network (LAN-only HTTP)
- Every endpoint (except /api/v1/health) requires constant-time Bearer token authentication
- Playback is restricted to stations and cached AI Music tracks already in your UrlPlayer library (arbitrary LAN URLs are rejected)
