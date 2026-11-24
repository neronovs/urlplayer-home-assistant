"""Media player platform for UrlPlayer."""
from functools import partial
from typing import Any, Dict, List, Optional

from homeassistant.components.media_player import BrowseMedia, MediaClass, MediaPlayerEntity, MediaPlayerEntityFeature, MediaPlayerState, MediaType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_TOKEN, PLATFORMS
from .client import UrlPlayerClient

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.BROWSE_MEDIA
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the UrlPlayer media player platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([UrlPlayerMediaPlayer(data["coordinator"], data["client"], entry)])


class UrlPlayerMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a UrlPlayer media player."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        client: UrlPlayerClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the media player."""
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.title
        self._attr_has_entity_name = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="UrlPlayer",
            model="Android"
        )
        self._attr_supported_features = SUPPORTED_FEATURES

    @property
    def _status(self) -> Dict[str, Any]:
        """Return the status from coordinator data."""
        return (self.coordinator.data or {}).get("status") or {}

    @property
    def _catalog(self) -> Dict[str, Any]:
        """Return the catalog from coordinator data."""
        return (self.coordinator.data or {}).get("catalog") or {}

    @property
    def _stations(self) -> List[Dict[str, Any]]:
        """Return the stations from coordinator data."""
        return self._catalog.get("stations") or []

    @property
    def _tracks(self) -> List[Dict[str, Any]]:
        """Return the tracks from coordinator data."""
        return self._catalog.get("tracks") or []

    @property
    def state(self) -> MediaPlayerState:
        """Return the current state of the media player."""
        status = self._status
        if status.get("state") == "playing":
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def media_title(self) -> Optional[str]:
        """Return the title of current playing media."""
        status = self._status
        return status.get("song") or status.get("station")

    @property
    def media_artist(self) -> Optional[str]:
        """Return the artist of current playing media, or None if not available."""
        status = self._status
        if status.get("song"):
            return None
        return status.get("station")

    @property
    def source(self) -> Optional[str]:
        """Return the current source (station)."""
        status = self._status
        return status.get("station")

    @property
    def source_list(self) -> List[str]:
        """Return the list of available sources."""
        return [s["title"] for s in self._stations if "title" in s]

    @property
    def volume_level(self) -> Optional[float]:
        """Return the volume level."""
        status = self._status
        return status.get("volume")

    @property
    def media_image_hash(self) -> Optional[str]:
        """Return the hash of the artwork."""
        status = self._status
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
            pass
        return (None, None)

    async def async_media_play(self) -> None:
        """Start playing."""
        await self.hass.async_add_executor_job(self._client.play)
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        """Stop playing."""
        await self.hass.async_add_executor_job(self._client.stop)
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        """Pause playing."""
        await self.hass.async_add_executor_job(self._client.stop)
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        """Skip to next track."""
        await self.hass.async_add_executor_job(self._client.next_track)
        await self.coordinator.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        """Skip to previous track."""
        await self.hass.async_add_executor_job(self._client.previous_track)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        """Select a source."""
        stations = self._stations
        station_url = next((s["url"] for s in stations if s["title"] == source), None)
        if station_url:
            await self.hass.async_add_executor_job(partial(self._client.play, url=station_url))
        else:
            await self.hass.async_add_executor_job(partial(self._client.play, source=source))
        await self.coordinator.async_request_refresh()

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        if media_id.startswith("drive:"):
            await self.hass.async_add_executor_job(partial(self._client.play, media_id=media_id))
        elif media_id.startswith("http://") or media_id.startswith("https://"):
            await self.hass.async_add_executor_job(partial(self._client.play, url=media_id))
        else:
            await self.hass.async_add_executor_job(partial(self._client.play, source=media_id))
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        await self.hass.async_add_executor_job(self._client.set_volume, volume)
        await self.coordinator.async_request_refresh()

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the browser media for UrlPlayer."""
        # Build a proper BrowseMedia tree based on content ID
        if media_content_id == "favourites":
            # Return favorites (if available)
            return BrowseMedia(
                title="Favourites",
                media_class=MediaClass.DIRECTORY,
                media_content_id="favourites",
                media_content_type="favorites",
                can_play=False,
                can_expand=True,
                children=[],
            )
        elif media_content_id == "stations":
            # Return all stations
            children = []
            for station in self._stations:
                if "title" in station and "url" in station:
                    children.append(
                        BrowseMedia(
                            title=station["title"],
                            media_class=MediaClass.CHANNEL,
                            media_content_id=station["url"],
                            media_content_type="music",
                            can_play=True,
                            can_expand=False,
                        )
                    )
            return BrowseMedia(
                title="All Stations",
                media_class=MediaClass.DIRECTORY,
                media_content_id="stations",
                media_content_type="station",
                can_play=False,
                can_expand=True,
                children=children,
            )
        elif media_content_id == "ai_music":
            # Return AI music (if available)
            return BrowseMedia(
                title="AI Music",
                media_class=MediaClass.DIRECTORY,
                media_content_id="ai_music",
                media_content_type="ai_music",
                can_play=False,
                can_expand=True,
                children=[],
            )
        else:
            # Root level - show main categories
            return BrowseMedia(
                title="UrlPlayer",
                media_class=MediaClass.DIRECTORY,
                media_content_id="",
                media_content_type="library",
                can_play=False,
                can_expand=True,
                children=[
                    BrowseMedia(
                        title="Favourites",
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="favourites",
                        media_content_type="favorites",
                        can_play=False,
                        can_expand=True,
                    ),
                    BrowseMedia(
                        title="All Stations",
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="stations",
                        media_content_type="station",
                        can_play=False,
                        can_expand=True,
                    ),
                    BrowseMedia(
                        title="AI Music",
                        media_class=MediaClass.DIRECTORY,
                        media_content_id="ai_music",
                        media_content_type="ai_music",
                        can_play=False,
                        can_expand=True,
                    ),
                ],
            )
