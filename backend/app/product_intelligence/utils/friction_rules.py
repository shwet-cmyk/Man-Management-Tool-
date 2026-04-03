from datetime import timedelta

def is_rage_click(clicks: list[dict]) -> bool:
    if len(clicks) < 3:
        return False
    return (clicks[-1]['event_timestamp'] - clicks[0]['event_timestamp']) <= timedelta(seconds=6)
