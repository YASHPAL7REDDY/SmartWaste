"""
Festival and Holiday Calendar Service for SmartWaste ML Pipeline
================================================================

Provides calendar features (is_holiday, is_festival, festival_intensity) 
using a configurable local calendar file.

No external API dependencies. Pure Python with YAML configuration.
"""

import os
import yaml
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """Represents a holiday, festival, or special event."""
    name: str
    event_date: date
    event_type: str  # 'holiday', 'festival'
    intensity: float = 1.0
    window_days: int = 0


@dataclass
class CalendarFeatures:
    """ML-ready calendar features matching the preprocessing pipeline."""
    is_holiday: bool
    is_festival: bool
    festival_intensity: float
    source: str  # 'config', 'fallback'
    events: List[str]  # names of events on this date


class CalendarService:
    """
    Production-ready calendar service for SmartWaste ML feature pipeline.
    
    Reads holiday/festival definitions from a YAML configuration file.
    Supports:
    - Recurring holidays (same month-day every year)
    - Specific-date holidays (specific years only)
    - Festivals with intensity and window days
    - Festival window days with 50% intensity decay
    
    Configuration file: backend/config/india_calendar.yaml
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize calendar service.
        
        Args:
            config_path: Path to YAML calendar config. Defaults to backend/config/india_calendar.yaml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "india_calendar.yaml"
        
        self.config_path = config_path
        self._events: Dict[date, List[CalendarEvent]] = {}
        self._lock = threading.RLock()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load and parse the calendar configuration file."""
        with self._lock:
            self._events = {}
            
            if not self.config_path.exists():
                logger.warning(f"Calendar config not found at {self.config_path}. Using empty calendar.")
                return
            
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                if not config:
                    logger.warning("Calendar config is empty.")
                    return
                
                # Parse national holidays (recurring)
                for holiday in config.get("national_holidays", []):
                    self._add_recurring_holiday(holiday, "holiday")
                
                # Parse Karnataka holidays (recurring + specific dates)
                for holiday in config.get("karnataka_holidays", []):
                    if "date" in holiday:
                        self._add_recurring_holiday(holiday, "holiday")
                    elif "dates" in holiday:
                        self._add_specific_dates(holiday, "holiday")
                
                # Parse festivals with windows
                for festival in config.get("festivals", []):
                    self._add_festival(festival)
                
                logger.info(f"Loaded calendar with {len(self._events)} event dates")
                
            except Exception as e:
                logger.error(f"Failed to load calendar config: {e}")
                self._events = {}
    
    def _add_recurring_holiday(self, holiday: dict, event_type: str) -> None:
        """Add a holiday that recurs on the same month-day each year."""
        month_day = holiday["date"]
        month, day = map(int, month_day.split("-"))
        name = holiday["name"]
        
        # Generate for a wide range of years (2020-2030)
        for year in range(2020, 2031):
            try:
                event_date = date(year, month, day)
                if event_date not in self._events:
                    self._events[event_date] = []
                self._events[event_date].append(CalendarEvent(
                    name=name,
                    event_date=event_date,
                    event_type=event_type,
                    intensity=1.0,
                    window_days=0
                ))
            except ValueError:
                pass  # Invalid date (e.g., Feb 30)
    
    def _add_specific_dates(self, holiday: dict, event_type: str) -> None:
        """Add a holiday with specific dates per year."""
        name = holiday["name"]
        for date_str in holiday.get("dates", []):
            try:
                event_date = date.fromisoformat(date_str)
                if event_date not in self._events:
                    self._events[event_date] = []
                self._events[event_date].append(CalendarEvent(
                    name=name,
                    event_date=event_date,
                    event_type=event_type,
                    intensity=1.0,
                    window_days=0
                ))
            except ValueError:
                logger.warning(f"Invalid date format in calendar config: {date_str}")
    
    def _add_festival(self, festival: dict) -> None:
        """Add a festival with a window of effect."""
        name = festival["name"]
        window_days = festival.get("window_days", 0)
        intensity = festival.get("intensity", 1.0)
        
        for date_str in festival.get("dates", []):
            try:
                festival_date = date.fromisoformat(date_str)
                
                # Add main festival date
                if festival_date not in self._events:
                    self._events[festival_date] = []
                self._events[festival_date].append(CalendarEvent(
                    name=name,
                    event_date=festival_date,
                    event_type="festival",
                    intensity=intensity,
                    window_days=window_days
                ))
                
                # Add window days (pre and post festival) with 50% intensity
                if window_days > 0:
                    for i in range(1, window_days + 1):
                        for offset in [-i, i]:
                            window_date = festival_date + timedelta(days=offset)
                            if window_date not in self._events:
                                self._events[window_date] = []
                            window_name = f"{name} ({'+' if offset > 0 else ''}{offset}d)"
                            self._events[window_date].append(CalendarEvent(
                                name=window_name,
                                event_date=window_date,
                                event_type="festival",
                                intensity=intensity * 0.5,
                                window_days=0
                            ))
            except ValueError:
                logger.warning(f"Invalid date format in festival config: {date_str}")
    
    def get_calendar_features(self, target_date: date) -> CalendarFeatures:
        """
        Get ML-ready calendar features for a target date.
        
        This is the main entry point for the ML pipeline.
        
        Args:
            target_date: Date for which calendar features are needed
            
        Returns:
            CalendarFeatures with is_holiday, is_festival, festival_intensity
        """
        events = self._events.get(target_date, [])
        
        if not events:
            return CalendarFeatures(
                is_holiday=False,
                is_festival=False,
                festival_intensity=0.0,
                source="fallback",
                events=[]
            )
        
        # Check for holidays and festivals
        is_holiday = any(e.event_type == "holiday" for e in events)
        is_festival = any(e.event_type == "festival" for e in events)
        
        # Get maximum intensity (festival intensity takes precedence for ML)
        festival_intensity = max(
            (e.intensity for e in events if e.event_type == "festival"),
            default=0.0
        )
        
        event_names = [e.name for e in events]
        
        logger.debug(f"Calendar for {target_date}: holiday={is_holiday}, festival={is_festival}, "
                     f"intensity={festival_intensity}, events={event_names}")
        
        return CalendarFeatures(
            is_holiday=is_holiday,
            is_festival=is_festival,
            festival_intensity=festival_intensity,
            source="config",
            events=event_names
        )
    
    def get_events_for_date(self, target_date: date) -> List[CalendarEvent]:
        """Get all events for a specific date."""
        return self._events.get(target_date, [])
    
    def reload_config(self) -> None:
        """Reload the calendar configuration (useful for updates without restart)."""
        logger.info("Reloading calendar configuration...")
        self._load_config()


# Singleton instance
_calendar_service: Optional[CalendarService] = None
_service_lock = threading.Lock()


def get_calendar_service(config_path: Optional[Path] = None) -> CalendarService:
    """Get or create the singleton calendar service instance."""
    global _calendar_service
    with _service_lock:
        if _calendar_service is None:
            _calendar_service = CalendarService(config_path)
        return _calendar_service


def reset_calendar_service() -> None:
    """Reset the singleton (mainly for testing)."""
    global _calendar_service
    with _service_lock:
        _calendar_service = None


# Convenience function for ML predictors - returns simple tuple for backward compatibility
def get_calendar_features(
    target_date: date
) -> Tuple[bool, bool, float]:
    """
    Get calendar features as a simple tuple for backward compatibility.
    
    Returns:
        (is_holiday, is_festival, festival_intensity)
    """
    service = get_calendar_service()
    features = service.get_calendar_features(target_date)
    return (features.is_holiday, features.is_festival, features.festival_intensity)