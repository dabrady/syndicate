import frontmatter
import functools
from github import Github, InputGitTreeElement
import json
import os
import requests

def action_log(msg):
    """(SIDE-EFFECT) Prints `msg` to the Github workflow log."""
    print(msg)

def action_debug(msg):
    """(SIDE-EFFECT) Prints `msg` to the Github workflow debug log."""
    print(f"::debug::{msg}")

def action_warn(msg):
    """(SIDE-EFFECT) Prints `msg` to the Github workflow warning log."""
    print(f"::warning::{msg}")

def action_error(msg):
    """(SIDE-EFFECT) Prints `msg` to the Github workflow error log."""
    print(f"::error::{msg}")

def action_log_group(title):
    """
    Decorates a function such that all its generated log statements are grouped
    in the Github workflow log under `title`.
    """

    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            print(f"::group::{title}")
            result = func(*args, **kwargs)
            print("::endgroup::")
            return result
        return _wrapper
    return _decorator

def action_setenv(key, value):
    """
    (SIDE-EFFECT) Sets an environment variable of the running Github workflow job.
    """
    print(f"::set-env name={key}::{value}")

def action_setoutput(key, value):
    """(SIDE-EFFECT) Sets an output variable of the running Github workflow step."""
    print(f"::set-output name={key}::{value}")

def job_addoutput(results):
    """
    (SIDE-EFFECT) Persist `results` for future steps in the running Github
    workflow job.
    """
    syndicated_posts = job_getoutput()
    syndicated_posts.update(results)
    action_setenv('SYNDICATE_POSTS', json.dumps(syndicated_posts))

def job_getoutput():
    """Returns the persisted results of the running Github workflow job."""
    # Default to an empty dictionary if no results have yet been persisted.
    return json.loads(os.getenv('SYNDICATE_POSTS', '{}'))

# Memoize authentication and repo fetching.
@functools.lru_cache(maxsize=1)
def repo():
    """
    (MEMOIZED) Returns an authenticated reference to a repository object for the
    repository this Github action is running in.
    @see https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html#github.Repository.Repository
    """
    if not os.getenv("GITHUB_TOKEN"):
        raise ValueError("missing GITHUB_TOKEN")
    if not os.getenv("GITHUB_REPOSITORY"):
        raise ValueError("missing GITHUB_REPOSITORY")

    gh = Github(os.getenv("GITHUB_TOKEN"))
    return gh.get_repo(os.getenv("GITHUB_REPOSITORY"))

def parent_sha():
    """
    Returns the git SHA to use as parent for any commits generated by this
    Github workflow step.
    """
    if not os.getenv("GITHUB_SHA"):
        raise ValueError("missing GITHUB_SHA")
    return os.getenv('SYNDICATE_SHA', os.getenv("GITHUB_SHA"))

def get_trigger_payload():
    """
    Returns a list of lightweight File objects describing each of the modified
    files in the commit that triggered this Github workflow.
    @see https://pygithub.readthedocs.io/en/latest/github_objects/File.html#github.File.File
    """
    if not os.getenv("GITHUB_SHA"):
        raise ValueError("missing GITHUB_SHA")
    # NOTE
    # Explicitly using GITHUB_SHA to ensure we always have access to the changed
    # files even if other steps generate commits.
    return repo().get_commit(os.getenv("GITHUB_SHA")).files

def file_contents(filepath):
    """
    Returns a `ContentFile` object of the matching the given path in latest known
    commit to this repo.
    @see https://pygithub.readthedocs.io/en/latest/github_objects/ContentFile.html#github.ContentFile.ContentFile
    @see :func:`~syndicate.utils.parent_sha`
    """
    # NOTE
    # Using the latest known commit to ensure we capture any modifications made
    # to the post frontmatter by previous actions.
    return repo().get_contents(filepath, ref=parent_sha())

def get_posts(post_dir=os.getenv('SYNDICATE_POST_DIR', 'posts')):
    """
    Returns the latest known :func:`~syndicate.utils.file_contents` of the files
    added and modified in the commit that triggered this Github workflow.
    """
    files = get_trigger_payload()
    if not files:
        raise ValueError("target commit was empty")

    posts = [file for file in files if file.filename.startswith(post_dir)]
    return [
        file_contents(post.filename)
        for post in posts
        if post.status != 'deleted'  # ignore deleted files
    ]

def fronted(post):
    """
    Returns the :py:class:`frontmatter.Post` representation of the given
    :func:`~syndicate.utils.file_contents` object.

    If `post` is actually already a `frontmatter.Post`, this is a no-op.
    """
    if not post:
        raise ValueError("missing post")
    if isinstance(post, frontmatter.Post):
        return post
    raw_contents = post.decoded_content.decode('utf-8')
    return frontmatter.loads(raw_contents)

def silo_key_for(silo):
    """Returns a formatted string used to identify a silo ID in post frontmatter."""
    return f'{silo.lower()}_silo_id'

def silo_id_for(post, silo):
    """
    Retrieves the ID appropriate for `silo` from the frontmatter of the given
    `post`; returns None if no relevant ID exists.
    """
    if not post:
        raise ValueError("missing post")
    if not silo:
        raise ValueError("missing silo")
    return fronted(post).get(silo_key_for(silo))

def mark_syndicated_posts(silo_ids_by_path, fronted_posts_by_path):
    """
    Injects the given silo IDs for the given posts into their frontmatter
    and commits the updated posts back to this repo.

    If a silo ID already exists in a given post, that's fine: we assume IDs don't
    change, and so we don't try to change them.

    Returns a dictionary which is the response of the commit request.
    """
    if not silo_ids_by_path:
        raise ValueError("missing silo IDs")
    if not fronted_posts_by_path:
        raise ValueError("missing fronted posts")

    updated_fronted_posts_by_path = {}
    silos_included = set()
    for path, silo_ids_by_silo in silo_ids_by_path.items():
        fronted_post = fronted_posts_by_path[path]

        # Format:
        # {
        #     'dev_silo_id': 42,
        #     'medium_silo_id': 'abc123',
        #     ...
        # }
        new_silo_ids = {}
        for silo, sid in silo_ids_by_silo.items():
            # Ignore already posts marked with this silo
            if not silo_id_for(fronted_post, silo):
                new_silo_ids[silo_key_for(silo)] = sid
                silos_included.add(silo)

        # Only add to commit if there're any new IDs to add.
        if not new_silo_ids:
            continue

        # Create new fronted post with old frontmatter merged with silo IDs.
        updated_post = frontmatter.Post(**dict(fronted_post.to_dict(), **new_silo_ids))
        updated_fronted_posts_by_path[path] = updated_post
    return commit_updated_posts(updated_fronted_posts_by_path, silos_included)

def commit_updated_posts(fronted_posts_by_path, silos):
    """
    Returns the response of committing the (presumably changed) given posts to
    the remote GITHUB_REF of this repo by following the recipe outlined here:

        https://developer.github.com/v3/git/

    1. Get the current commit object
    2. Retrieve the tree it points to
    3. Retrieve the content of the blob object that tree has for that
       particular file path
    4. Change the content somehow and post a new blob object with that new
       content, getting a blob SHA back
    5. Post a new tree object with that file path pointer replaced with your
       new blob SHA getting a tree SHA back
    6. Create a new commit object with the current commit SHA as the parent
       and the new tree SHA, getting a commit SHA back
    7. Update the reference of your branch to point to the new commit SHA
    """
    if not fronted_posts_by_path:
        action_log("All good: already marked.")
        return None
    if not os.getenv("GITHUB_TOKEN"):
        raise ValueError("missing GITHUB_TOKEN")
    if not os.getenv("GITHUB_REPOSITORY"):
        raise ValueError("missing GITHUB_REPOSITORY")
    if not os.getenv("GITHUB_REF"):
        raise ValueError("missing GITHUB_REF")

    parent = parent_sha()
    # Create a new tree with our updated blobs.
    new_tree = repo().create_git_tree(
        [
            InputGitTreeElement(
                path,
                mode='100644', # 'file', @see https://developer.github.com/v3/git/trees/#tree-object
                type='blob',
                content=frontmatter.dumps(fronted_post)
            )
            for path, fronted_post in fronted_posts_by_path.items()
        ],
        base_tree=repo().get_git_tree(parent)
    )

    # Commit the new tree.
    new_commit = repo().create_git_commit(
        f'(syndicate): adding IDs for {silos}',
        new_tree,
        [repo().get_git_commit(parent)]
    )
    # Poosh it.
    ref_name = os.getenv('GITHUB_REF').lstrip('refs/')
    try:
        repo().get_git_ref(ref_name).edit(new_commit.sha)
    except github.GithubException as err:
        action_error(f"Failed to mark syndicated posts: {err}")
        return None
    ## NOTE Need to update the reference SHA for future workflow steps.
    action_setenv('SYNDICATE_SHA', new_commit.sha)
    action_log("Syndicate posts marked.")
