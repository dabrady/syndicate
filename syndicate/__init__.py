from datetime import datetime
from syndicate.utils import action_log, action_warn, action_output, get_posts

import github3
import sys
import os
import importlib.util

def elsewhere(silos):
    commit = _get_commit_payload()
    assert commit, "could not fetch commit payload"
    posts = get_posts(commit)
    assert posts, "no posts to update"

    action_log(f"You want to publish to these places: {silos}")

    specs = {silo:_locate(silo) for silo in silos}
    recognized_silos = {silo:spec for (silo,spec) in specs.items() if spec}
    action_log(f"I know how to publish to these places: {list(recognized_silos.keys())}")

    available_keys = {silo:bool(_get_api_key(silo)) for silo in recognized_silos.keys()}

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
_API_KEY = lambda s: f"{s}_API_KEY"

def _locate(silo):
    return importlib.util.find_spec(f'syndicate.silos.{silo}')

def _syndicate(silo_spec, api_key, posts):
    if silo_spec and api_key:
        return importlib.import_module(silo_spec.name).do_the_thing(posts, api_key)
    else:
        return None

def _has_api_key(silo):
    return _API_KEY(silo) in os.environ

def _get_api_key(silo):
    return os.getenv(_API_KEY(silo))

def _get_commit_payload():
    assert os.getenv("GITHUB_REPOSITORY"), "GITHUB_REPOSITORY not available"
    assert os.getenv("GITHUB_TOKEN"), "GITHUB_TOKEN not available"
    assert os.getenv("GITHUB_SHA"), "GITHUB_SHA not available"

    gh = github3.login(token=os.getenv("GITHUB_TOKEN"))
    repo = gh.repository(*os.getenv("GITHUB_REPOSITORY").split('/'))
    commit = repo.commit(os.getenv("GITHUB_SHA"))
    return commit
