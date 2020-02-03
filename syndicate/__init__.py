from syndicate.utils import action_log, action_warn

import functools
import importlib.util
import os
import sys

def elsewhere(posts, silos):
    if not silos:
        action_log('No silos specified, nothing to see here.')
        return None

    # De-dupe.
    silos = list(set(silos))
    action_log(f"You want to publish to these places: {silos}")

    specs = {silo:_locate(silo) for silo in silos if _locate(silo)}
    if list(specs.keys()) != silos:
        action_warn(f"I don't know how to publish to these places: { [silo for silo in silos if silo not in specs] }")

    api_keys = {silo:_get_api_key(silo) for silo in silos if _get_api_key(silo)}
    if list(api_keys.keys()) != silos:
        action_warn(f"I don't have API keys for these places: { [silo for silo in silos if silo not in api_keys] }")

    action_log("I'll do what I can.")
    results = {
        silo:_syndicate(spec, api_keys[silo], posts)
        for (silo, spec) in specs.items()
        if silo in api_keys
    }
    if results:
        return results
    else:
        action_warn("Sorry, can't do anything with that!")
        return None

### privates ###
_API_KEY = lambda s: f"{s.upper()}_API_KEY"

@functools.lru_cache(maxsize=10)
def _locate(silo):
    return getattr(importlib.util.find_spec(f'syndicate.silos.{silo.lower()}'), 'name', None)

def _syndicate(silo_spec, api_key, posts):
    if silo_spec and api_key:
        return importlib.import_module(silo_spec).syndicate(posts, api_key)
    else:
        return None

def _get_api_key(silo):
    return os.getenv(_API_KEY(silo))
