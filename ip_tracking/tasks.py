from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone
from datetime import timedelta
from .models import RequestLog, SuspiciousIP
import logging

logger = logging.getLogger(__name__)

@shared_task
def detect_anomalies():
        # Define the time window (last hour)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Sensitive paths to monitor
        sensitive_paths = ['/admin', '/login', '/login/anonymous']
        
        # Get all IPs and their request counts in the last hour
        request_counts = RequestLog.objects.filter(timestamp__gte=one_hour_ago).values('ip_address').annotate(count=models.Count('id'))
        
        for entry in request_counts:
            ip = entry['ip_address']
            count = entry['count']
            
            # Flag IPs exceeding 100 requests/hour
            if count > 100:
                reason = f"Exceeded 100 requests/hour ({count})"
                SuspiciousIP.objects.get_or_create(ip_address=ip, defaults={'reason': reason})
                logger.warning(f"Flagged suspicious IP {ip} for {reason}")
            
            # Check for sensitive path access
            sensitive_access = RequestLog.objects.filter(
                ip_address=ip,
                timestamp__gte=one_hour_ago,
                path__in=sensitive_paths
            ).exists()
            if sensitive_access and not SuspiciousIP.objects.filter(ip_address=ip).exists():
                reason = "Accessed sensitive path"
                SuspiciousIP.objects.get_or_create(ip_address=ip, defaults={'reason': reason})
                logger.warning(f"Flagged suspicious IP {ip} for {reason}")