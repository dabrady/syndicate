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
    'mark_as_syndicated': json.loads(os.getenv('INPUT_MARK_AS_SYNDICATED'))
}

# Syndicate
action_output('syndicated_posts', syndicate.elsewhere(**action_inputs))
