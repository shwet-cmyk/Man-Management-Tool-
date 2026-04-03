def classify_change(field_name: str | None) -> str:
    if not field_name:
        return 'FLOW'
    low = field_name.lower()
    if 'label' in low:
        return 'LABEL'
    if 'route' in low:
        return 'ROUTE'
    if 'help' in low:
        return 'HELP'
    return 'FIELD'
