from syndicate.utils import action_log_group, action_log, action_warn, action_error, get_canonical_url, yaml_sequence, fronted, syndicate_id_for
import requests
import pprint

SILO_NAME = 'DEV'
@action_log_group(SILO_NAME)
def syndicate(posts, api_key):
    action_log(f"Hello? Yes, this is {SILO_NAME}.")
    results = {
        'added': {post.path:_draft(post, api_key) for post in posts if not syndicate_id_for(post, SILO_NAME)},
        'modified': {post.path:_update(post, api_key) for post in posts if syndicate_id_for(post, SILO_NAME)}
    }
    action_log("The results are in:")
    action_log(pprint.pformat(results))
    return results

### privates ###

## This is a simple semantic wrapper around the DEV API, currently in beta.

# NOTE Not currently used
def _fetch(post_id=None, api_key=None):
    assert api_key, "missing API key"

    headers = {'api-key': api_key}
    if post_id:
        # Fetch data for given post ID
        ## NOTE Currently, there's no way to fetch data for a specific post.
        ## The workaround I'm using here is the best we can do: fetch and search.
        endpoint = "https://dev.to/api/articles/me/all"
        post_data = None
        page = 0
        while not post_data:
            page += 1
            response = requests.get(endpoint, params={ 'page': page }, headers=headers)
            response.raise_for_status() # raise error if bad request
            posts = response.json()
            if posts:
                post_data = next((data for data in posts if data['id'] == post_id), None)
            else:
                break; # No more posts to fetch
        return post_data
    else:
        # Fetch all post data
        endpoint = "https://dev.to/api/articles/me/all"
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status() # raise error if bad request
        return response.json()

def _draft(post, api_key=None):
    assert api_key, "missing API key"
    assert post, "missing post"
    assert fronted(post).get('title'), "article is missing a title"

    payload = {
        'article': {
            # NOTE This can be overridden by explicitly setting 'published' in
            # the frontmatter.
            'published': False,
            'body_markdown': post.decoded.decode('utf-8')
        }
    }
    endpoint = "https://dev.to/api/articles"
    headers = {'api-key': api_key}
    response = requests.post(endpoint, headers=headers, json=payload)

    if response.status_code != requests.codes.created:
        action_error(f"Failed to create draft for '{post.name}': {response.json()}")
        return None
    else:
        results = response.json()
        return results['id']

def _update(post, api_key=None):
    assert api_key, "missing API key"
    assert post, "missing post"

    endpoint = f'https://dev.to/api/articles/{syndicate_id_for(post, SILO_NAME)}'
    headers = {'api-key': api_key}
    payload = {'article': { 'body_markdown': post.decoded.decode('utf-8') } }
    response = requests.put(endpoint, headers=headers, json=payload)
    if response.status_code != requests.codes.ok:
        action_error(f"Failed to update post '{post.name}': {response.json()}")
        return None
    else:
        results = response.json()
        return results['id']
