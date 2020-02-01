import frontmatter
import textwrap

# A light-weight, as-needed mock of github3.repos.contents.Contents
# @see https://github3.readthedocs.io/en/master/api-reference/repos.html#github3.repos.contents.Contents
class MockPost:
    def __init__(self):
        self.raw_contents = textwrap.dedent(
            """
            ---
            title: A beautiful mock
            tags: beauty, fake
            ---
            What is a body?
            """).strip()
        self.front, _ = frontmatter.parse(self.raw_contents)
        self.decoded = self.raw_contents.encode('utf-8')
        self.html_url = 'https://silo.com/a-beautiful-mock'
        self.updated = False

    def update(self, *args, **kwargs):
        self.updated = True
