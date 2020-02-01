import functools
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

# Memoize authentication
@functools.lru_cache(maxsize=1)
def github():
    assert os.getenv("GITHUB_TOKEN"), "GITHUB_TOKEN not available"
    return github3.login(token=os.getenv("GITHUB_TOKEN"))

def get_commit_payload():
    assert os.getenv("GITHUB_REPOSITORY"), "GITHUB_REPOSITORY not available"
    assert os.getenv("GITHUB_SHA"), "GITHUB_SHA not available"

    repo = github().repository(*os.getenv("GITHUB_REPOSITORY").split('/'))
    commit = repo.commit(os.getenv("GITHUB_SHA"))
    return (repo, commit)

def get_posts(post_dir='pages/posts'):
    repo, commit = get_commit_payload()
    assert commit, "could not fetch commit payload"

    posts = [file for file in commit.files if file['filename'].startswith(post_dir)]
    post_contents = {post['status']:repo.file_contents(post['filename'], commit.sha) for post in posts}

    return {
        'added': [contents for (status, contents) in post_contents.items() if status == 'added'],
        'modified': [contents for (status, contents) in post_contents.items() if status == 'modified']
    }

def get_canonical_url(post):
    assert os.getenv("GITHUB_REPOSITORY"), "GITHUB_REPOSITORY not available"
    # return f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/{post.path}"
    return post.html_url

def yaml_sequence(sequence):
    JUST_GIVE_IT_BACK = lambda s: s
    cases = {
        # Support simple comma-separated YAML sequences
        type(''): lambda s: [item.strip() for item in sequence.split(',')],
        # If the YAML sequence has already been processed into a list, just give it back
        type([]): JUST_GIVE_IT_BACK
    }
    # If I know how to handle it, handle it; otherwise, just give it back
    return cases.get(type(sequence), JUST_GIVE_IT_BACK)(sequence)
