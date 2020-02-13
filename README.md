# syndicate

A simple implementation of the [P.O.S.S.E.](https://indieweb.org/POSSE) content publishing model, packaged as a Github Action.

Write your content, store it on Github, and use this action in a workflow to draft it to silo platforms like [DEV.to](https://dev.to). The action will keep the silos up to date with your latest changes here on Github.

Wherever possible, when content is syndicated to a silo for the first time, it is created in an unpublished/"draft" form. Any exceptions to this will be called out in the documentation for [`silos`](#silos) below.

The silos currently supported are:
- https://dev.to

## Example usage

See [the example workflow](https://github.com/dabrady/syndicate/blob/develop/.github/workflows/example.yml) for a fully annotated example, but here's the quick version:

```yaml
uses: dabrady/syndicate@v1.0
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  DEV_API_KEY: ${{ secrets.DEV_API_KEY }}
  SYNDICATE_POSTS_DIR: pages/posts
with:
  silos: DEV
  mark_as_syndicated: true
```

## Be aware: Github is the source of truth
Syndication is a one-way street: changes made to your content on Github will be copied to your silos, but changes made to a copy of the content on a particular silo will not be synced to your Github repository.

**Github is the source of truth**: any changes made on specific platforms will be overwritten with whatever is in Github the next time this action processes a change to that content.

This can have undesirable effects. Not all platforms support the same writing systems, and you might often find yourself needing to tweak your content on a particular silo before you publish it; but if you then make an update to it on Github, those silo-specific tweaks will be wiped away and you'll have to do it again.

For this reason, by default this action treats your content as immutable, and creates a new draft in the specified silos for every commit you make to a particular file. This prevents overwriting existing published content with content that is unsuitable for that platform.

This comes with its own set of drawbacks and annoyances, however, so it is possible to simply manifest new content as new drafts, and push updates to existing content directly to their existing syndicated counterparts.

## Inputs

### `silos`

_Default: `none`_

A YAML list of platforms to syndicate your content to. Silo names are case insensitive but should be snake_cased if they contain spaces.
E.g.

```yaml
with:
  silos: |
    DEV
    Medium
    CNN
    BBC
```

If a given silo is unsupported, it will be ignored and called out in the action log.

The silos currently supported are:
- `DEV` (https://dev.to)

### `mark_as_syndicated`

_Default: `false`_

A flag used to trigger a commit upstream which adds the silo-specific IDs to the YAML frontmatter of your syndicated content. This ensures that any subsequent changes you make to your posts will trigger an update to the syndicated copy, instead of triggering the creation of a new draft on your silos.

For instance, if the commit that triggered this workflow added a new post called `pages/posts/i-got-a-new-cat.md`, a step in your workflow configured like this:

```yaml
steps:
- name: Push to DEV.to and sync IDs
  uses: dabrady/syndicate@v1.0
  with:
    silos: DEV
    mark_as_syndicated: true
```

will create a new draft on DEV.to with a copy of `pages/posts/i-got-a-new-cat.md` and result in a commit to the upstream head of the branch that triggered this workflow that looks like this:

```diff
diff --git a/pages/posts/i-got-a-new-cat.md b/pages/posts/i-got-a-new-cat.md
index e94caa8..cc23cc3 100644
--- a/pages/posts/i-got-a-new-cat.md
+++ b/pages/posts/i-got-a-new-cat.md
@@ -2,3 +2,4 @@ on:
---
+dev_silo_id: 5316572
title: I got a new cat!
---
```

Providing no silos, but asking to mark new posts as syndicated, will ensure any posts added to a silo **by previous steps** are properly marked before the job completes. Think of it like a save point: this approach to using the flag allows you to bundle silo syndication into as many or as few commits as you wish:

```yaml
steps:
...
- name: Save unsaved silo IDs to Github
  uses: dabrady/syndicate@v1.0
  with:
    mark_as_syndicated: true
```

### Environment variables

#### Required

##### `GITHUB_TOKEN`

In order to syndicate your content, this action needs access to your content.

A unique `GITHUB_TOKEN` secret is created by Github for every workflow run for use by actions to access the repository, and needs to be added to the environment of this action in your workflow setup. E.g.
```yaml
steps:
- name: Push to DEV.to and sync IDs
  uses: dabrady/syndicate@v1.0
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    silos: DEV
    mark_as_syndicated: true
```

See the [Github Workflow documentation](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/authenticating-with-the-github_token) for full details.

##### `<SILO>_API_KEY`

It is assumed that this action will need to interact with every supported silo via a public API, and that that API authenticates via a personal API key.

Thus, this action will ignore any silos specified unless a corresponding API key is exposed in its environment. The keys are expected to be found in environment variables matching the following format:

```
<SILO>_API_KEY
```

where `<SILO>` is a SCREAMING\_SNAKE\_CASE version of a recognized argument for the `silos` action input. For example, the API key for the `DEV` silo should be exposed as the `DEV_API_KEY` environment variable.

For details on how to expose these secrets to the action without exposing them to the world, see the [Github documentation on working with secrets](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/creating-and-using-encrypted-secrets).

#### Optional

##### `SYNDICATE_POST_DIR`

_Default: `posts`_

Natrually, not all commits to your repo may contain a change to the content you want to syndicate.

The simplistic approach currently implemented for identifying the proper files is to look for file paths with a given prefix/in a particular directory of your repo. Set this environment variable to the place in your repo (relative to the root) where you keep the stuff you want to share elsewhere.

(The choice to use an environment variable for this instead of an input is so that you can set it once in your workflow and not have to specify it on every use of this action, should you choose to use it multiple times in a given workflow.)

## Outputs

### `time`

A timestamp marking the end of the action.

### `syndicated_posts`

A JSON-formatted string of posts that were added/modified on each of the `silos` specified, including the unique identifiers given to them by the silo and the public URL of the added/modified post.
E.g.
```json
{
  "DEV": {
    "added": {
      "pages/posts/i-got-a-new-cat.md": [ 201054451, "https://dev.to/daniel13rady/i-got-a-new-cat-aej2-temp-slug-0246" ]
    },
    "modified": {}
  },
  "Medium": { ... },
  ...
}
```

#### Environment variables

##### `SYNDICATE_SHA`
:warning: Internal, do not set this yourself.

Using the `mark_as_syndicated` flag will cause a commit to be generated and pushed to the upstream of the branch that triggered the workflow. The generated commit SHA is stored in this variable for use as the parent of any commits generated by later steps and considered to be the 'head' of the branch when present.

##### `SYNDICATE_POSTS`
:warning: Internal, do not set this yourself.

**NOTE** The word is 'syndicate', not ~~'syndicate**d**'~~. It is a prefix used by convention on all environment variables set by this action.

A JSON string formatted identically to the `syndicated_posts` action output, but containing the composite results of all invocations of this action so far in the running workflow.
