from syndicate.utils import action_log_group, action_log, get_canonical_url
import frontmatter as frontmatter
import requests

@action_log_group("dev")
def do_the_thing(posts, api_key):
    action_log("Hello? Yes, this is DEV.")
    action_log("You want to syndicate these posts:")
    action_log(posts)

    return True

### privates ###

## This is a simple semantic wrapper around the DEV API, currently in beta.

def _fetch(api_key=None, post_id=None):
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

    raw_contents = post.decoded.decode('utf-8')
    front, _ = frontmatter.parse(raw_contents)
    assert front.get('title'), "can't draft an article without a title"

    payload = {
        'article': {
            'title': front['title'],
            'published': False,
            'tags': front.get('tags', []),
            'series': front.get('series', None),
            'canonical_url': get_canonical_url(post.path),
            'body_markdown': raw_contents
        }
    }

    action_log("Drafting a post with this payload:")
    action_log(payload)
    # endpoint = "https://dev.to/api/articles"

def _publish():
    pass

def _update():
    pass
