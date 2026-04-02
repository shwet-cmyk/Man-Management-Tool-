from __future__ import annotations
from collections import defaultdict
from app.product_intelligence.utils.friction_rules import is_rage_click

class FrictionDetectionService:
    def detect(self, events: list[dict]) -> tuple[list[dict], list[dict]]:
        grouped: dict[tuple[str, str, str | None], list[dict]] = defaultdict(list)
        for e in events:
            grouped[(e['route_path'], e['screen_key'], e.get('element_id'))].append(e)

        dead_clicks: list[dict] = []
        rage_clicks: list[dict] = []
        for key, rows in grouped.items():
            route_path, screen_key, element_id = key
            button_clicks = [r for r in rows if r['event_type'] in {'BUTTON_CLICK', 'ROW_CLICK', 'NO_RESPONSE_CLICK'}]
            if not button_clicks:
                continue
            if any(r['event_type'] == 'NO_RESPONSE_CLICK' for r in button_clicks):
                dead_clicks.append({'route_path': route_path, 'screen_key': screen_key, 'element_id': element_id, 'click_timestamp': button_clicks[-1]['event_timestamp'], 'click_count': len(button_clicks)})
            if is_rage_click(button_clicks):
                rage_clicks.append({'route_path': route_path, 'screen_key': screen_key, 'element_id': element_id, 'first_click_at': button_clicks[0]['event_timestamp'], 'last_click_at': button_clicks[-1]['event_timestamp'], 'click_count': len(button_clicks)})
        return dead_clicks, rage_clicks
