from syndicate.utils import action_log_group, action_log, action_error, fronted, silo_id_for
import requests
import pprint

SILO_NAME = 'Medium'
@action_log_group(SILO_NAME)
def syndicate(posts, api_key):
    """
    Syndicates the given posts to https://medium.com.

    By default, articles are created in a "draft"/unpublished state, but this
    can be overridden by individual posts by specifying `published: true` in
    their frontmatter, if you prefer a "just do it" approach.

    The required API key is a "self-issued access token" and must be explicitly
    requested from Medium by emailing a request to yourfriends@medium.com. See
    their docs for more details:

       https://github.com/Medium/medium-api-docs#22-self-issued-access-tokens

    NOTE: The Medium API only allows creation at this time: it does not support
    updates, so unfortunately this adapter cannot synchronize changes to content
    that has already been syndicated to Medium.
    """
    if not posts:
        raise ValueError("missing posts")
    if not api_key:
        raise ValueError("missing API key")

    action_log(f"Hello? Yes, this is {SILO_NAME}.")
    results = {
        'added': {post.path:_create(post, api_key) for post in posts if not silo_id_for(post, SILO_NAME)},
        # NOTE The Medium API only allows creation, so we can't update anything.
        'modified': {}
    }
    action_log("The results are in:")
    action_log(pprint.pformat(results))
    return results

### privates ###

def _create(post, api_key):
    """
    Creates a new article for the given post on Medium and returns the silo ID
    and URL of the newly created post.

    This tries to create an **unpublished** draft. However, the 'published'
    status can be overridden in the frontmatter of the post itself for a
    "just do it" approach.

    @see https://github.com/Medium/medium-api-docs#33-posts
    """
    if not post:
        raise ValueError("missing post")

    payload = _get_payload(post)
    endpoint = f"https://api.medium.com/v1/users/{_get_user_id(api_key)}/posts"
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.post(endpoint, headers, json=payload)
    if response.status_code != requests.codes.created:
        action_error(f"Failed to create draft for '{post.name}': {response.json()}")
        return None
    else:
        results = response.json()
        return (results['id'], results['url'])

def _get_payload(post):
    """
    Returns a payload for creating the given post on Medium.

    @see https://github.com/Medium/medium-api-docs#33-posts
    """
    fronted_post = fronted(post)
    if not fronted_post.get('title'):
        raise ValueError("article is missing a title")

    published = fronted_post.get('published')
    return {
        "title": fronted_post.get('title'),
        "publishStatus": 'public' if published else 'draft',
        "canonicalUrl": fronted_post.get('canonical_url'),
        # NOTE From the docs:
        # > Only the first three will be used. Tags longer than 25 characters will be ignored.
        "tags": fronted_post.get('tags'),
        "content": fronted_post.content,
        "contentFormat": 'markdown'
    }

def _get_user_id(api_key):
    """Returns the ID of the authenticated user."""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.get("https://api.medium.com/v1/me", headers)
    if response.status_code != requests.codes.ok:
        action_error(f"Failed to get user details: {response.json()}")
        return None
    else:
        results = response.json()
        return results['id']
