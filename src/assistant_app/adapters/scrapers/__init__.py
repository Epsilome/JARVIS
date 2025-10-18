from . import cdiscount_fr
from importlib import import_module

_MODULES = [
    "cdiscount_fr",
    # "fnac_fr",
    # "darty_fr",
]
ALL = {
    "cdiscount": cdiscount_fr,
    # "fnac": fnac_fr,
    # "darty": darty_fr,
}

def _load_module(modname: str):
    """
    Import the module and return (store_name, scraper_obj).
    scraper_obj is either the module's `scraper` attribute if present,
    else the module itself.
    """
    m = import_module(f"{__name__}.{modname}")
    obj = getattr(m, "scraper", m) 
    name = (
        getattr(obj, "name", None)
        or getattr(obj, "STORE", None)
        or modname.replace("_fr", "").capitalize() 
    )
    return name, obj

SCRAPERS = {}
ALL = []

for mod in _MODULES:
    try:
        name, obj = _load_module(mod)
        SCRAPERS[name] = obj
        ALL.append(obj)
    except Exception as e:
        pass

__all__ = ["SCRAPERS", "ALL"]
