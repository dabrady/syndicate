import sys
import os
from datetime import datetime
import importlib.util

def elsewhere(silos):
    print(f"You want to publish to these places: {silos}")

    print("Do I know how?")
    recognized_silos = {silo:bool(_locate(silo)) for silo in silos}
    print(recognized_silos)

    print(f"Do we have the necessary API keys?")
    available_keys = {silo:(f"{silo}_API_KEY" in os.environ) for silo in silos }
    print(available_keys)

    print(f"::set-output name=time::{datetime.now()}")

### privates ###
def _locate(silo):
    return importlib.util.find_spec(f'syndicate.silos.{silo}')
