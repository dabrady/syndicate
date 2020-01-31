from syndicate.silos import dev
import requests_mock
import re

def test_fetch_request_all_posts(requests_mock):
    fake_results = []
    requests_mock.get("https://dev.to/api/articles/me/all", json=fake_results)
    results = dev._fetch('fake_api_key')
    assert results == fake_results

def test_fetch_request_specific_post(requests_mock):
    fake_post_id = 13
    requests_mock.get("https://dev.to/api/articles/me/all", json=[{'id':fake_post_id}])
    results = dev._fetch('fake_api_key', fake_post_id)
    assert results['id'] == fake_post_id


def test_fetch_request_invalid_post(requests_mock):
    invalid_post_id = 13
    def fake_results(req, con):
        # Ugh, query string parsing. But they don't expose the params at the top-level, so....
        if int( re.search(r'page=(\d+)', req.query).group(1) ) == 1:
            return [{"id": invalid_post_id + 1}]
        else:
            return []
    requests_mock.get("https://dev.to/api/articles/me/all", json=fake_results)
    results = dev._fetch('fake_api_key', invalid_post_id)
    assert results is None
