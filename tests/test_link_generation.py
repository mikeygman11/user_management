"""tests/test_link_generation.py — Tests for URL link-generation utilities

This module contains unit tests for functions in app.utils.link_generation,
including create_link, create_user_links, and pagination link generators.
"""

import os
import sys
from urllib.parse import parse_qs, urlparse, urlunparse, urlencode

from builtins import len, sorted, str
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import Request

# Allow imports from the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.link_generation import (
    create_link,
    create_user_links,
    generate_pagination_links,
)

def normalize_url(url):
    """Normalize URL by sorting query parameters and stripping trailing slash."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query, keep_blank_values=True)
    sorted_items = sorted((k, sorted(v)) for k, v in query_params.items())
    encoded_query = urlencode(sorted_items, doseq=True)
    normalized = urlunparse(parsed_url._replace(query=encoded_query))
    return normalized.rstrip('/')

@pytest.fixture
def mock_request():
    """Provide a mock FastAPI Request with url_for and url attributes for testing."""
    request = MagicMock(spec=Request)
    request.url_for = MagicMock(
        side_effect=lambda action, user_id: (
            f"http://testserver/{action}/{user_id}"
        )
    )
    request.url = "http://testserver/users"
    return request


def test_create_link():
    """Test that create_link produces a link with the correct href attribute."""
    link = create_link("self", "http://example.com", "GET", "view")
    assert normalize_url(str(link.href)) == "http://example.com"


def test_create_user_links(mock_request):
    """Test that create_user_links returns three correct HATEOAS links."""
    user_id = uuid4()
    links = create_user_links(user_id, mock_request)
    assert len(links) == 3
    assert normalize_url(str(links[0].href)) == (
        f"http://testserver/get_user/{user_id}"
    )
    assert normalize_url(str(links[1].href)) == (
        f"http://testserver/update_user/{user_id}"
    )
    assert normalize_url(str(links[2].href)) == (
        f"http://testserver/delete_user/{user_id}"
    )


def test_generate_pagination_links(mock_request):
    """Test that generate_pagination_links produces correct pagination links.
    Includes the self link and navigation to other pages."""
    skip = 10
    limit = 5
    total_items = 50
    links = generate_pagination_links(mock_request, skip, limit, total_items)
    assert len(links) >= 4
    expected_self_url = "http://testserver/users?limit=5&skip=10"
    assert normalize_url(str(links[0].href)) == normalize_url(
        expected_self_url
    ), "Self link should match expected URL"