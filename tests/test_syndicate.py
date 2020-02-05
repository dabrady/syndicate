import importlib.util
import pytest
import syndicate

@pytest.fixture(autouse=True)
def clear_silo_cache():
    """Needed to ensure our monkeypatching doesn't get cached between tests."""
    yield
    syndicate._locate.cache_clear()

def test_elsewhere_returns_none_when_given_no_posts():
    assert not syndicate.elsewhere([], ['Fake_Silo'])

def test_elsewhere_returns_none_when_given_no_silos():
    assert not syndicate.elsewhere(['a post'], [])

def test_elsewhere_returns_none_when_no_api_keys_exist_for_given_silos(monkeypatch):
    fake_silo = 'Fake_Silo'
    # Ensure we cannot use the fake silo adapter.
    monkeypatch.delenv(syndicate._API_KEY(fake_silo), raising=False)
    assert not syndicate.elsewhere(['a post'], [fake_silo])

def test_elsewhere_returns_none_when_no_adapter_exists_for_given_silos(monkeypatch):
    fake_silo = 'Fake_Silo'
    # Ensure we cannot find the fake silo adapter.
    monkeypatch.setattr(importlib.util, 'find_spec', lambda s: None)
    # Ensure we can use the fake silo adapter.
    monkeypatch.setenv(syndicate._API_KEY(fake_silo), 'fake API key')
    assert not syndicate.elsewhere(['a post'], [fake_silo])

def test_elsewhere_returns_syndication_results_for_recognized_silos_when_given_api_keys(monkeypatch):
    class MockSpec:
        def __init__(self):
            self.name = 'mock_spec'
    class MockSilo:
        def syndicate(posts, api_key):
            return 'mock results'
    fake_silo = 'Fake_Silo'
    # Ensure we can find the fake silo adapter.
    monkeypatch.setattr(importlib.util, 'find_spec', lambda s: MockSpec())
    # Ensure we can load the fake silo adapter.
    monkeypatch.setattr(importlib, 'import_module', lambda s: MockSilo)
    # Ensure we can use the fake silo adapter.
    monkeypatch.setenv(syndicate._API_KEY(fake_silo), 'fake API key')
    assert syndicate.elsewhere(['a post'], [fake_silo])
