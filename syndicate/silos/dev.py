from syndicate.utils import action_log_group, action_log, action_warn, action_error, get_canonical_url, yaml_sequence, commit_silo_id
import frontmatter
import requests

@action_log_group("dev")
def syndicate(posts, api_key):
    action_log("Hello? Yes, this is DEV.")

    return {
        'added': [id for id in (_draft(post, api_key) for post in posts if not _id_for(post)) if id],
        'modified': [id for id in (_update(post, api_key) for post in posts if _id_for(post)) if id]
    }

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

    payload = _payload_for(post)

    endpoint = "https://dev.to/api/articles"
    headers = {'api-key': api_key}
    response = requests.post(endpoint, headers=headers, json=payload)

    if response.status_code != requests.codes.created:
        action_error(f"Failed to create draft for '{post.name}'")
        action_error(response.json())
        return None
    else:
        results = response.json()
        return results['id']

def _update(post, api_key=None):
    assert api_key, "missing API key"
    assert post, "missing post"

    endpoint = f'https://dev.to/api/articles/{_id_for(post)}'
    headers = {'api-key': api_key}
    payload = {'article': { 'body_markdown': post.decoded.decode('utf-8') } }
    response = requests.put(endpoint, headers=headers, json=payload)
    if response.status_code != requests.codes.ok:
        action_error(f"Failed to update post '{post.name}'")
        action_error(response.json())
        return None
    else:
        results = response.json()
        return results['id']

def _id_for(post):
    assert post, "missing post"
    return _fronted(post).get('dev_id')

def _fronted(post):
    assert post, "missing post"
    raw_contents = post.decoded.decode('utf-8')
    return frontmatter.loads(raw_contents)

def _payload_for(post):
    assert post, "missing post"

    fronted_post = _fronted(post)
    assert fronted_post.get('title'), "article is missing a title"

    # TODO test if can be accomplished by just sending raw contents as body_markdown
    return {
        'article': {
            'title': fronted_post['title'],
            'published': False,
            'tags': yaml_sequence(fronted_post.get('tags', [])),
            'series': fronted_post.get('series', None),
            'canonical_url': get_canonical_url(post),
            'body_markdown': fronted_post.content
        }
    }
