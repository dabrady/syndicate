#!/usr/bin/env python3
from datetime import datetime
import json
import os
import sys

# NOTE This is where our action module lives in the container
# TODO Is there a way to manipulate the path from Dockerfile?
ACTION_SOURCE='/action'
sys.path.insert(0, os.path.abspath(ACTION_SOURCE))

import syndicate
from syndicate.utils import action_log, action_setoutput, job_getoutput, job_setoutput, get_posts, fronted, mark_syndicated_posts

action_inputs = {
    'silos': os.getenv('INPUT_SILOS').splitlines(),
    'mark_as_syndicated': json.loads(os.getenv('INPUT_MARK_AS_SYNDICATED'))
}

# Syndicate
posts = get_posts()
if not posts:
    action_log("No posts added or updated, nothing to see here.")
    action_setoutput("time", datetime.now())
    sys.exit()


# Result set format:
# {
#     '<silo>': {
#         'added': {
#             'post/path': <id>,
#             ...
#         },
#         'modified': {
#             'post/path': <id>,
#             ...
#         }
#     },
#     ...
# }
syndicated_posts = syndicate.elsewhere(posts, action_inputs['silos']) or {}
action_setoutput("time", datetime.now())
action_setoutput('syndicated_posts', syndicated_posts)

# Merge output with output of any previous runs
job_setoutput(syndicated_posts)

if action_inputs['mark_as_syndicated']:
    ## NOTE
    # If silos were provided, commit only the results of this step. In the case
    # where no silos were provided, commit all job results so far.
    #
    # This allows us to bundle sydications into as few or many commits as we
    # want in our workflows.
    ##
    if not action_inputs['silos']:
       syndicated_posts = job_getoutput()

    # Just focus on the added ones.
    indexed_paths_by_silo = {
        silo: results['added']
        for (silo, results) in syndicated_posts.items()
        if results
    }

    # {
    #     'path/to/post': {
    #         'dev': 42,
    #         'medium': 'abc123',
    #         ...
    #     },
    #     ...
    # }
    syndicate_ids_by_path = {}
    for (silo, indexed_paths) in indexed_paths_by_silo.items():
        for (path, id) in indexed_paths.items():
            syndicate_ids_by_path.setdefault(path, {})
            syndicate_ids_by_path[path][silo] = id

    mark_syndicated_posts(
        syndicate_ids_by_path,
        {post.path:fronted(post) for post in posts}
    )
