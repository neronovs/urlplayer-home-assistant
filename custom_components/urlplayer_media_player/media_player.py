"""Media player platform for UrlPlayer."""
from typing import Any, Dict, List, Optional
import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerState,
    MediaType,
    BrowseMedia,
    SUPPORT_PLAY,
    SUPPORT_STOP,
    SUPPORT_PAUSE,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
    SUPPORT_BROWSE_MEDIA,
)
from homeassistant.components.media_player.entity import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_TOKEN
from .client import UrlPlayerClient

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = (
    SUPPORT_PLAY
    | SUPPORT_STOP
    | SUPPORT_PAUSE
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_STEP
    | SUPPORT_BROWSE_MEDIA
)


async def async_setup_entry(
    hass: HomeAssistant, entry: dict, async_add_entities
) -> None:
    """Set up the UrlPlayer media player platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    client = UrlPlayerClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_TOKEN]
    )
    async_add_entities([UrlPlayerMediaPlayer(coordinator, client, entry)])


class UrlPlayerMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a UrlPlayer media player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_media_content_type = MediaType.MUSIC

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: UrlPlayerClient,
        entry: dict,
    ) -> None:
        """Initialize the media player."""
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._attr_supported_features = SUPPORTED_FEATURES

    @property
    def state(self) -> MediaPlayerState:
        """Return the current state of the media player."""
        status = self.coordinator.data.get("status", {})
        if status.get("state") == "playing":
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def media_title(self) -> Optional[str]:
        """Return the title of current playing media."""
        status = self.coordinator.data.get("status", {})
        return status.get("song") or status.get("station")

    @property
    def media_artist(self) -> Optional[str]:
        """Return the artist of current playing media, or None if not available."""
        status = self.coordinator.data.get("status", {})
        if status.get("song"):
            return None
        return status.get("station")

    @property
    def source(self) -> Optional[str]:
        """Return the current source (station)."""
        status = self.coordinator.data.get("status", {})
        return status.get("station")

    @property
    def source_list(self) -> List[str]:
        """Return the list of available sources."""
        stations = self.coordinator.data.get("stations", [])
        return [s["title"] for s in stations]

    @property
    def volume_level(self) -> Optional[float]:
        """Return the volume level."""
        status = self.coordinator.data.get("status", {})
        return status.get("volume")

    @property
    def media_image_hash(self) -> Optional[str]:
        """Return the hash of the artwork."""
        status = self.coordinator.data.get("status", {})
        if status.get("has_artwork"):
            return status.get("artwork_hash")
        return None

    async def async_get_media_image(self) -> tuple[bytes | None, str | None]:
        """Fetch media image from UrlPlayer server."""
        try:
            artwork = await self.hass.async_add_executor_job(self._client.artwork)
            if artwork is not None:
                return artwork
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error fetching artwork")
        return (None, None)

    async def async_media_play(self) -> None:
        """Start playing."""
        await self.hass.async_add_executor_job(self._client.toggle)
        await self.coordinator.async_refresh()

    async def async_media_stop(self) -> None:
        """Stop playing."""
        await self.hass.async_add_executor_job(self._client.stop)
        await self.coordinator.async_refresh()

    async def async_media_pause(self) -> None:
        """Pause playing."""
        await self.hass.async_add_executor_job(self._client.stop)
        await self.coordinator.async_refresh()

    async def async_media_next_track(self) -> None:
        """Skip to next track."""
        await self.hass.async_add_executor_job(self._client.next_track)
        await self.coordinator.async_refresh()

    async def async_media_previous_track(self) -> None:
        """Skip to previous track."""
        await self.hass.async_add_executor_job(self._client.previous_track)
        await self.coordinator.async_refresh()

    async def async_select_source(self, source: str) -> None:
        """Select a source."""
        stations = self.coordinator.data.get("stations", [])
        station_url = next((s["url"] for s in stations if s["title"] == source), None)
        if station_url:
            await self.hass.async_add_executor_job(self._client.play, url=station_url)
        else:
            await self.hass.async_add_executor_job(self._client.play, source=source)
        await self.coordinator.async_refresh()

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        if media_id.startswith("drive:"):
            await self.hass.async_add_executor_job(self._client.play, media_id=media_id)
        elif media_id.startswith("http://") or media_id.startswith("https://"):
            await self.hass.async_add_executor_job(self._client.play, url=media_id)
        else:
            await self.hass.async_add_executor_job(self._client.play, source=media_id)
        await self.coordinator.async_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        await self.hass.async_add_executor_job(self._client.set_volume, volume)
        await self.coordinator.async_refresh()

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the browser media for UrlPlayer."""
        # This is a simplified implementation - in a real implementation,
        # you would build a proper BrowseMedia tree with Favourites, All Stations, etc.
        return BrowseMedia(
            title="UrlPlayer",
            media_class="directory",
            media_content_id="",
            media_content_type="library",
            can_play=False,
            can_expand=True,
            children=[
                BrowseMedia(
                    title="Favourites",
                    media_class="directory",
                    media_content_id="favourites",
                    media_content_type="favorites",
                    can_play=False,
                    can_expand=True,
                ),
                BrowseMedia(
                    title="All Stations",
                    media_class="directory",
                    media_content_id="stations",
                    media_content_type="station",
                    can_play=False,
                    can_expand=True,
                ),
                BrowseMedia(
                    title="AI Music",
                    media_class="directory",
                    media_content_id="ai_music",
                    media_content_type="ai_music",
                    can_play=False,
                    can_expand=True,
                ),
            ],
        )
