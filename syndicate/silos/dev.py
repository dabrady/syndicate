from syndicate.utils import action_log_group, action_log, get_canonical_url, yaml_sequence, commit_silo_id
import frontmatter as frontmatter
import requests

@action_log_group("dev")
def do_the_thing(posts, api_key):
    action_log("Hello? Yes, this is DEV.")
    action_log("You want to syndicate these posts:")
    action_log(posts)

    for post in posts['added']:
        results = _draft(post, api_key)
        action_log("Draft success!")
        action_log(results)

    return True

### privates ###

## This is a simple semantic wrapper around the DEV API, currently in beta.

def _fetch(post_id=None, api_key=None):
    assert api_key, "missing API key"

    headers = {
        'api-key': api_key
    }
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

    action_log("Drafting a post with this payload:")
    action_log(payload)
    endpoint = "https://dev.to/api/articles"
    headers = {
        'api-key': api_key
    }
    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()

    results = response.json()
    assert results['id']
    commit_silo_id(post, results['id'], silo='dev')
    return results

def _publish():
    pass

def _update():
    pass

def _payload_for(post):
    raw_contents = post.decoded.decode('utf-8')
    assert frontmatter.checks(raw_contents)

    front, body = frontmatter.parse(raw_contents)
    assert front.get('title'), "article is missing a title"

    return {
        'article': {
            'title': front['title'],
            'published': False,
            'tags': yaml_sequence(front.get('tags', None)),
            'series': front.get('series', None),
            'canonical_url': get_canonical_url(post),
            'body_markdown': body
        }
    }
