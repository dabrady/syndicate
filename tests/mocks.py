import frontmatter
import textwrap

class MockPost:
    """
    A light-weight mock of a post object.
    @see https://pygithub.readthedocs.io/en/latest/github_objects/ContentFile.html#github.ContentFile.ContentFile
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
        self.decoded_content = self.raw_contents.encode('utf-8')
        self.name = 'a-beautiful-mock.md'
