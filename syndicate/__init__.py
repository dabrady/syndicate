from syndicate.utils import action_log, action_warn

import functools
import importlib.util
import os
import sys

def elsewhere(posts, silos):
    """
    Syndicates the given posts to the given silos and returns a dictionary of
    the results keyed by the silo that generated them.

    If a silo has no defined adapter, it is ignored.
    If a silo has no defined API key, it is ignored.

    Result dictionary is formatted like so:

        {
            <silo>: {
              'added': {
                 <path/to/post>: <silo id>,
                 ...
              },
              'modified': {
                 <path/to/post>: <silo id>,
                 ...
              }
            },
            ...
        }

    Since not all silos may be in sync, the 'added' posts of one silo may be
    merely 'modified' by another, and vice versa.

    Where possible, silo adapters should only create posts in a 'draft' or
    unpublished status, to allow time for review and any platform-specific
    changes to be made by the author.
    """
    if not posts:
        action_log("No posts to syndicate, nothing to do.")
        return None
    if not silos:
        action_log('No silos specified, nothing to do.')
        return None

    silos = list(set(silos))  # de-dupe the given list of silos
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
    """Locates the given silo adapter and returns its Python module name if found."""
    assert silo, 'missing silo'
    return getattr(importlib.util.find_spec(f'syndicate.silos.{silo.lower()}'), 'name', None)

def _syndicate(silo_spec, api_key, posts):
    """Loads and invokes the entrypoint of the given silo adaptor, returning the results."""
    assert silo_spec, 'missing silo spec'
    assert api_key, 'missing API key'
    return importlib.import_module(silo_spec).syndicate(posts, api_key)

def _get_api_key(silo):
    """Returns the API key for the given silo, as defined in the environment."""
    assert silo, 'missing silo'
    return os.getenv(_API_KEY(silo))
