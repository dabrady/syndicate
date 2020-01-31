#!/usr/bin/env python3
import os
import sys

ACTION_SOURCE='/action'
sys.path.insert(0, os.path.abspath(ACTION_SOURCE))

import syndicate
syndicate.elsewhere(sys.argv[1].splitlines())
