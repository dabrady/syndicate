from syndicate.utils import silo_id_for
from syndicate.silos import dev
from .mocks import MockPost
import pytest
import requests
import requests_mock

def test_create_error_when_api_key_missing():
    with pytest.raises(AssertionError):
        dev._create(MockPost())

def test_create_error_when_post_missing():
    with pytest.raises(AssertionError):
        dev._create(None)

def test_create_returns_nothing_when_request_fails(requests_mock, monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'herp/derp')
    requests_mock.post(
        "https://dev.to/api/articles",
        status_code=requests.codes.unprocessable_entity,
        json={"error": "you made a unintelligble request"})
    assert not dev._create(MockPost(), api_key='fake_api_key')

def test_create_returns_something_on_success(requests_mock, monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'herp/derp')
    requests_mock.post(
        "https://dev.to/api/articles",
        status_code=requests.codes.created,
        json={ 'type_of': 'article', 'id': 42, 'url': 'https://fake.url/for-this-post' })
    assert dev._create(MockPost(), api_key='fake_api_key')

def test_update_error_when_api_key_missing():
    with pytest.raises(AssertionError):
        dev._update(MockPost())

def test_update_error_when_post_missing():
    with pytest.raises(AssertionError):
        dev._update(None)

def test_update_returns_nothing_when_request_fails(requests_mock, monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'herp/derp')
    mock = MockPost()
    requests_mock.put(
        f"https://dev.to/api/articles/{silo_id_for(mock, dev.SILO_NAME)}",
        status_code=requests.codes.unprocessable_entity,
        json={"error": "you made an unintelligble request"})
    assert not dev._update(mock, api_key='fake_api_key')

def test_update_returns_something_on_success(requests_mock, monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'herp/derp')
    mock = MockPost()
    mock_id= silo_id_for(mock, dev.SILO_NAME)
    requests_mock.put(
        f"https://dev.to/api/articles/{mock_id}",
        status_code=requests.codes.ok,
        json={'type_of': 'article', 'id': mock_id, 'url': 'https://fake.url/for-this-post'})
    assert dev._update(mock, api_key='fake_api_key')
