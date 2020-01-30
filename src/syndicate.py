#!/usr/bin/env python3

import sys
import os
from datetime import datetime

print(f"You want to publish to these places? {sys.argv[1:]}")

print("We have access to these environment variables:")
print(os.environ)

print(f"::set-output name=time::{datetime.now()}")
