import frontmatter
import functools
import github3
import json
import os
import requests

### Github Action utilities ###
def action_log(msg):
    print(msg)

def action_debug(msg):
    print(f"::debug::{msg}")

def action_warn(msg):
    print(f"::warning::{msg}")

def action_error(msg):
    print(f"::error::{msg}")

def action_log_group(title):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            print(f"::group::{title}")
            result = func(*args, **kwargs)
            print("::endgroup::")
            return result
        return _wrapper
    return _decorator

def action_setenv(key, value):
    print(f"::set-env name={key}::{value}")

def action_setoutput(key, value):
    print(f"::set-output name={key}::{value}")

def job_setoutput(results):
    # Compile results for future steps
    syndicated_posts = results
    if 'SYNDICATE_POSTS' in os.environ:
        syndicated_posts = job_getoutput()
        syndicated_posts.update(results)
    action_setenv('SYNDICATE_POSTS', json.dumps(syndicated_posts))

def job_getoutput():
    return json.loads(os.getenv('SYNDICATE_POSTS', '{}'))

# Memoize authentication
@functools.lru_cache(maxsize=1)
def repo():
    assert os.getenv("GITHUB_TOKEN"), "GITHUB_TOKEN not available"
    assert os.getenv("GITHUB_REPOSITORY"), "GITHUB_REPOSITORY not available"

    gh = github3.login(token=os.getenv("GITHUB_TOKEN"))
    return gh.repository(*os.getenv("GITHUB_REPOSITORY").split('/'))

## NOTE
## This action may generate a new commit, so we need to be sure we're always
## using the proper SHA.
def target_sha():
    assert os.getenv("GITHUB_SHA"), "GITHUB_SHA not available"
    return os.getenv('SYNDICATE_SHA', os.getenv("GITHUB_SHA"))

def get_commit_payload():
    return repo().commit(target_sha()).files

def file_contents(filename):
    return repo().file_contents(filename, target_sha())

def get_posts(post_dir=os.getenv('SYNDICATE_POST_DIR', 'posts')):
    files = get_commit_payload()
    assert files, "target commit was empty"

    posts = [file for file in files if file['filename'].startswith(post_dir)]
    if not posts:
        return None
    else:
        # Don't care about the Git status: it might not be in sync with the silo
        return [file_contents(post['filename']) for post in posts]

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

def fronted(post):
    assert post, "missing post"
    if type(post) == frontmatter.Post:
        return post
    raw_contents = post.decoded.decode('utf-8')
    return frontmatter.loads(raw_contents)

def syndicate_key_for(silo):
    return f'{silo.lower()}_syndicate_id'

def syndicate_id_for(post, silo):
    assert post, "missing post"
    assert silo, "missing silo"
    return fronted(post).get(syndicate_key_for(silo))

def mark_syndicated_posts(siloed_ids_by_path, fronted_posts_by_path):
    updated_fronted_posts_by_path = {}
    for (path, siloed_ids) in siloed_ids_by_path.items():
        fronted_post = fronted_posts_by_path[path]
        syndicate_ids = {
            syndicate_key_for(silo):sid
            for (silo, sid) in siloed_ids.items()
            if not syndicate_id_for(fronted_post, silo) # ignore already marked posts
        }
        # Create new fronted post with old frontmatter merged with syndicate IDs.
        updated_post = frontmatter.Post(**dict(fronted_post.to_dict(), **syndicate_ids))

        # Only update if anything changed.
        if updated_post.keys() != fronted_post.keys():
            updated_fronted_posts_by_path[path] = updated_post
    commit_post_changes(updated_fronted_posts_by_path)

## NOTE
# Following the recipe outlined here for creating a commit consisting of
# multiple file updates:
#     https://developer.github.com/v3/git/
#
# 1. Get the current commit object
# 2. Retrieve the tree it points to
# 3. Retrieve the content of the blob object that tree has for that
#    particular file path
# 4. Change the content somehow and post a new blob object with that new
#    content, getting a blob SHA back
# 5. Post a new tree object with that file path pointer replaced with your
#    new blob SHA getting a tree SHA back
# 6. Create a new commit object with the current commit SHA as the parent
#    and the new tree SHA, getting a commit SHA back
# 7. Update the reference of your branch to point to the new commit SHA
##
def commit_post_changes(fronted_posts_by_path):
    if not fronted_posts_by_path:
        return None
    assert os.getenv("GITHUB_TOKEN"), "GITHUB_TOKEN not available"
    assert os.getenv("GITHUB_REPOSITORY"), "GITHUB_REPOSITORY not available"
    assert os.getenv("GITHUB_REF"), "GITHUB_REF not available"

    # Create new blobs in the repo's Git database containing the updated contents of our posts.
    new_blobs_by_path = {
        path:repo().create_blob(frontmatter.dumps(fronted_post), 'utf-8')
        for (path, fronted_post) in fronted_posts_by_path.items()
    }
    parent_sha = target_sha()
    # Create a new tree with our updated blobs.
    new_tree = repo().create_tree(
        [
            {
                'path': path,
                'mode': '100644', # 'file', @see https://developer.github.com/v3/git/trees/#tree-object
                'type': 'blob',
                'sha':  blob_sha
            }
            for (path, blob_sha) in new_blobs_by_path.items()
        ],
        base_tree=parent_sha
    )

    # Update the parent tree with our new subtree.
    # NOTE The github3 package I'm using apparently doesn't support updating refs -_-
    # Hand-rolling my own using the Github API directly.
    # @see https://developer.github.com/v3/
    new_commit = repo().create_commit(
        f'(syndicate): adding syndicate IDs to post frontmatter',
        new_tree.sha,
        [parent_sha]
    )
    response = requests.put(
        f'https://api.github.com/repos/{os.getenv("GITHUB_REPOSITORY")}/git/{os.getenv("GITHUB_REF")}',
        headers={
            'Authorization': f"token {os.getenv('GITHUB_TOKEN')}",
            'Accept': 'application/vnd.github.v3+json'
        },
        json={'sha': new_commit.sha}
    )
    if response.status_code == requests.codes.ok:
        ## NOTE Need to update the reference SHA for future workflow steps.
        action_setenv('SYNDICATE_SHA', new_commit.sha)
        return response.json()
    else:
        action_error(f"Failed to mark syndicated posts: {response.json()}")
        return None
