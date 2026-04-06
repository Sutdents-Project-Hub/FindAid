import os

from labmate.db import ensure_schema, get_connection
from labmate.app_logic import build_action_plan, classify_need
from labmate.resources import load_sample_resources, search_resources, upsert_resources


def main():
    conn = get_connection(":memory:")
    ensure_schema(conn)

    sample_path = os.path.join("data", "sample", "resources.json")
    resources = load_sample_resources(sample_path)
    upsert_resources(conn, resources)

    need = classify_need("就業", "履歷 面試")
    hits = search_resources(conn, need.get("query"), limit=5)

    settings = {"offline": True, "openai_model": "gpt-4o-mini"}
    plan = build_action_plan(settings, llm_client=None, need_category=need.get("category"), user_text=need.get("query"), resources=hits)
    assert plan.get("crisis") is not True
    assert isinstance(plan.get("steps"), list) and len(plan.get("steps")) > 0
    assert isinstance(plan.get("materials"), list) and len(plan.get("materials")) > 0

    print("OK")


if __name__ == "__main__":
    main()

