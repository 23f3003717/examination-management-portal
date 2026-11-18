from datetime import datetime
def parse_iso_datetime(value, field_name):
    try:return datetime.fromisoformat(value)
    except (TypeError,ValueError):raise ValueError(f"{field_name} must be an ISO date/time string")
