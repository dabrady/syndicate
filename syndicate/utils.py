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

def get_posts(commit=None, post_dir='pages/posts'):
    assert commit, 'missing commit payload'
    return {
        file['filename']:file['status']
        for file in commit.files
        if (
            file['filename'].startswith(post_dir) and
            file['status'] in ('created', 'modified')
        )
    }
