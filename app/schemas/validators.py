def _strip_and_validate(value: str | None, field_label: str) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError(f"Название {field_label} не может быть пустым")
    if len(value) > 200:
        raise ValueError(f"Название {field_label} не может быть длиннее 200 символов")
    return value