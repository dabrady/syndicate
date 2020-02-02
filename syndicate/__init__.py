from datetime import datetime
from syndicate.utils import action_log, action_warn, action_output, get_posts

import sys
import os
import importlib.util

def elsewhere(silos):
    if not silos:
        action_log('No silos specified, nothing to see here.')
        action_output("time", datetime.now())
        return None

    posts = get_posts()
    if not posts:
        action_log("No posts added or updated, nothing to see here.")
        action_output("time", datetime.now())
        return None

    action_log(f"You want to publish to these places: {silos}")

    specs = {silo:_locate(silo) for silo in silos}
    recognized_silos = {silo:spec for (silo,spec) in specs.items() if spec}
    available_keys = {silo:_has_api_key(silo) for silo in recognized_silos.keys()}

    if recognized_silos and any(available_keys.values()):
        action_log(f"I know how to publish to these places: {list(recognized_silos.keys())}")
        action_log("I'll do what I can.")
        if not all(available_keys.values()):
            action_log(f"But I don't have API keys for these places: {[silo for (silo, available) in available_keys.items() if not available]}")

        results = {
            silo:_syndicate(spec, _get_api_key(silo), posts)
            for (silo,spec) in specs.items()
            if _has_api_key(silo)
        }

        action_output("time", datetime.now())
        return results
    else:
        action_warn("Sorry, can't help you.")
        action_output("time", datetime.now())
        return None

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
