from syndicate.utils import action_log_group, action_warn, syndicate_id_for

SILO_NAME = 'Medium'
@action_log_group(SILO_NAME)
def syndicate(posts, api_key):
    action_warn("not yet implemented")
    action_warn("using mock data for testing")

    return {
        'added': {post.path:4 for post in posts if not syndicate_id_for(post, SILO_NAME)}
    }
