import frontmatter
import textwrap

class MockPost:
    """
    A light-weight mock of a post object.
    @see https://github3.readthedocs.io/en/master/api-reference/repos.html#github3.repos.contents.Contents
    """
    def __init__(self):
        self.raw_contents = textwrap.dedent(
            """
            ---
            dev_silo_id: 42
            title: A beautiful mock
            tags: beauty, fake
            ---
            What is a body?
            """).strip()
        self.decoded = self.raw_contents.encode('utf-8')
        self.name = 'a-beautiful-mock.md'
