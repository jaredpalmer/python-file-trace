"""IP Geolocation for checkout."""


class IPGeolocationClient:
    """Client for IP geolocation services."""

    def close(self):
        pass


def get_client():
    """Get the IP geolocation client."""
    return IPGeolocationClient()
