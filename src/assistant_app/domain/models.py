from dataclasses import dataclass

@dataclass
class Product:
    store: str
    country: str
    title: str
    price: float
    currency: str
    url: str
    specs: dict

    def to_dict(self) -> dict:
        return {
            "store": self.store,
            "country": self.country,
            "title": self.title,
            "price": self.price,
            "currency": self.currency,
            "url": self.url,
            "specs": self.specs or {},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Product":
        return cls(
            store=d["store"],
            country=d.get("country") or "",
            title=d["title"],
            price=float(d["price"]),
            currency=d.get("currency") or "EUR",
            url=d["url"],
            specs=d.get("specs") or {},
        )
