"""API publique paresseuse du système de mémoire de JARVIS."""

_MEMORY_EXPORTS = {
    "analyze_memory",
    "find_best_memory",
    "find_semantic_memory",
    "load_memory",
    "recall_memory",
    "remember",
    "save_memory",
    "search_memory",
    "update_missing_embeddings",
}

__all__ = sorted(_MEMORY_EXPORTS)


def __getattr__(name):
    if name in _MEMORY_EXPORTS:
        from . import memory as memory_module

        return getattr(memory_module, name)
    raise AttributeError(f"module 'memory' has no attribute {name!r}")
