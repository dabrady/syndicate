#!/usr/bin/env python3
import json
import os
import sys

# NOTE This is where our action module lives in the container.
# TODO Is there a way to manipulate the path from Dockerfile?
ACTION_SOURCE='/action'
sys.path.insert(0, os.path.abspath(ACTION_SOURCE))

import syndicate
from syndicate.utils import action_log, action_output, action_setenv, mark_as_syndicated

action_inputs = {
    'silos': os.getenv('INPUT_SILOS').splitlines(),
    'mark_as_syndicated': json.loads(os.getenv('INPUT_MARK_AS_SYNDICATED'))
}

# Syndicate
results = syndicate.elsewhere(action_inputs['silos'])
action_output('syndicated_posts', results)

if results:
    # Compile results for future steps.
    previous_results = os.getenv('SYNDICATED_POSTS')
    if previous_results:
        syndicated_posts = json.loads(previous_results)
        syndicated_posts.update(results)
    else:
        syndicated_posts = results
        action_setenv('SYNDICATED_POSTS', json.dumps(syndicated_posts))

## TODO commit up here using 'SYNDICATED_POSTS' or results
if action_inputs['mark_as_syndicated']:
    # NOTE In the special case where no silos were provided, commit all compiled results
    if action_inputs['silos']:
        action_log("marking most recent results")
        mark_as_syndicated(results)
    else:
        action_log("marking all results")
        ## TODO fix null pointer JSON parsing
        mark_as_syndicated(json.loads(os.getenv('SYNDICATED_POSTS')))
else:
    action_log("You opted not to update your repo with the syndicate IDs of newly added posts")
