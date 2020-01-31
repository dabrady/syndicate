import sys
import os
from datetime import datetime
import importlib.util

def elsewhere(silos):
    print(f"You want to publish to these places: {silos}")

    print("Do I know how?")
    specs = {silo:_locate(silo) for silo in silos}
    recognized_silos = {silo:bool(spec) for (silo,spec) in specs.items()}
    print(recognized_silos)

    print(f"Do we have the necessary API keys?")
    available_keys = {silo:bool(_get_api_key(silo)) for (silo, known) in recognized_silos.items() if known }
    print(available_keys)

    if any(available_keys.values()):
        print("Let's do this thing.")
        results = {silo:_load(spec, _get_api_key(silo)) for (silo,spec) in specs.items() if _has_api_key(silo)}
        print(results)
    else:
        print("Sorry, can't do anything with that.")

    print(f"::set-output name=time::{datetime.now()}")

### privates ###
_API_KEY = lambda s: f"{s}_API_KEY"

def _locate(silo):
    return importlib.util.find_spec(f'syndicate.silos.{silo}')

def _load(silo_spec, api_key):
    if silo_spec and api_key:
        return importlib.import_module(silo_spec.name).do_the_thing(api_key)
    else:
        return None

def _has_api_key(silo):
    return _API_KEY(silo) in os.environ

def _get_api_key(silo):
    return os.getenv(_API_KEY(silo))
