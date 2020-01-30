#!/usr/bin/env python3

import sys
from datetime import datetime

print(f"You want to publish to these places: {sys.argv[1:-1]}")
print(f"::set-output name=time::{datetime.now()}")
