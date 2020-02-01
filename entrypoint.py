#!/usr/bin/env python3
import json
import os
import sys

# NOTE This is where our action module lives in the container.
# TODO Is there a way to manipulate the path from Dockerfile?
ACTION_SOURCE='/action'
sys.path.insert(0, os.path.abspath(ACTION_SOURCE))

import syndicate
from syndicate.utils import action_output, action_setenv

action_inputs = {
    'silos': os.getenv('INPUT_SILOS').splitlines()
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
