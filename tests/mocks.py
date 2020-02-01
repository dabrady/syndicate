import frontmatter
import textwrap

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

    def update(self, *args, **kwargs):
        pass
