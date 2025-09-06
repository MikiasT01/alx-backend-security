import logging
from django.http import HttpRequest, HttpResponseForbidden
from django.core.cache import cache
from .models import RequestLog, BlockedIP
from ipware import get_client_ip
import geoip2.database
import os

logger = logging.getLogger(__name__)

    # Path to GeoIP2 City database (download from https://www.maxmind.com)
GEOIP_PATH = os.path.join(os.path.dirname(__file__), 'GeoLite2-City.mmdb')

class IPLoggingMiddleware:
        def __init__(self, get_response):
            self.get_response = get_response
            self.reader = geoip2.database.Reader(GEOIP_PATH)

        def __call__(self, request: HttpRequest):
            # Get client IP
            ip, _ = get_client_ip(request)
            if ip:
                # Check if IP is blocked
                if BlockedIP.objects.filter(ip_address=ip).exists():
                    logger.warning(f"Blocked request from blacklisted IP: {ip}, Path: {request.path}")
                    return HttpResponseForbidden("Access denied: Your IP is blocked.")
                
                # Get or cache geolocation data
                cache_key = f"geo_{ip}"
                geo_data = cache.get(cache_key)
                if geo_data is None:
                    try:
                        response = self.reader.city(ip)
                        geo_data = {
                            "country": response.country.name,
                            "city": response.city.name
                        }
                        cache.set(cache_key, geo_data, timeout=24 * 60 * 60)  # Cache for 24 hours
                    except Exception as e:
                        logger.error(f"Geolocation error for {ip}: {str(e)}")
                        geo_data = {"country": None, "city": None}
                
                country = geo_data.get("country", None)
                city = geo_data.get("city", None)
                
                # Log request with geolocation
                log_entry = RequestLog.objects.create(
                    ip_address=ip,
                    path=request.path,
                    country=country,
                    city=city
                )
                logger.info(f"Logged request from IP: {ip}, Path: {request.path}, Country: {country}, City: {city}")
            response = self.get_response(request)
            return response

        def __del__(self):
            self.reader.close()  # Close the reader to free resources