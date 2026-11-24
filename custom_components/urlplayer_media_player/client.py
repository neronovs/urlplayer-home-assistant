import urllib.request
import urllib.error
import json
from typing import Dict, Tuple, Optional

class UrlPlayerAuthError(Exception):
    """Custom exception for authentication errors."""
    pass


class UrlPlayerConnectionError(Exception):
    """Custom exception for connection errors."""
    pass


class UrlPlayerClient:
    """Clean Python HTTP client class for UrlPlayer."""

    def __init__(self, host: str, port: int, token: str, timeout: float = 5.0):
        """Initialize the UrlPlayer client."""
        self.host = host
        self.port = port
        self.token = token
        self.timeout = timeout

    @property
    def base_url(self) -> str:
        """Get the base URL for API calls."""
        return f"http://{self.host}:{self.port}"

    def artwork_url(self, artwork_hash: Optional[str] = None) -> str:
        """Get the artwork URL with optional version parameter."""
        url = f"{self.base_url}/api/v1/artwork"
        if artwork_hash:
            url += f"?v={artwork_hash}"
        return url

    def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make an HTTP request with proper error handling."""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            if data:
                req_data = json.dumps(data).encode('utf-8')
                request = urllib.request.Request(url, data=req_data, headers=headers, method=method)
            else:
                request = urllib.request.Request(url, headers=headers, method=method)
            
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise UrlPlayerAuthError(f"Authentication failed: {e}")
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise UrlPlayerConnectionError(f"Connection error: {e}")

    def health(self) -> Dict:
        """Get the health status of the UrlPlayer server."""
        url = f"{self.base_url}/api/v1/health"
        return self._make_request(url, method="GET")

    def status(self) -> Dict:
        """Get the current status of the UrlPlayer player."""
        url = f"{self.base_url}/api/v1/status"
        return self._make_request(url, method="GET")

    def stations(self) -> Dict:
        """Get the list of stations and tracks."""
        url = f"{self.base_url}/api/v1/stations"
        return self._make_request(url, method="GET")

    def artwork(self) -> Optional[Tuple[bytes, str]]:
        """Get the artwork for the current track."""
        url = f"{self.base_url}/api/v1/artwork"
        try:
            request = urllib.request.Request(url)
            request.add_header("Authorization", f"Bearer {self.token}")
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                content_type = response.getheader('Content-Type', '')
                return (response.read(), content_type)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise UrlPlayerConnectionError(f"Connection error: {e}")

    def toggle(self) -> Dict:
        """Toggle play/pause."""
        url = f"{self.base_url}/api/v1/toggle"
        return self._make_request(url, method="POST")

    def stop(self) -> Dict:
        """Stop playback."""
        url = f"{self.base_url}/api/v1/stop"
        return self._make_request(url, method="POST")

    def next_track(self) -> Dict:
        """Skip to the next track."""
        url = f"{self.base_url}/api/v1/next"
        return self._make_request(url, method="POST")

    def previous_track(self) -> Dict:
        """Go to the previous track."""
        url = f"{self.base_url}/api/v1/previous"
        return self._make_request(url, method="POST")

    def play(self, url: Optional[str] = None, media_id: Optional[str] = None, source: Optional[str] = None) -> Dict:
        """Start playing a track."""
        payload = {}
        if url is not None:
            payload["url"] = url
        if media_id is not None:
            payload["media_id"] = media_id
        if source is not None:
            payload["source"] = source
            
        url = f"{self.base_url}/api/v1/play"
        return self._make_request(url, method="POST", data=payload)

    def set_volume(self, level: float) -> Dict:
        """Set the volume level."""
        url = f"{self.base_url}/api/v1/volume"
        payload = {"level": round(max(0.0, min(1.0, level)), 3)}
        return self._make_request(url, method="POST", data=payload)
