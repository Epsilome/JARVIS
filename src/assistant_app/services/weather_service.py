"""
Weather Service - OpenWeatherMap API
"""
import httpx
import logging

logger = logging.getLogger(__name__)

# OpenWeatherMap API
OPENWEATHER_API_KEY = "6ab420a304ecbf99d3fdf33bb9ee93cc"
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Weather icon mapping (OpenWeather icon codes to emoji)
ICON_MAP = {
    "01d": "☀️", "01n": "🌙",  # Clear
    "02d": "⛅", "02n": "☁️",  # Few clouds
    "03d": "☁️", "03n": "☁️",  # Scattered clouds
    "04d": "☁️", "04n": "☁️",  # Broken clouds
    "09d": "🌧️", "09n": "🌧️",  # Shower rain
    "10d": "🌦️", "10n": "🌧️",  # Rain
    "11d": "⛈️", "11n": "⛈️",  # Thunderstorm
    "13d": "🌨️", "13n": "🌨️",  # Snow
    "50d": "🌫️", "50n": "🌫️",  # Mist
}

async def get_weather(city: str = "Casablanca", country: str = "MA") -> dict:
    """
    Fetch current weather from OpenWeatherMap.
    Returns dict with: temp, humidity, wind, icon, description
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                OPENWEATHER_BASE_URL,
                params={
                    "q": f"{city},{country}",
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            icon_code = data["weather"][0]["icon"]
            return {
                "temp": round(data["main"]["temp"]),
                "humidity": data["main"]["humidity"],
                "wind": round(data["wind"]["speed"] * 3.6),  # m/s to km/h
                "icon": ICON_MAP.get(icon_code, "🌤️"),
                "description": data["weather"][0]["description"].title(),
                "city": data["name"],
            }
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return {
            "temp": 24,
            "humidity": 65,
            "wind": 12,
            "icon": "☀️",
            "description": "Clear",
            "city": city,
        }

def get_weather_sync(city: str = "Casablanca", country: str | None = None) -> dict:
    """
    Synchronous weather fetch using sync httpx.
    This avoids asyncio.run() conflicts when called from FastAPI.
    """
    import httpx
    
    # Build query string
    if country:
        query = f"{city},{country}"
    else:
        query = city
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                OPENWEATHER_BASE_URL,
                params={
                    "q": query,
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                },
            )
            response.raise_for_status()
            data = response.json()
            
            icon_code = data["weather"][0]["icon"]
            return {
                "temp": round(data["main"]["temp"]),
                "humidity": data["main"]["humidity"],
                "wind": round(data["wind"]["speed"] * 3.6),  # m/s to km/h
                "icon": ICON_MAP.get(icon_code, "🌤️"),
                "description": data["weather"][0]["description"].title(),
                "city": data["name"],
                "country": data["sys"]["country"],
            }
    except httpx.HTTPStatusError as e:
        logger.error(f"Weather API HTTP error: {e.response.status_code} - {e.response.text}")
        raise ValueError(f"Weather API error: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Weather API request error: {e}")
        raise ValueError(f"Weather API connection error: {e}")
    except Exception as e:
        logger.error(f"Weather API unexpected error: {e}")
        raise ValueError(f"Weather error: {e}")

