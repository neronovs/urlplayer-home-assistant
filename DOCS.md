# UrlPlayer Home Assistant Integration

## Setup Guide

### 1. Enable the Server in UrlPlayer
- Go to UrlPlayer Settings → Home Assistant
- Enable the Local HTTP server
- Copy the URL and token displayed

### 2. Install the Custom Component
- **Option 1 (HACS / Marketplace)**: Open the repository via the [1-click HACS link](https://my.home-assistant.io/redirect/hacs_repository/?owner=neronovs&repository=urlplayer-home-assistant&category=integration) (or add `https://github.com/neronovs/urlplayer-home-assistant` as a Custom repository with category **Integration**), click **Install** (or **Download**), and restart Home Assistant if prompted.
- **Option 2 (Terminal one-liner)**: Run `curl -fsSL https://raw.githubusercontent.com/neronovs/urlplayer-home-assistant/main/install.sh | sh` in your Home Assistant Terminal, then restart Home Assistant.
- **Option 3 (Manual copy)**: Copy `custom_components/urlplayer_media_player` to `/config/custom_components/urlplayer_media_player` and restart Home Assistant.

### 3. Add the Integration

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
