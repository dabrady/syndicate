#!/usr/bin/env python3
from datetime import datetime
import json
import os
import sys
import syndicate
from syndicate.utils import action_log, action_setoutput, job_getoutput, job_addoutput, get_posts, fronted, mark_syndicated_posts

action_inputs = {
    'silos': os.getenv('INPUT_SILOS').splitlines(),
    'mark_as_syndicated': json.loads(os.getenv('INPUT_MARK_AS_SYNDICATED'))
}

posts = get_posts()
if not posts:
    action_log("No posts added or updated, nothing to do.")
    action_setoutput("time", datetime.now())
    sys.exit()

# Do the thing.
# Result set format:
# {
#     '<silo>': {
#         'added': {
#             'path/to/new_post': <silo id>,
#             ...
#         },
#         'modified': {
#             'path/to/updated_post': <silo id>,
#             ...
#         }
#     },
#     ...
# }
syndicated_posts = syndicate.elsewhere(posts, action_inputs['silos']) or {}
action_setoutput('syndicated_posts', syndicated_posts)
# Merge output with output of any previous runs
job_addoutput(syndicated_posts)

if action_inputs['mark_as_syndicated']:
    action_log("Marking newly syndicated posts...")
    ## NOTE
    # If silos were provided, commit only the results of this step. In the case
    # where no silos were provided, commit all job results so far.
    #
    # This allows us to bundle syndications into as few or many commits as we
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

    if not indexed_paths_by_silo:
        action_log("Nothing new to mark.")
        sys.exit()

    # {
    #     'path/to/post': {
    #         '<silo A>': 42,
    #         '<silo B>': 'abc123',
    #         ...
    #     },
    #     ...
    # }
    silo_ids_by_path = {}
    for (silo, indexed_paths) in indexed_paths_by_silo.items():
        for (path, sid) in indexed_paths.items():
            silo_ids_by_path.setdefault(path, {})
            silo_ids_by_path[path][silo] = sid

    mark_syndicated_posts(
        silo_ids_by_path,
        {post.path:fronted(post) for post in posts}
    )

action_setoutput("time", datetime.now())
