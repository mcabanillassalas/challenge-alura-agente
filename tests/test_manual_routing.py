from app.core.manual_routing import infer_manual_code


from pathlib import Path

from app.core.manual_routing import get_manual_family, infer_manual_code, load_manual_routing_config


def test_load_manual_routing_config_uses_yaml_file() -> None:
    config = load_manual_routing_config(Path("app/core/manual_routing.yml"))
    assert config["manual_code_family"]["AS"] == "administracion_sistema"
    assert any(
        item["keyword"] == "usuarios" and item["weight"] == 1
        for item in config["query_routing_rules"]["AS"]
    )


def test_infer_manual_code_for_user_creation() -> None:
    assert infer_manual_code("puedes darme informacion referente a la creacion de usuarios en Exactus") == "AS"


def test_infer_manual_code_for_hr_topic() -> None:
    assert infer_manual_code("cómo se maneja la información de empleados en Exactus") == "RH"


def test_get_manual_family_defaults_to_general_when_unknown() -> None:
    assert get_manual_family("ZZ", Path("app/core/manual_routing.yml")) == "general"