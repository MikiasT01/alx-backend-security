import logging
from django.http import HttpRequest, HttpResponseForbidden
from .models import RequestLog, BlockedIP
from ipware import get_client_ip

logger = logging.getLogger(__name__)

class IPLoggingMiddleware:
        def __init__(self, get_response):
            self.get_response = get_response

        def __call__(self, request: HttpRequest):
            # Get client IP
            ip, _ = get_client_ip(request)
            if ip:
                # Check if IP is blocked
                if BlockedIP.objects.filter(ip_address=ip).exists():
                    logger.warning(f"Blocked request from blacklisted IP: {ip}, Path: {request.path}")
                    return HttpResponseForbidden("Access denied: Your IP is blocked.")
                # Log request if not blocked
                RequestLog.objects.create(ip_address=ip, path=request.path)
                logger.info(f"Logged request from IP: {ip}, Path: {request.path}")
            response = self.get_response(request)
            return response