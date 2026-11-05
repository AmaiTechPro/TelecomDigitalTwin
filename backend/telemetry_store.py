from copy import deepcopy
from threading import Lock


# Latest telemetry indexed by device ID
_latest_telemetry = {}

# Protect shared state when MQTT and API threads access it
_cache_lock = Lock()


def update_telemetry(event: dict) -> bool:
    """
    Store the latest telemetry event for a device.
    """

    device_id = event.get("device_id")

    if not isinstance(device_id, str) or not device_id.strip():
        return False

    with _cache_lock:
        _latest_telemetry[device_id] = deepcopy(event)

    return True


def get_all_telemetry() -> dict:
    """
    Return the latest readings from all devices.
    """

    with _cache_lock:
        return deepcopy(_latest_telemetry)


def get_device_telemetry(device_id: str):
    """
    Return the latest reading for one device.
    """

    with _cache_lock:
        event = _latest_telemetry.get(device_id)

        return deepcopy(event) if event is not None else None


def get_device_count() -> int:
    """
    Return the number of devices currently represented in the cache.
    """

    with _cache_lock:
        return len(_latest_telemetry)