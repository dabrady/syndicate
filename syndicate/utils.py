import frontmatter
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
def repo():
    assert os.getenv("GITHUB_TOKEN"), "GITHUB_TOKEN not available"
    assert os.getenv("GITHUB_REPOSITORY"), "GITHUB_REPOSITORY not available"

    gh = github3.login(token=os.getenv("GITHUB_TOKEN"))
    return gh.repository(*os.getenv("GITHUB_REPOSITORY").split('/'))

def get_commit_payload():
    assert os.getenv("GITHUB_SHA"), "GITHUB_SHA not available"
    return repo().commit(os.getenv("GITHUB_SHA")).files

def file_contents(filename):
    assert os.getenv("GITHUB_SHA"), "GITHUB_SHA not available"
    return repo().file_contents(filename, os.getenv("GITHUB_SHA"))

def get_posts(post_dir=os.getenv('SYNDICATE_POST_DIR', 'posts')):
    files = get_commit_payload()
    assert files, "could not fetch commit payload"

    posts = [file for file in files if file['filename'].startswith(post_dir)]
    post_contents = {post['status']:file_contents(post['filename']) for post in posts}

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

def commit_silo_id(post, post_id, silo=None):
    assert post, "missing post info"
    assert post_id, "missing post ID"
    assert silo, "silo not specified"

    fronted_post = frontmatter.loads(post.decoded.decode('utf-8'))
    fronted_post[f'{silo}_id'] = post_id

    action_log(f"Updating frontmatter with ID for {silo}")
    pushed_change = post.update(
        f'syndicate({silo}): adding post ID to frontmatter',
        frontmatter.dumps(fronted_post).encode('utf-8')
    )
    action_log(pushed_change)
