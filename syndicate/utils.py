import frontmatter
import functools
import github3
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

def action_setenv(key, value):
    print(f"::set-env name={key}::{value}")

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
    assert files, "commit had no files in its payload"

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
    raw_contents = post.decoded.decode('utf-8')
    return frontmatter.loads(raw_contents)

def id_for(post, silo):
    assert post, "missing post"
    assert silo, "missing silo"
    return fronted(post).get(f'{silo}_syndicate_id') # TODO extract this template

# @DEPRECATED, DELETEME
def commit_silo_id(post, post_id, silo):
    assert post, "missing post info"
    assert post_id, "missing post ID"
    assert silo, "silo not specified"

    fronted_post = fronted(post)
    fronted_post[f'{silo}_syndicate_id'] = post_id

    action_log(f"Updating frontmatter with ID for {silo}")
    pushed_change = post.update(
        f'syndicate({silo}): adding post ID to frontmatter',
        frontmatter.dumps(fronted_post).encode('utf-8')
    )
    action_log(pushed_change)

def job_output(results):
    assert results, "no results to compile!"

    # Compile results for future steps.
    syndicated_posts = results
    if 'SYNDICATED_POSTS' in os.environ:
        syndicated_posts = json.loads(os.getenv('SYNDICATED_POSTS'))
        syndicated_posts.update(results)
    action_setenv('SYNDICATED_POSTS', json.dumps(syndicated_posts))
    return syndicated_posts

def mark_syndicated_posts(result_set):
    assert result_set, "no results to mark as syndicated!"
    action_log('marking!!!')

    for (silo, results) in result_set.items():
        if results['added']:
            action_log(f"TODO mark these for {silo}: {results['added']}")
        else:
            action_log(f"No new posts syndicated to {silo}")

def commit_post_changes(new_contents_by_post_path):
    assert os.getenv("GITHUB_TOKEN"), "GITHUB_TOKEN not available"
    assert os.getenv("GITHUB_REPOSITORY"), "GITHUB_REPOSITORY not available"
    assert os.getenv("GITHUB_SHA"), "GITHUB_SHA not available"
    assert os.getenv("GITHUB_REF"), "GITHUB_REF not available"
    parent_sha = os.getenv("GITHUB_SHA")

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

    # Create new blobs in the repo's Git database containing the updated contents of our posts.
    new_blobs_by_post = {path:repo().create_blob(new_contents, 'utf-8') for (path, new_contents) in new_contents_by_post_path.items()}
    # Create a new tree with our updated blobs for the post paths.
    new_tree = repo().create_tree(
        [
            {
                'path': path,
                'mode': '100644', # 'file', @see https://developer.github.com/v3/git/trees/#tree-object
                'type': 'blob',
                'sha':  blob_sha
            }
            for (path, blob_sha) in new_blobs_by_post.items()
        ],
        base_tree=parent_sha
    )
    # NOTE The github3 package I'm using apparently doesn't support updating refs -_-
    # Hand-rolling my own using the Github API directly.
    # @see https://developer.github.com/v3/
    headers ={
        'Authorization': f"token {os.getenv('GITHUB_TOKEN')}",
        'Accept': 'application/vnd.github.v3+json'
    }
    endpoint = f'https://api.github.com/repos/{os.getenv("GITHUB_REPOSITORY")}/git/{os.getenv("GITHUB_REF")}'
    data = {
        'sha': repo().create_commit(
            'test commit',
            new_tree.sha,
            [parent_sha]
        ).sha
    }
    response = requests.put(endpoint, headers=headers, json=data)
    if response.status_code == requests.codes.ok:
        return response.json()
    else:
        action_error(f"Failed to mark syndicated posts: {response.json()}")
        return None
