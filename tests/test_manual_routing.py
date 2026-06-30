from app.core.manual_routing import infer_manual_code


from pathlib import Path

from app.core.manual_routing import get_manual_family, infer_manual_code, load_manual_routing_config
from app.services.rag_chain import _rank_documents


class _FakeDocument:
    def __init__(self, source: str, manual_code: str, title: str, content: str) -> None:
        self.page_content = content
        self.metadata = {
            "source": source,
            "manual_code": manual_code,
            "document_title": title,
            "page": 1,
        }


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


def test_rank_documents_prefers_administration_system_for_user_queries() -> None:
    docs_with_scores = [
        (_FakeDocument("RH_Manual_Usuario_Recursos_Humanos.pdf", "RH", "RH Manual Usuario Recursos Humanos", "cambio de clave de acceso"), 0.2),
        (_FakeDocument("AS_Manual_Usuario_Administracion_Sistema.pdf", "AS", "AS Manual Usuario Administracion Sistema", "usuarios, grupos y privilegios de usuarios"), 0.3),
    ]

    ranked_docs = _rank_documents("puedes darme informacion referente a la creacion de usuarios en Exactus", docs_with_scores)

    assert ranked_docs[0].metadata["manual_code"] == "AS"