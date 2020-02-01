#!/usr/bin/env python3
import json
import os
import sys

# NOTE This is where our action module lives in the container.
# TODO Is there a way to manipulate the path from Dockerfile?
ACTION_SOURCE='/action'
sys.path.insert(0, os.path.abspath(ACTION_SOURCE))

import syndicate
from syndicate.utils import action_log, action_output, action_setenv

action_inputs = {
    'silos': os.getenv('INPUT_SILOS').splitlines(),
    'commit_on_create': json.loads(os.getenv('INPUT_COMMIT_ON_CREATE'))
}

# Syndicate
results = syndicate.elsewhere(**action_inputs)
action_output('syndicated_posts', results)

## TODO commit up here using 'SYNDICATED_POSTS' or results
if action_inputs['commit_on_create']:
    action_log("Sorry, commit not yet supported")
else:
    action_log("You opted not to update your repo with the syndicate IDs of newly added posts")

if results:
    # Compile results for future steps.
    previous_results = os.getenv('SYNDICATED_POSTS')
    if previous_results:
        syndicated_posts = json.loads(previous_results)
        syndicated_posts.update(results)
    else:
        syndicated_posts = results
        action_setenv('SYNDICATED_POSTS', json.dumps(syndicated_posts))
