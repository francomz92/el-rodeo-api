def __getattr__(name: str):
    """Lazy imports to avoid circular dependency with _registry.

    The _registry module (in common) imports from this package, and this
    package's __init__ would trigger a circular import if we eagerly loaded
    repository modules here.
    """
    import importlib

    mapping = {
        "RefreshTokenRepository": ".refresh_token_repository",
    }
    if name in mapping:
        mod = importlib.import_module(mapping[name], __package__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["RefreshTokenRepository"]
