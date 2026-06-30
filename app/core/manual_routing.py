from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ROUTING_FILE = Path(__file__).with_name("manual_routing.yml")


def load_manual_routing_config(config_path: Path | None = None) -> dict[str, dict[str, list[dict[str, Any]]]]:
    path = config_path or DEFAULT_ROUTING_FILE
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de enrutamiento: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    manual_code_family = data.get("manual_code_family", {})
    query_routing_rules = data.get("query_routing_rules", {})

    normalized_rules: dict[str, list[dict[str, Any]]] = {}
    for manual_code, keywords in query_routing_rules.items():
        normalized_keywords: list[dict[str, Any]] = []
        for keyword_item in keywords:
            if isinstance(keyword_item, str):
                keyword_text = keyword_item.strip()
                if keyword_text:
                    normalized_keywords.append({"keyword": keyword_text, "weight": 1})
                continue

            if isinstance(keyword_item, dict):
                keyword_text = str(keyword_item.get("keyword", "")).strip()
                if not keyword_text:
                    continue
                weight = int(keyword_item.get("weight", 1) or 1)
                normalized_keywords.append({"keyword": keyword_text, "weight": max(weight, 1)})

        normalized_rules[str(manual_code).upper()] = normalized_keywords

    normalized_family = {
        str(manual_code).upper(): str(family).strip()
        for manual_code, family in manual_code_family.items()
        if str(family).strip()
    }

    return {
        "manual_code_family": normalized_family,
        "query_routing_rules": normalized_rules,
    }


def get_manual_family(manual_code: str, config_path: Path | None = None) -> str:
    config = load_manual_routing_config(config_path)
    return config["manual_code_family"].get(manual_code.upper(), "general")


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(character for character in normalized if not unicodedata.combining(character)).lower()


def infer_manual_code(question: str) -> str | None:
    routing_config = load_manual_routing_config()
    query_routing_rules = routing_config["query_routing_rules"]
    normalized_question = normalize_text(question)

    best_code: str | None = None
    best_score = 0
    for manual_code, keywords in query_routing_rules.items():
        score = 0
        for keyword_item in keywords:
            keyword = str(keyword_item.get("keyword", "")).strip()
            weight = int(keyword_item.get("weight", 1) or 1)
            if keyword and keyword in normalized_question:
                score += weight + max(len(keyword.split()) - 1, 0)
        if score > best_score:
            best_score = score
            best_code = manual_code

    if best_score == 0:
        return None

    return best_code