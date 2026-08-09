import json
from logging import getLogger
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.models.enums import DiscoverType
from src.settings import settings

from .base_fetch import FetchSubtitle

logger = getLogger(__name__)

# Setup retry strategy for connection resets
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)

session.mount("https://", adapter)
session.mount("http://", adapter)


class OPENSUBTITLE(FetchSubtitle):
    def __init__(self):

        self.headers = {
            "Accept": "application/json",
            "Api-Key": settings.OPENSUBTITLE_KEY,
            "User-Agent": f"{settings.APP_NAME} v0.1.0",
            "Content-Type": "application/json",
        }
        self.BASE_URL = "https://api.opensubtitles.com/api/v1"

        self.TOKEN_FILE = Path("secrets.txt")

        self.ACCESS_TOKEN: str | None

    def load_access_key(self):
        """
        Load access token from file
        """
        global ACCESS_TOKEN
        if ACCESS_TOKEN:
            return ACCESS_TOKEN
        if self.TOKEN_FILE.exists():
            logger.debug("Loading access token")
            ACCESS_TOKEN = self.TOKEN_FILE.read_text()
            return ACCESS_TOKEN

    def login(self):
        body = {
            "username": settings.OPENSUBTITLE_USERNAME,
            "password": settings.OPENSUBTITLE_PASSWORD,
        }
        res = requests.post(
            f"{self.BASE_URL}/login",
            headers=self.headers,
            json=body,
        )
        if res.status_code == 200:
            data = res.json()
            access_token = data["token"]
            self.headers["Authorization"] = f"Bearer {access_token}"
            self.TOKEN_FILE.write_text(access_token)
            logger.info("Opensubtitle login successfull")
            return True
        else:
            logger.debug(
                f"Opensubtitle login failed, status code: {res.status_code}, Response: {res.json()}"
            )
            return False

    def discover(self, discover_type: DiscoverType = DiscoverType.MOST_DOWNLOADED):
        result = session.get(
            f"{self.BASE_URL}/discover/{discover_type.value}",
            headers=self.headers,
        )

        if result.status_code == 200:
            data = result.json()
            print(json.dumps(data, indent=2))
            logger.info(f"Discover data fetched with flag: {discover_type.value}")
            return data
        else:
            logger.debug(
                f"Discover data fetch failed with status code: {result.status_code}"
            )
            raise Exception("Discover")  # noqa: TRY002

    def search(self, query: dict):
        result = session.get(
            f"{self.BASE_URL}/features",
            params=query,
            headers=self.headers,
        )

        if result.ok:
            data = result.json()
            logger.info(f"Search data fetched with flag: {query}")
            return data
        else:
            logger.debug(
                f"Opensubtitle search failed with status code : {result.status_code}, data : {result.json()}"
            )
            raise Exception("Internal search call failed")  # noqa: TRY002

    def download(self):
        self.headers["Authorization"] = f"Bearer {self.load_access_key()}"
        res = session.post(
            f"{self.BASE_URL}/download",
            headers=self.headers,
            json={"file_id": 6633446},
            timeout=10,
        )

        if res.status_code == 200:
            data = res.json()
            print(data)
            conn = session.get(data["link"], timeout=10)
            if conn != 200:
                return
            file = Path(conn["filename"])
            file.write_bytes(conn.content)
