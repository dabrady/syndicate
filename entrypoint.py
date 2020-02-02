#!/usr/bin/env python3
import json
import os
import sys

# NOTE This is where our action module lives in the container.
# TODO Is there a way to manipulate the path from Dockerfile?
ACTION_SOURCE='/action'
sys.path.insert(0, os.path.abspath(ACTION_SOURCE))

import syndicate
from syndicate.utils import action_log, action_output, job_output, mark_syndicated_posts

action_inputs = {
    'silos': os.getenv('INPUT_SILOS').splitlines(),
    'mark_as_syndicated': json.loads(os.getenv('INPUT_MARK_AS_SYNDICATED'))
}

# Syndicate
results = syndicate.elsewhere(action_inputs['silos'])
action_output('syndicated_posts', results)

# Merge output with output of any previous runs
job_results_so_far = job_output(results)

# Mark as syndicated
if mark_as_syndicated:
    ## NOTE
    # If silos were provided, commit only the results of this step. In the case
    # where no silos were provided, commit all job results so far.
    #
    # This allows us to bundle sydications into as few or many commits as we
    # want in our workflows.
    ##
    if action_inputs['silos']:
        mark_syndicated_posts(results)
    else:
        mark_syndicated_posts(job_results_so_far)
