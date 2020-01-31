import github3
import os

### Github Action utilities ###
def action_log(msg):
    print(msg)

def action_debug(msg):
    print(f"::debug::{msg}")

def action_warn(msg):
    print(f"::warning::{msg}")

def action_error(msg):
    print(f"::error::{msg}")

def action_output(key, value):
    print(f"::set-output name={key}::{value}")

def action_log_group(title):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            print(f"::group::{title}")
            result = func(*args, **kwargs)
            print("::endgroup::")
            return result
        return _wrapper
    return _decorator

def get_commit_payload():
    assert os.getenv("GITHUB_REPOSITORY"), "GITHUB_REPOSITORY not available"
    assert os.getenv("GITHUB_TOKEN"), "GITHUB_TOKEN not available"
    assert os.getenv("GITHUB_SHA"), "GITHUB_SHA not available"

    gh = github3.login(token=os.getenv("GITHUB_TOKEN"))
    repo = gh.repository(*os.getenv("GITHUB_REPOSITORY").split('/'))
    commit = repo.commit(os.getenv("GITHUB_SHA"))
    return commit

def get_posts(post_dir='pages/posts'):
    commit = get_commit_payload()
    assert commit, "could not fetch commit payload"

    files = [file for file in commit.files if file['filename'].startswith(post_dir)]

    # TODO
    posts = []

    return {
        'added': [post['filename'] for post in posts if post['status'] == 'added'],
        'modified': [post['filename'] for post in posts if post['status'] == 'modified']
    }
