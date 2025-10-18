from typing import Protocol, List
from assistant_app.domain.models import Product

class Scraper(Protocol):
    store: str
    country: str
    async def search_async(self, query: str) -> List[Product]: ...
