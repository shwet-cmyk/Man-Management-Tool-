from __future__ import annotations

class AiUxRecommendationService:
    def generate(self, *, dead_clicks: list[dict], rage_clicks: list[dict], error_events: list[dict], help_open_count: int = 0) -> list[dict]:
        recs = []
        if dead_clicks:
            recs.append({'module_name': dead_clicks[0]['screen_key'].split('_')[0], 'screen_key': dead_clicks[0]['screen_key'], 'recommendation_title': 'Dead click friction detected', 'recommendation_text': 'Make primary action visibly enabled or de-emphasize non-actionable controls.', 'evidence_summary': f"dead_click_count={len(dead_clicks)}", 'confidence_score': 0.82, 'severity_level': 'HIGH', 'status': 'NEW'})
        if rage_clicks:
            recs.append({'module_name': rage_clicks[0]['screen_key'].split('_')[0], 'screen_key': rage_clicks[0]['screen_key'], 'recommendation_title': 'Rage click pattern detected', 'recommendation_text': 'Improve response latency and add inline loading/confirmation feedback.', 'evidence_summary': f"rage_click_count={len(rage_clicks)}", 'confidence_score': 0.79, 'severity_level': 'HIGH', 'status': 'NEW'})
        if error_events:
            recs.append({'module_name': error_events[0]['module_name'], 'screen_key': error_events[0]['screen_key'], 'recommendation_title': 'Error cluster requires UX guidance', 'recommendation_text': 'Add inline validation hints and refine error message copy.', 'evidence_summary': f"error_event_count={len(error_events)}", 'confidence_score': 0.76, 'severity_level': 'MEDIUM', 'status': 'NEW'})
        if help_open_count > 10:
            recs.append({'module_name': 'global', 'screen_key': None, 'recommendation_title': 'High help usage indicates discoverability gap', 'recommendation_text': 'Move common actions higher and add contextual helper text near key controls.', 'evidence_summary': f"help_open_count={help_open_count}", 'confidence_score': 0.69, 'severity_level': 'MEDIUM', 'status': 'NEW'})
        return recs
