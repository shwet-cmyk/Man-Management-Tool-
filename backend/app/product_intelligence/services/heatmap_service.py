from __future__ import annotations
from collections import Counter

class HeatmapService:
    def aggregate(self, events: list[dict], heatmap_type: str = 'CLICK') -> list[dict]:
        key_counter = Counter((e['route_path'], e['screen_key'], e.get('element_id')) for e in events)
        return [
            {
                'route_path': route,
                'screen_key': screen,
                'module_name': next((e['module_name'] for e in events if e['route_path']==route and e['screen_key']==screen), 'Unknown'),
                'element_id': element,
                'heatmap_type': heatmap_type,
                'interaction_count': count,
            }
            for (route, screen, element), count in key_counter.items()
        ]
