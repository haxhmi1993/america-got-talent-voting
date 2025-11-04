"""
Metrics endpoint for Prometheus.
"""
from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Define metrics
vote_requests_total = Counter(
    'vote_requests_total',
    'Total number of vote requests',
    ['status']
)

vote_request_duration = Histogram(
    'vote_request_duration_seconds',
    'Vote request duration in seconds'
)


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns:
        Prometheus-formatted metrics
    """
    metrics_output = generate_latest()
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)
