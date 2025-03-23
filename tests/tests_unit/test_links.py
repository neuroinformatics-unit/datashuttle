import validators

from datashuttle.configs import links


def test_links():
    """Test canonical links are working. Unfortunately Zulip links cannot
    be validated.
    """
    assert validators.url(links.get_docs_link())
    assert validators.url(links.get_github_link())
    assert validators.url(links.get_link_github_issues())
    # assert validators.url(links.get_link_zulip()) Zulip links fail even when valid...
