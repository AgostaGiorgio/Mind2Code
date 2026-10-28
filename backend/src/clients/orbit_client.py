import threading
import logging
import requests

logger = logging.getLogger(__name__)


class OrbitClient:
    """Best-effort heartbeat to the Orbit registry.

    Shared, identical across all Orbit-family projects. Do not customize per
    service: identity comes from the constructor arguments (name, version,
    description, app_url, icon), not from edits to this file.

    Sends the first registration immediately, then every `ping_interval_seconds`
    on a daemon thread. Network failures are logged as warnings and never raised.
    """

    def __init__(
        self,
        orbit_api_url: str,
        name: str,
        version: str,
        description: str,
        app_url: str,
        icon: str = None,
        ping_interval_seconds: int = 3600,
    ):
        self.orbit_register_url = orbit_api_url

        self.payload = {
            "name": name,
            "version": version,
            "description": description,
            "icon": icon,
            "url": app_url,
        }

        self.ping_interval = ping_interval_seconds
        self._stop_event = threading.Event()
        self._thread = None

    def _send_registration(self):
        try:
            response = requests.post(
                self.orbit_register_url, json=self.payload, timeout=10, verify=False
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.warning(f"[Orbit Client] Error: {e}")

    def _loop(self):
        while not self._stop_event.is_set():
            self._send_registration()
            self._stop_event.wait(self.ping_interval)

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join()
