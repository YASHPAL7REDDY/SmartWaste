"""
Real-world Weather Service for SmartWaste ML Pipeline
======================================================

Provides weather features (temp_max_c, rainfall_mm, humidity_pct) using OpenWeatherMap API.
Implements caching, fallback strategies, and area-to-coordinate mapping.

No model retraining required. Pure feature pipeline enhancement.
"""

import os
import json
import time
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import threading

import requests

logger = logging.getLogger(__name__)


@dataclass
class WeatherFeatures:
    """ML-ready weather features matching the preprocessing pipeline."""
    temp_max_c: Optional[float]
    rainfall_mm: Optional[float]
    humidity_pct: Optional[float]
    source: str  # 'api_current', 'api_forecast', 'api_historical', 'cache', 'historical_avg', 'fallback'
    fetched_at: str
    area: str
    target_date: str
    is_missing: bool = False


@dataclass
class AreaCoordinates:
    """Latitude/longitude for a SmartWaste area."""
    area: str
    latitude: float
    longitude: float


# Area → Coordinate mapping for all 18 SmartWaste areas (Bangalore)
AREA_COORDINATES: Dict[str, AreaCoordinates] = {
    "Anekal": AreaCoordinates("Anekal", 12.7667, 77.7000),
    "BTM Layout": AreaCoordinates("BTM Layout", 12.9165, 77.6101),
    "Bannerghatta": AreaCoordinates("Bannerghatta", 12.8000, 77.5667),
    "Bommanahalli": AreaCoordinates("Bommanahalli", 12.9000, 77.6333),
    "Devanahalli": AreaCoordinates("Devanahalli", 13.2333, 77.7167),
    "Electronic City": AreaCoordinates("Electronic City", 12.8456, 77.6603),
    "HSR Layout": AreaCoordinates("HSR Layout", 12.9082, 77.6476),
    "Hebbal": AreaCoordinates("Hebbal", 13.0358, 77.5970),
    "Indiranagar": AreaCoordinates("Indiranagar", 12.9719, 77.6412),
    "Jayanagar": AreaCoordinates("Jayanagar", 12.9230, 77.5845),
    "Kengeri": AreaCoordinates("Kengeri", 12.9069, 77.4839),
    "Koramangala": AreaCoordinates("Koramangala", 12.9279, 77.6271),
    "Malleswaram": AreaCoordinates("Malleswaram", 13.0027, 77.5674),
    "Marathahalli": AreaCoordinates("Marathahalli", 12.9592, 77.6974),
    "Rajajinagar": AreaCoordinates("Rajajinagar", 13.0067, 77.5523),
    "Sarjapur": AreaCoordinates("Sarjapur", 12.8580, 77.7850),
    "Whitefield": AreaCoordinates("Whitefield", 12.9698, 77.7499),
    "Yelahanka": AreaCoordinates("Yelahanka", 13.1007, 77.5962),
}


class WeatherCache:
    """
    Thread-safe weather cache with TTL support.
    
    Cache keys: (area, target_date, weather_type) where weather_type in 
    {'current', 'forecast', 'historical'}
    
    TTL:
    - current/forecast: ~1 hour (3600 seconds)
    - historical: ~24 hours (86400 seconds)
    """
    
    def __init__(
        self,
        current_ttl: int = 3600,
        forecast_ttl: int = 3600,
        historical_ttl: int = 86400,
        cache_file: Optional[Path] = None
    ):
        self.current_ttl = current_ttl
        self.forecast_ttl = forecast_ttl
        self.historical_ttl = historical_ttl
        self.cache_file = cache_file
        self._cache: Dict[str, Tuple[WeatherFeatures, float]] = {}
        self._lock = threading.RLock()
        self._load_from_file()
    
    def _make_key(self, area: str, target_date: str, weather_type: str) -> str:
        return f"{area}|{target_date}|{weather_type}"
    
    def _get_ttl(self, weather_type: str) -> int:
        if weather_type == "historical":
            return self.historical_ttl
        return self.current_ttl  # current and forecast use same TTL
    
    def get(self, area: str, target_date: str, weather_type: str) -> Optional[WeatherFeatures]:
        key = self._make_key(area, target_date, weather_type)
        with self._lock:
            if key in self._cache:
                features, timestamp = self._cache[key]
                if time.time() - timestamp < self._get_ttl(weather_type):
                    logger.debug(f"Cache hit: {key}")
                    return features
                else:
                    logger.debug(f"Cache expired: {key}")
                    del self._cache[key]
            return None
    
    def set(self, area: str, target_date: str, weather_type: str, features: WeatherFeatures) -> None:
        key = self._make_key(area, target_date, weather_type)
        with self._lock:
            self._cache[key] = (features, time.time())
            self._save_to_file()
    
    def _save_to_file(self) -> None:
        if not self.cache_file:
            return
        try:
            data = {
                k: {"features": asdict(v[0]), "timestamp": v[1]}
                for k, v in self._cache.items()
            }
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save weather cache: {e}")
    
    def _load_from_file(self) -> None:
        if not self.cache_file or not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            for k, v in data.items():
                features = WeatherFeatures(**v["features"])
                self._cache[k] = (features, v["timestamp"])
            logger.info(f"Loaded {len(self._cache)} entries from weather cache")
        except Exception as e:
            logger.warning(f"Failed to load weather cache: {e}")


class WeatherService:
    """
    Production-ready weather service for SmartWaste ML feature pipeline.
    
    Uses OpenWeatherMap API (https://openweathermap.org/api)
    Requires OPENWEATHER_API_KEY environment variable.
    
    Features:
    - Current weather
    - 5-day/3-hour forecast (free tier)
    - Historical weather (requires paid plan or One Call API 3.0)
    - Caching with configurable TTL
    - Graceful fallback to historical averages
    - Explicit missing data indicators
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"
    
    # Monthly historical averages for Bangalore (fallback when API unavailable)
    # Derived from synthetic training data statistics
    HISTORICAL_MONTHLY_AVG: Dict[int, Dict[str, float]] = {
        1: {"temp_max_c": 28.5, "rainfall_mm": 0.5, "humidity_pct": 65.0},
        2: {"temp_max_c": 30.5, "rainfall_mm": 0.3, "humidity_pct": 58.0},
        3: {"temp_max_c": 33.0, "rainfall_mm": 1.0, "humidity_pct": 55.0},
        4: {"temp_max_c": 34.5, "rainfall_mm": 5.0, "humidity_pct": 60.0},
        5: {"temp_max_c": 33.5, "rainfall_mm": 15.0, "humidity_pct": 70.0},
        6: {"temp_max_c": 30.0, "rainfall_mm": 80.0, "humidity_pct": 85.0},
        7: {"temp_max_c": 29.0, "rainfall_mm": 120.0, "humidity_pct": 88.0},
        8: {"temp_max_c": 29.0, "rainfall_mm": 110.0, "humidity_pct": 88.0},
        9: {"temp_max_c": 29.5, "rainfall_mm": 90.0, "humidity_pct": 85.0},
        10: {"temp_max_c": 29.5, "rainfall_mm": 40.0, "humidity_pct": 78.0},
        11: {"temp_max_c": 28.5, "rainfall_mm": 10.0, "humidity_pct": 70.0},
        12: {"temp_max_c": 27.5, "rainfall_mm": 2.0, "humidity_pct": 65.0},
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache: Optional[WeatherCache] = None,
        timeout: int = 10,
        enable_fallback: bool = True
    ):
        """
        Initialize weather service.
        
        Args:
            api_key: OpenWeatherMap API key. If None, reads from OPENWEATHER_API_KEY env var.
            cache: WeatherCache instance. If None, creates default file-based cache.
            timeout: Request timeout in seconds.
            enable_fallback: Whether to use historical averages when API fails.
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.timeout = timeout
        self.enable_fallback = enable_fallback
        
        if cache is None:
            cache_dir = Path(__file__).parent.parent.parent / "cache"
            cache_file = cache_dir / "weather_cache.json"
            self.cache = WeatherCache(cache_file=cache_file)
        else:
            self.cache = cache
        
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "SmartWaste/1.0"})
        
        if not self.api_key:
            logger.warning("OPENWEATHER_API_KEY not set. Weather service will use fallback only.")
    
    def get_coordinates(self, area: str) -> Optional[AreaCoordinates]:
        """Get latitude/longitude for a SmartWaste area."""
        return AREA_COORDINATES.get(area)
    
    def get_weather_features(
        self,
        area: str,
        target_date: date,
        prediction_time: Optional[datetime] = None
    ) -> WeatherFeatures:
        """
        Get ML-ready weather features for an area and target date.
        
        This is the main entry point for the ML pipeline.
        
        Args:
            area: SmartWaste area name
            target_date: Date for which weather is needed
            prediction_time: When the prediction is being made (for leakage prevention).
                           Defaults to now. For historical training, pass the actual prediction time.
        
        Returns:
            WeatherFeatures with temp_max_c, rainfall_mm, humidity_pct
        """
        prediction_time = prediction_time or datetime.now()
        target_date_str = target_date.isoformat()
        area_coords = self.get_coordinates(area)
        
        if not area_coords:
            logger.warning(f"Unknown area: {area}. Using fallback.")
            return self._get_fallback_features(area, target_date, "unknown_area")
        
        # Determine weather type based on target_date vs prediction_time
        days_ahead = (target_date - prediction_time.date()).days
        
        if days_ahead < 0:
            # Historical date - use historical data
            return self._get_historical_weather(area_coords, target_date, target_date_str)
        elif days_ahead == 0:
            # Today - use current weather
            return self._get_current_weather(area_coords, target_date, target_date_str)
        elif days_ahead <= 5:
            # Within 5 days - use forecast
            return self._get_forecast_weather(area_coords, target_date, target_date_str, days_ahead)
        else:
            # Beyond forecast range - use historical monthly average
            logger.info(f"Target date {target_date} is {days_ahead} days ahead (>5), using historical average")
            return self._get_historical_average(area, target_date, target_date_str)
    
    def _get_current_weather(
        self,
        coords: AreaCoordinates,
        target_date: date,
        target_date_str: str
    ) -> WeatherFeatures:
        """Get current weather from API or cache."""
        # Check cache first
        cached = self.cache.get(coords.area, target_date_str, "current")
        if cached:
            return cached
        
        if not self.api_key:
            return self._get_fallback_features(coords.area, target_date, "no_api_key")
        
        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                "lat": coords.latitude,
                "lon": coords.longitude,
                "appid": self.api_key,
                "units": "metric"
            }
            response = self._session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            features = WeatherFeatures(
                temp_max_c=data["main"].get("temp_max", data["main"]["temp"]),
                rainfall_mm=data.get("rain", {}).get("1h", 0.0),
                humidity_pct=data["main"]["humidity"],
                source="api_current",
                fetched_at=datetime.now().isoformat(),
                area=coords.area,
                target_date=target_date_str,
                is_missing=False
            )
            self.cache.set(coords.area, target_date_str, "current", features)
            logger.info(f"Fetched current weather for {coords.area} on {target_date_str}")
            return features
            
        except requests.RequestException as e:
            logger.warning(f"Current weather API failed for {coords.area}: {e}")
            return self._get_fallback_features(coords.area, target_date, "api_error")
    
    def _get_forecast_weather(
        self,
        coords: AreaCoordinates,
        target_date: date,
        target_date_str: str,
        days_ahead: int
    ) -> WeatherFeatures:
        """Get forecast weather from API or cache."""
        # Check cache first
        cached = self.cache.get(coords.area, target_date_str, "forecast")
        if cached:
            return cached
        
        if not self.api_key:
            return self._get_fallback_features(coords.area, target_date, "no_api_key")
        
        try:
            # Use 5-day/3-hour forecast (free tier)
            url = f"{self.BASE_URL}/forecast"
            params = {
                "lat": coords.latitude,
                "lon": coords.longitude,
                "appid": self.api_key,
                "units": "metric"
            }
            response = self._session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            # Find forecast entries for target date
            target_entries = []
            for entry in data["list"]:
                entry_date = datetime.fromtimestamp(entry["dt"]).date()
                if entry_date == target_date:
                    target_entries.append(entry)
            
            if not target_entries:
                logger.warning(f"No forecast entries for {coords.area} on {target_date_str}")
                return self._get_fallback_features(coords.area, target_date, "no_forecast_data")
            
            # Aggregate: max temp, sum rainfall, mean humidity
            temps = [e["main"]["temp_max"] for e in target_entries]
            rainfalls = [e.get("rain", {}).get("3h", 0.0) for e in target_entries]
            humidities = [e["main"]["humidity"] for e in target_entries]
            
            features = WeatherFeatures(
                temp_max_c=max(temps),
                rainfall_mm=sum(rainfalls),
                humidity_pct=sum(humidities) / len(humidities),
                source="api_forecast",
                fetched_at=datetime.now().isoformat(),
                area=coords.area,
                target_date=target_date_str,
                is_missing=False
            )
            self.cache.set(coords.area, target_date_str, "forecast", features)
            logger.info(f"Fetched forecast weather for {coords.area} on {target_date_str} ({days_ahead} days ahead)")
            return features
            
        except requests.RequestException as e:
            logger.warning(f"Forecast weather API failed for {coords.area}: {e}")
            return self._get_fallback_features(coords.area, target_date, "api_error")
    
    def _get_historical_weather(
        self,
        coords: AreaCoordinates,
        target_date: date,
        target_date_str: str
    ) -> WeatherFeatures:
        """Get historical weather from API or cache."""
        # Check cache first
        cached = self.cache.get(coords.area, target_date_str, "historical")
        if cached:
            return cached
        
        if not self.api_key:
            return self._get_fallback_features(coords.area, target_date, "no_api_key")
        
        try:
            # OpenWeatherMap One Call API 3.0 for historical (requires paid plan)
            # For free tier, we fall back to historical averages
            # If you have paid plan, uncomment and use:
            """
            url = f"{self.ONECALL_URL}/timemachine"
            params = {
                "lat": coords.latitude,
                "lon": coords.longitude,
                "dt": int(datetime.combine(target_date, datetime.min.time()).timestamp()),
                "appid": self.api_key,
                "units": "metric"
            }
            response = self._session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            # Process historical data...
            """
            
            # Free tier fallback: use historical monthly average
            logger.info(f"Historical weather API not available (free tier), using monthly average for {coords.area}")
            return self._get_historical_average(coords.area, target_date, target_date_str)
            
        except requests.RequestException as e:
            logger.warning(f"Historical weather API failed for {coords.area}: {e}")
            return self._get_fallback_features(coords.area, target_date, "api_error")
    
    def _get_historical_average(
        self,
        area: str,
        target_date: date,
        target_date_str: str
    ) -> WeatherFeatures:
        """Get historical monthly average for the area/month."""
        month = target_date.month
        avg = self.HISTORICAL_MONTHLY_AVG.get(month, self.HISTORICAL_MONTHLY_AVG[1])
        
        features = WeatherFeatures(
            temp_max_c=avg["temp_max_c"],
            rainfall_mm=avg["rainfall_mm"],
            humidity_pct=avg["humidity_pct"],
            source="historical_avg",
            fetched_at=datetime.now().isoformat(),
            area=area,
            target_date=target_date_str,
            is_missing=True  # Flag that this is not real observed/forecast data
        )
        # Cache historical averages for 24 hours
        self.cache.set(area, target_date_str, "historical", features)
        return features
    
    def _get_fallback_features(
        self,
        area: str,
        target_date: date,
        reason: str
    ) -> WeatherFeatures:
        """Generate fallback features with explicit missing indicator."""
        if not self.enable_fallback:
            return WeatherFeatures(
                temp_max_c=None,
                rainfall_mm=None,
                humidity_pct=None,
                source=f"fallback_disabled_{reason}",
                fetched_at=datetime.now().isoformat(),
                area=area,
                target_date=target_date.isoformat(),
                is_missing=True
            )
        
        # Use historical monthly average as fallback
        month = target_date.month
        avg = self.HISTORICAL_MONTHLY_AVG.get(month, self.HISTORICAL_MONTHLY_AVG[1])
        
        logger.warning(f"Using fallback for {area} on {target_date}: {reason}")
        return WeatherFeatures(
            temp_max_c=avg["temp_max_c"],
            rainfall_mm=avg["rainfall_mm"],
            humidity_pct=avg["humidity_pct"],
            source=f"fallback_{reason}",
            fetched_at=datetime.now().isoformat(),
            area=area,
            target_date=target_date.isoformat(),
            is_missing=True  # Explicit flag: NOT real weather data
        )


# Singleton instance
_weather_service: Optional[WeatherService] = None
_service_lock = threading.Lock()


def get_weather_service() -> WeatherService:
    """Get or create the singleton weather service instance."""
    global _weather_service
    with _service_lock:
        if _weather_service is None:
            _weather_service = WeatherService()
        return _weather_service


def reset_weather_service() -> None:
    """Reset the singleton (mainly for testing)."""
    global _weather_service
    with _service_lock:
        _weather_service = None


# Convenience function for ML predictors - returns simple tuple for backward compatibility
def get_weather_features(
    area: str,
    target_date: date,
    prediction_time: Optional[datetime] = None
) -> Tuple[float, float, float]:
    """
    Get weather features as a simple tuple for backward compatibility.
    
    Returns:
        (temp_max_c, rainfall_mm, humidity_pct)
        
    Note: Always returns floats (never None). Check is_missing via get_weather_service().get_weather_features()
    if you need to know whether real data was used.
    """
    service = get_weather_service()
    features = service.get_weather_features(area, target_date, prediction_time)
    
    # Return defaults if missing (for backward compatibility with existing models)
    if features.is_missing or features.temp_max_c is None:
        month = target_date.month
        avg = WeatherService.HISTORICAL_MONTHLY_AVG.get(month, WeatherService.HISTORICAL_MONTHLY_AVG[1])
        return (avg["temp_max_c"], avg["rainfall_mm"], avg["humidity_pct"])
    
    return (features.temp_max_c, features.rainfall_mm, features.humidity_pct)