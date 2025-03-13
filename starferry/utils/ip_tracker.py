from datetime import datetime, timedelta
import asyncio
from typing import Dict

# Now each IP maps to a dictionary with a timestamp and count of requests.
ip_tracker: Dict[str, Dict] = {}

def track_ip(ip: str) -> bool:
    """
    Increment the count for the given ip and return True if the request is allowed.
    Returns False if the rate limit (10 requests per 30 minutes) is exceeded.
    """
    now = datetime.now()
    if ip not in ip_tracker:
        ip_tracker[ip] = {"timestamp": now, "count": 1}
        return True
    data = ip_tracker[ip]
    if now - data["timestamp"] > timedelta(minutes=30):
        # Reset the count if more than 30 minutes have passed.
        ip_tracker[ip] = {"timestamp": now, "count": 1}
        return True
    elif data["count"] < 10:
        data["count"] += 1
        return True
    else:
        return False

async def cleanup_ip_tracker():
    while True:
        try:
            current_time = datetime.now()
            expired_ips = [
                ip for ip, data in ip_tracker.items()
                if current_time - data["timestamp"] > timedelta(minutes=30)
            ]
            for ip in expired_ips:
                del ip_tracker[ip]
            await asyncio.sleep(1800)  # 30 minutes
        except asyncio.CancelledError:
            break