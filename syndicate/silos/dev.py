from syndicate.utils import action_log_group, action_log, action_warn, action_error, get_canonical_url, yaml_sequence, commit_silo_id
import frontmatter
import requests

@action_log_group("dev")
def syndicate(posts, api_key):
    action_log("Hello? Yes, this is DEV.")
    action_log("You want to syndicate these posts:")
    action_log(posts)

    results = {
        'added': [],
        'modified': []
    }
    for post in posts['added']:
        post_id = _draft(post, api_key)
        if post_id:
            action_log("Drafted successfully!")
            results['added'].append(post_id)
        else:
            action_warn(f"Draft failure for '{post.name}'")

    for post in posts['modified']:
        post_id = _update(post, api_key)
        if post_id:
            action_log("Updated successfully!")
            results['modified'].append(post_id)
        else:
            action_warn(f"Update failure for '{post.name}'")

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

    payload = _payload_for(post)

    action_log("Drafting a post with this payload:")
    action_log(payload)
    endpoint = "https://dev.to/api/articles"
    headers = {'api-key': api_key}
    response = requests.post(endpoint, headers=headers, json=payload)

    if response.status_code != requests.codes.created:
        action_error("Failed to create draft!")
        action_error(response.json())
        return None
    else:
        results = response.json()
        post_id = results['id']
        assert post_id
        ## TODO Move this up to `elsewhere`
        commit_silo_id(post, post_id, silo='dev')
        return post_id

def _publish():
    pass

def _update(post, api_key=None):
    assert api_key, "missing API key"
    assert post, "missing post"

    endpoint = f'https://dev.to/api/articles/{_id_for(post)}'
    headers = {'api-key': api_key}
    payload = {'article': { 'body_markdown': post.decoded.decode('utf-8') } }
    response = requests.put(endpoint, headers=headers, json=payload)
    if response.status_code != requests.codes.ok:
        action_error("Failed to update post!")
        action_error(response.json())
        return None
    else:
        results = response.json()
        post_id = results['id']
        assert post_id
        return post_id

def _id_for(post):
    assert post, "missing post"
    id = _front_of(post).get('dev_id')
    assert id, "missing post id for DEV"
    return id

def _front_of(post):
    assert post, "missing post"
    raw_contents = post.decoded.decode('utf-8')
    assert frontmatter.checks(raw_contents), "post is missing frontmatter"
    front, _ = frontmatter.parse(raw_contents)
    return front

def _payload_for(post):
    raw_contents = post.decoded.decode('utf-8')
    assert frontmatter.checks(raw_contents), "post is missing frontmatter"

    front, body = frontmatter.parse(raw_contents)
    assert front.get('title'), "article is missing a title"

    # TODO test if can be accomplished by just sending raw_contents as body
    return {
        'article': {
            'title': front['title'],
            'published': False,
            'tags': yaml_sequence(front.get('tags', [])),
            'series': front.get('series', None),
            'canonical_url': get_canonical_url(post),
            'body_markdown': body
        }
    }
