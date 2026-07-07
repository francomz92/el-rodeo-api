def __getattr__(name: str):
    """Lazy imports to avoid circular dependency with _registry.

    The _registry module imports from auth/ repos which in turn import
    from this package (mixins, tenant_aware_repository). Eager loading
    would create a circular import chain.
    """
    import importlib

    mapping = {
        "repositories_list": "._registry",
    }
    if name in mapping:
        mod = importlib.import_module(mapping[name], __package__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["repositories_list"]
