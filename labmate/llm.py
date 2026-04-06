import json
import re
from urllib.parse import urlparse

from openai import OpenAI


def _normalize_base_url(base_url):
    base_url = (base_url or "").strip()
    if not base_url:
        return ""
    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        return base_url
    path = parsed.path or ""
    if path in ("", "/"):
        return base_url.rstrip("/") + "/v1"
    if path.rstrip("/") == "/v1":
        return base_url.rstrip("/")
    return base_url.rstrip("/")


def build_client(settings):
    if settings.get("offline"):
        return None
    api_key = settings.get("openai_api_key") or ""
    if not api_key:
        return None
    kwargs = {"api_key": api_key}
    base_url = (settings.get("openai_base_url") or "").strip()
    if base_url:
        kwargs["base_url"] = _normalize_base_url(base_url)
    return OpenAI(**kwargs)


def call_llm(client, model, system_message, user_message, temperature=0.4):
    if client is None:
        raise RuntimeError("LLM_UNAVAILABLE")
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_message}, {"role": "user", "content": user_message}],
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def extract_json_object(text):
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("JSON_NOT_FOUND")
    return json.loads(m.group(0))
