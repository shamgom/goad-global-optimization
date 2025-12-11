def test_import_package():
    """Smoke test: package imports and exposes a version string."""
    import importlib
    goad = importlib.import_module('goad_v1')
    assert hasattr(goad, '__version__')
