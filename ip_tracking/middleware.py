import logging
from django.http import HttpRequest
from .models import RequestLog
from ipware import get_client_ip

logger = logging.getLogger(__name__)

class IPLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        ip, _ = get_client_ip(request)
        if ip:
            RequestLog.objects.create(ip_address=ip, path=request.path)
            logger.info(f"Logged request from IP: {ip}, Path: {request.path}")
        response = self.get_response(request)
        return response