import requests


class IPInformation:
    def __init__(
        self,
        ip: str,
        country: str,
        latitude: float,
        longitude: float,
        timezone: str,
        is_eu: bool,
        city: str,
    ):
        self.ip = ip
        self.country = country
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.is_eu = is_eu
        self.city = city


class IPInfoGrabber:
    API_URLS = [
        "http://ip-api.com/json/#ip_address",
        "https://ipinfo.io/#ip_address/json/",
    ]

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def _get_api_response(self, ip_address: str) -> dict:
        last_exception = None
        for url in self.API_URLS:
            try:
                response = requests.get(f"{url.replace('#ip_address', ip_address)}")
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                last_exception = e
                continue
        if last_exception:
            raise last_exception

    def get_ip_info(self, ip_address: str, debug: bool = False) -> IPInformation:
        if debug and ip_address in ["127.0.0.1", "::1"]:
            return IPInformation(
                ip=ip_address,
                country="Unknown",
                latitude=0.0,
                longitude=0.0,
                timezone="Unknown",
                is_eu=False,
                city="Unknown",
            )

        if not any(
            [
                ":" in ip_address,
                all(
                    part.isdigit() and 0 <= int(part) <= 255
                    for part in ip_address.split(".")
                ),
            ]
        ):
            raise requests.RequestException(f"Invalid IP address format: {ip_address}")

        data = self._get_api_response(ip_address)

        if data.get("countryCode"):
            return IPInformation(
                ip=ip_address,
                country=data["countryCode"],
                latitude=data["lat"],
                longitude=data["lon"],
                timezone=data["timezone"],
                is_eu=data.get("inEU", False),
                city=data["city"],
            )
        elif data.get("country_code"):
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
        else:
            try:
                loc = data.get("loc", "0,0").split(",")
                return IPInformation(
                    ip=ip_address,
                    country=data.get("country", "Unknown"),
                    latitude=float(loc[0]),
                    longitude=float(loc[1]),
                    timezone=data.get("timezone", "UTC"),
                    is_eu=data.get("is_eu", False),
                    city=data.get("city", "Unknown"),
                )
            except (KeyError, ValueError, IndexError) as e:
                raise ValueError(
                    f"Failed to parse ipinfo.io response: {
                        str(e)}"
                )
