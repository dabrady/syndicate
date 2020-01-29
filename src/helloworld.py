#!/usr/bin/env python3

import sys
from datetime import datetime

print(f"Hello, {sys.argv[1]}!")
print(f"::set-output name=time::{datetime.now()}")
