from datetime import datetime
from syndicate.utils import action_log, action_warn, action_output, get_posts

import sys
import os
import importlib.util

def elsewhere(silos):
    posts = get_posts()
    if not posts:
        action_log("No posts added or updated, nothing to see here.")
        action_output("time", datetime.now())
        return

    action_log(f"You want to publish to these places: {silos}")

    specs = {silo:_locate(silo) for silo in silos}
    recognized_silos = {silo:spec for (silo,spec) in specs.items() if spec}
    action_log(f"I know how to publish to these places: {list(recognized_silos.keys())}")

    available_keys = {silo:_has_api_key(silo) for silo in recognized_silos.keys()}

    if not all(available_keys.values()):
        action_log(f"But I don't have API keys for these places: {[silo for (silo, available) in available_keys.items() if not available]}")

    if any(available_keys.values()):
        action_log("I'll do what I can.")

        results = {silo:_syndicate(spec, _get_api_key(silo), posts) for (silo,spec) in specs.items() if _has_api_key(silo)}

        action_log(results)
    else:
        action_warn("Sorry, can't help you.")

    action_output("time", datetime.now())

### privates ###
_API_KEY = lambda s: f"{s.upper()}_API_KEY"

def _locate(silo):
    return importlib.util.find_spec(f'syndicate.silos.{silo.lower()}')

def _syndicate(silo_spec, api_key, posts):
    if silo_spec and api_key:
        return importlib.import_module(silo_spec.name).syndicate(posts, api_key)
    else:
        return None

def _has_api_key(silo):
    return _API_KEY(silo) in os.environ

def _get_api_key(silo):
    return os.getenv(_API_KEY(silo))
