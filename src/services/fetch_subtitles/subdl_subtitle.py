import requests

from src.settings import settings

from .base_fetch import FetchSubtitle


class SUBDL(FetchSubtitle):
    def __init__(self):
        # Variables
        self.BASE_URL = "https://api.subdl.com/api/v2"
        self.headers = {"Authorization": f"Bearer {settings.SUBDL_KEY.get_secret_value()}"}

    def search(self, query: dict):
        print(self.headers)
        r = requests.get(
            f"{self.BASE_URL}/movies/search?q=dune&type=movie&limit=5",
            headers=self.headers,
        )
        print(r.json())
