"""
成因敘述與溢流預報（規則＋模板，不用 LLM）。

    from pipeline.attribution import attribute, describe

用延遲匯入，避免 python -m pipeline.attribution.rules 出現重複載入警告。
"""

__all__ = [
    "attribute", "describe", "Composer", "Narrative",
    "Attribution", "LakeRecord", "Observations",
]

_LOCATIONS = {
    "attribute": "rules",
    "Attribution": "rules",
    "LakeRecord": "rules",
    "Observations": "rules",
    "describe": "compose",
    "Composer": "compose",
    "Narrative": "compose",
}


def __getattr__(name):
    module = _LOCATIONS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module
    return getattr(import_module(f".{module}", __name__), name)


def __dir__():
    return sorted(__all__)
