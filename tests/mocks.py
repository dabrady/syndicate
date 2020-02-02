import frontmatter
import textwrap

# A light-weight, as-needed mock of github3.repos.contents.Contents
# @see https://github3.readthedocs.io/en/master/api-reference/repos.html#github3.repos.contents.Contents
class MockPost:
    def __init__(self):
        self.raw_contents = textwrap.dedent(
            """
            ---
            dev_syndicate_id: 42
            title: A beautiful mock
            tags: beauty, fake
            ---
            What is a body?
            """).strip()
        self.front, _ = frontmatter.parse(self.raw_contents)
        self.decoded = self.raw_contents.encode('utf-8')
        self.name = 'a-beautiful-mock.md'
        self.html_url = f'https://silo.com/{self.name}'
