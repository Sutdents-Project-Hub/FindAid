import os


def _env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip().lower()
    if raw in ("1", "true", "yes", "y", "on"):
        return True
    if raw in ("0", "false", "no", "n", "off"):
        return False
    return default


def _env_int(name, default=0):
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip()
    if raw == "":
        return default
    try:
        return int(raw)
    except Exception:
        return default


def _env_str(names, default=""):
    for name in names:
        raw = os.getenv(name)
        if raw is not None:
            return raw.strip()
    return default


def _env_bool_compat(names, default=False):
    for name in names:
        raw = os.getenv(name)
        if raw is not None:
            return _env_bool(name, default=default)
    return default


def _env_int_compat(names, default=0):
    for name in names:
        raw = os.getenv(name)
        if raw is not None:
            return _env_int(name, default=default)
    return default


def load_settings():
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    openai_base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    database_file = _env_str(["FINDAID_DATABASE_FILE", "LABMATE_DATABASE_FILE"], "findaid_data.db") or "findaid_data.db"
    offline = _env_bool_compat(["FINDAID_OFFLINE", "LABMATE_OFFLINE"], default=False) or (openai_api_key == "")
    allow_insecure_ssl = _env_bool_compat(["FINDAID_ALLOW_INSECURE_SSL", "LABMATE_ALLOW_INSECURE_SSL"], default=False)
    open_data_enabled = _env_bool_compat(["FINDAID_OPEN_DATA_ENABLED", "LABMATE_OPEN_DATA_ENABLED"], default=True)
    open_data_ttl_seconds = max(
        0,
        _env_int_compat(["FINDAID_OPEN_DATA_TTL_SECONDS", "LABMATE_OPEN_DATA_TTL_SECONDS"], default=300),
    )

    return {
        "openai_api_key": openai_api_key,
        "openai_base_url": openai_base_url,
        "openai_model": openai_model,
        "database_file": database_file,
        "offline": offline,
        "allow_insecure_ssl": allow_insecure_ssl,
        "open_data_enabled": open_data_enabled,
        "open_data_ttl_seconds": open_data_ttl_seconds,
    }
