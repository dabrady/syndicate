from syndicate.utils import action_log_group, action_log, action_error, fronted, silo_id_for
import requests
import pprint

SILO_NAME = 'DEV'
@action_log_group(SILO_NAME)
def syndicate(posts, api_key):
    """
    Syndicates the given posts to https://dev.to, updating the ones that
    already exist there and creating articles for the ones that don't.

    By default, articles are created in a "draft"/unpublished state, but this
    can be overridden by individual posts by specifying `published: true` in
    their frontmatter, if you prefer a "just do it" approach.

    This uses the DEV API, which is currently in beta: https://docs.dev.to/api

    The required API key can be generated for your account by following the steps
    outlined here: https://docs.dev.to/api/#section/Authentication
    """

    action_log(f"Hello? Yes, this is {SILO_NAME}.")
    results = {
        'added': {post.path:_create(post, api_key) for post in posts if not silo_id_for(post, SILO_NAME)},
        'modified': {post.path:_update(post, api_key) for post in posts if silo_id_for(post, SILO_NAME)}
    }
    action_log("The results are in:")
    action_log(pprint.pformat(results))
    return results

### privates ###

def _create(post, api_key=None):
    """
    Creates a new article for the given post on DEV.to and returns the silo ID
    and URL of the newly created article.

    This tries to create an **unpublished** draft. However, the 'published'
    status can be overridden in the frontmatter of the post itself for a
    "just do it" approach.

    @see https://docs.dev.to/api/#operation/createArticle
    """
    if not api_key:
        raise ValueError("missing API key")
    if not post:
        raise ValueError("missing post")
    if not fronted(post).get('title'):
        raise ValueError("article is missing a title")

    payload = {
        'article': {
            # NOTE This can be overridden by explicitly setting 'published' in
            # the frontmatter.
            'published': False,
            'body_markdown': post.decoded_content.decode('utf-8')
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
        return (results['id'], results['url'])

def _update(post, api_key=None):
    """
    Updates an article corresponding to the given post on DEV.to and returns the
    silo ID and URL of the updated arcticle.

    If a corresponding article does not exist, this will fail.

    @see https://docs.dev.to/api/#operation/updateArticle
    """
    if not api_key:
        raise ValueError("missing API key")
    if not post:
        raise ValueError("missing post")

    endpoint = f'https://dev.to/api/articles/{silo_id_for(post, SILO_NAME)}'
    headers = {'api-key': api_key}
    payload = {'article': { 'body_markdown': post.decoded_content.decode('utf-8') } }
    response = requests.put(endpoint, headers=headers, json=payload)
    if response.status_code != requests.codes.ok:
        action_error(f"Failed to update post '{post.name}': {response.json()}")
        return None
    else:
        results = response.json()
        return (results['id'], results['url'])
