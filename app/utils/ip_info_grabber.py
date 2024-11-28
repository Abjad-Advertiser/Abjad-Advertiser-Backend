import requests


class IPInformation:
    ip: str
    country: str
    latitude: float
    longitude: float
    timezone: str
    is_eu: bool
    city: str


class IPInfoGrabber:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.api_urls = [
            "http://ip-api.com/json/#ip_address",
            "https://ipinfo.io/#ip_address/json/",
        ]

    def get_ip_info(self, ip_address: str) -> IPInformation:
        """
        Fetches IP geolocation information using multiple IP API services

        Args:
            ip_address: IPv4 or IPv6 address to look up

        Returns:
            IPInformation object containing geolocation data

        Raises:
            requests.RequestException: If all API requests fail
        """
        last_exception = None

        for base_url in self.api_urls:
            try:
                response = requests.get(
                    f"{base_url.replace('#ip_address', ip_address)}"
                )
                response.raise_for_status()
                data = response.json()

                # Handle different API response formats
                if base_url == "http://ip-api.com/json/#ip_address":
                    return IPInformation(
                        ip=ip_address,
                        country=data["countryCode"],
                        latitude=data["lat"],
                        longitude=data["lon"],
                        timezone=data["timezone"],
                        is_eu=data.get("inEU", False),
                        city=data["city"],
                    )
                elif base_url == "https://ipinfo.io/#ip_address/json/":
                    return IPInformation(
                        ip=ip_address,
                        country=data["country_code"],
                        latitude=float(data["latitude"]),
                        longitude=float(data["longitude"]),
                        timezone=data["timezone"],
                        is_eu=data["country_code"]
                        in [
                            "AT",
                            "BE",
                            "BG",
                            "HR",
                            "CY",
                            "CZ",
                            "DK",
                            "EE",
                            "FI",
                            "FR",
                            "DE",
                            "GR",
                            "HU",
                            "IE",
                            "IT",
                            "LV",
                            "LT",
                            "LU",
                            "MT",
                            "NL",
                            "PL",
                            "PT",
                            "RO",
                            "SK",
                            "SI",
                            "ES",
                            "SE",
                        ],
                        city=data["city"],
                    )
                else:  # ipinfo.io
                    loc = data["loc"].split(",")
                    return IPInformation(
                        ip=ip_address,
                        country=data["country"],
                        latitude=float(loc[0]),
                        longitude=float(loc[1]),
                        timezone=data["timezone"],
                        is_eu=data.get("is_eu", False),
                        city=data["city"],
                    )

            except Exception as e:
                last_exception = e
                continue

        # If all APIs fail, raise the last exception
        if last_exception:
            raise last_exception
