import sys
import os
from datetime import datetime

def elsewhere(silos):
    print(f"You want to publish to these places? {silos}")
    print(f"Do we have the necessary API keys?")
    available_keys = {silo:(f"{silo}_API_KEY" in os.environ) for silo in silos }
    print(available_keys)
    print(f"::set-output name=time::{datetime.now()}")
