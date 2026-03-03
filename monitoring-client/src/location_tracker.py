"""Location tracking module for the monitoring client."""

import geocoder
from typing import Optional, Dict
from .logger import get_logger

logger = get_logger()


class LocationTracker:
    """Handles location tracking using IP-based geolocation."""
    
    def __init__(self):
        """Initialize the location tracker."""
        self._cached_location: Optional[Dict[str, str]] = None
    
    def get_location(self) -> Optional[Dict[str, str]]:
        """
        Get the current location based on IP address.
        
        Returns:
            Dictionary with 'city', 'state', and 'country' keys, or None if unable to determine.
        """
        logger.info("🌍 Attempting to get location from IP address...")
        try:
            # Use 'me' to get location from current IP
            logger.debug("Calling geocoder.ip('me')...")
            g = geocoder.ip('me')
            
            logger.info(f"Geocoder response - OK: {g.ok}, IP: {g.ip if hasattr(g, 'ip') else 'N/A'}")
            logger.debug(f"Geocoder full response: {g.json if hasattr(g, 'json') else 'N/A'}")
            
            if g.ok:
                location = {
                    'city': g.city or 'Unknown',
                    'state': g.state or 'Unknown',
                    'country': g.country or 'Unknown'
                }
                
                # Cache the location
                self._cached_location = location
                
                logger.info(f"✅ Location detected successfully: {location['city']}, {location['state']}, {location['country']}")
                print(f"✅ Location detected: {location['city']}, {location['state']}, {location['country']}")
                return location
            else:
                logger.warning(f"⚠️ Geocoder returned not OK. Status: {g.status if hasattr(g, 'status') else 'N/A'}")
                if self._cached_location:
                    logger.info(f"Using cached location: {self._cached_location}")
                    print(f"ℹ️ Using cached location: {self._cached_location['city']}, {self._cached_location['state']}")
                else:
                    logger.warning("No cached location available")
                    print("⚠️ No location data available (no cache)")
                return self._cached_location  # Return cached location if available
                
        except Exception as e:
            logger.error(f"❌ Error getting location: {e}", exc_info=True)
            print(f"❌ Error getting location: {e}")
            if self._cached_location:
                logger.info(f"Using cached location after error: {self._cached_location}")
                print(f"ℹ️ Using cached location: {self._cached_location['city']}, {self._cached_location['state']}")
            return self._cached_location  # Return cached location if available
    
    def get_location_string(self) -> str:
        """
        Get location as a formatted string.
        
        Returns:
            Formatted location string like "City, State, Country" or "Unknown" if unavailable.
        """
        location = self.get_location()
        if location:
            return f"{location['city']}, {location['state']}, {location['country']}"
        return "Unknown"
