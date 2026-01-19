#!/usr/bin/env python3
"""
Unit tests for Wayback Machine Downloader
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from wayback_downloader import WaybackDownloader


class TestWaybackDownloader:
    """Test suite for WaybackDownloader class"""

    def test_parse_wayback_url_basic(self):
        """Test parsing a basic Wayback Machine URL"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.timestamp == "20150101000000"
        assert downloader.original_domain == "example.com"

    def test_parse_wayback_url_with_path(self):
        """Test parsing a Wayback URL with path"""
        url = "https://web.archive.org/web/20150101000000/example.com/content/post"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.timestamp == "20150101000000"
        assert downloader.original_domain == "example.com"

    def test_parse_wayback_url_with_https(self):
        """Test parsing a Wayback URL with https original"""
        url = "https://web.archive.org/web/20150101000000/https://example.com/page"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.timestamp == "20150101000000"
        assert downloader.original_domain == "example.com"

    def test_parse_wayback_url_invalid(self):
        """Test that invalid URLs raise ValueError"""
        with pytest.raises(ValueError, match="Invalid Wayback Machine URL"):
            WaybackDownloader("https://example.com", output_dir="test_output")

    def test_build_wayback_url(self):
        """Test building a Wayback URL from original URL"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        wayback_url = downloader._build_wayback_url("http://example.com/page.html")
        assert (
            wayback_url
            == "https://web.archive.org/web/20150101000000/http://example.com/page.html"
        )

    def test_build_wayback_url_relative(self):
        """Test building a Wayback URL from relative path"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        wayback_url = downloader._build_wayback_url("/page.html")
        assert (
            wayback_url
            == "https://web.archive.org/web/20150101000000/http://example.com/page.html"
        )

    def test_is_internal_url_same_domain(self):
        """Test internal URL detection for same domain"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_internal_url("http://example.com/page.html") is True
        assert downloader._is_internal_url("https://example.com/page.html") is True

    def test_is_internal_url_relative(self):
        """Test internal URL detection for relative URLs"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_internal_url("/page.html") is True
        assert downloader._is_internal_url("/content/post") is True

    def test_is_internal_url_external(self):
        """Test internal URL detection for external URLs"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_internal_url("http://other.com/page.html") is False
        assert downloader._is_internal_url("https://external.org/") is False

    def test_is_internal_url_special_schemes(self):
        """Test internal URL detection for special schemes"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_internal_url("#anchor") is False
        assert downloader._is_internal_url("mailto:test@example.com") is False
        assert downloader._is_internal_url("javascript:void(0)") is False
        assert downloader._is_internal_url("tel:+1234567890") is False

    def test_is_internal_url_protocol_relative(self):
        """Test internal URL detection for protocol-relative URLs"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_internal_url("//example.com/page.html") is True
        assert downloader._is_internal_url("//other.com/page.html") is False

    def test_get_file_type_html(self):
        """Test file type detection for HTML files"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._get_file_type("http://example.com/page.html") == "html"
        assert downloader._get_file_type("http://example.com/page.htm") == "html"
        assert downloader._get_file_type("http://example.com/page.php") == "html"
        assert downloader._get_file_type("http://example.com/page") == "html"
        assert downloader._get_file_type("http://example.com/") == "html"

    def test_get_file_type_images(self):
        """Test file type detection for images"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._get_file_type("http://example.com/image.jpg") == "image"
        assert downloader._get_file_type("http://example.com/image.jpeg") == "image"
        assert downloader._get_file_type("http://example.com/image.png") == "image"
        assert downloader._get_file_type("http://example.com/image.gif") == "image"
        assert downloader._get_file_type("http://example.com/image.svg") == "image"
        assert downloader._get_file_type("http://example.com/image.webp") == "image"
        assert downloader._get_file_type("http://example.com/favicon.ico") == "image"

    def test_get_file_type_css(self):
        """Test file type detection for CSS"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._get_file_type("http://example.com/style.css") == "css"

    def test_get_file_type_js(self):
        """Test file type detection for JavaScript"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._get_file_type("http://example.com/script.js") == "js"

    def test_get_file_type_other(self):
        """Test file type detection for other files"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._get_file_type("http://example.com/file.pdf") == "other"
        assert downloader._get_file_type("http://example.com/file.zip") == "other"

    def test_url_to_filepath_root(self):
        """Test URL to filepath conversion for root"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        filepath = downloader._url_to_filepath("http://example.com/")
        assert filepath == Path("test_output/index.html")

    def test_url_to_filepath_page(self):
        """Test URL to filepath conversion for pages"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        filepath = downloader._url_to_filepath("http://example.com/content/post.html")
        assert filepath == Path("test_output/content/post.html")

    def test_url_to_filepath_no_extension(self):
        """Test URL to filepath conversion for URLs without extension"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        filepath = downloader._url_to_filepath("http://example.com/about")
        assert filepath == Path("test_output/about.html")

    def test_url_to_filepath_trailing_slash(self):
        """Test URL to filepath conversion for trailing slash"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        filepath = downloader._url_to_filepath("http://example.com/content/")
        assert filepath == Path("test_output/content/index.html")

    def test_url_to_filepath_with_query(self):
        """Test URL to filepath conversion with query parameters"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        filepath = downloader._url_to_filepath(
            "http://example.com/page?id=123&name=test"
        )
        assert "page" in str(filepath)
        assert "id" in str(filepath)
        assert "test" in str(filepath)

    def test_init_with_custom_delay(self):
        """Test initialization with custom delay"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output", delay=2.5)

        assert downloader.delay == 2.5

    def test_init_default_delay(self):
        """Test initialization with default delay"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.delay == 1.0

    def test_init_max_pages(self):
        """Test initialization with max pages limit"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output", max_pages=50)

        assert downloader.max_pages == 50

    def test_session_has_user_agent(self):
        """Test that session has custom User-Agent header"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert "User-Agent" in downloader.session.headers
        assert "WaybackDownloader" in str(downloader.session.headers["User-Agent"])

    def test_stats_initialization(self):
        """Test that statistics are properly initialized"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.stats["pages"] == 0
        assert downloader.stats["images"] == 0
        assert downloader.stats["css"] == 0
        assert downloader.stats["js"] == 0
        assert downloader.stats["other"] == 0
        assert downloader.stats["retries"] == 0

    @patch("wayback_downloader.requests.Session.get")
    def test_download_file_success(self, mock_get):
        """Test successful file download"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.content = b"<html><body>Test</body></html>"
        mock_get.return_value = mock_response

        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        result = downloader._download_file(
            "https://web.archive.org/web/20150101000000/http://example.com/test.html",
            "http://example.com/test.html",
        )

        assert result is not None
        assert "http://example.com/test.html" in downloader.visited_urls

    @patch("wayback_downloader.requests.Session.get")
    @patch("time.sleep")
    def test_download_file_rate_limited(self, mock_sleep, mock_get):
        """Test file download with rate limiting (HTTP 429)"""
        # First call returns 429, second call succeeds
        mock_response_429 = Mock()
        mock_response_429.status_code = 429

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.text = "<html><body>Test</body></html>"
        mock_response_200.content = b"<html><body>Test</body></html>"

        mock_get.side_effect = [mock_response_429, mock_response_200]

        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        result = downloader._download_file(
            "https://web.archive.org/web/20150101000000/http://example.com/test.html",
            "http://example.com/test.html",
        )

        assert result is not None
        assert downloader.stats["retries"] == 1
        assert mock_sleep.called

    @patch("wayback_downloader.requests.Session.get")
    def test_download_file_already_visited(self, mock_get):
        """Test that already visited URLs are skipped"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        # Mark URL as visited
        downloader.visited_urls.add("http://example.com/test.html")

        result = downloader._download_file(
            "https://web.archive.org/web/20150101000000/http://example.com/test.html",
            "http://example.com/test.html",
        )

        assert result is None
        assert not mock_get.called


class TestURLEdgeCases:
    """Test edge cases in URL handling"""

    def test_empty_path(self):
        """Test handling of empty path"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        filepath = downloader._url_to_filepath("http://example.com")
        assert filepath == Path("test_output/index.html")

    def test_complex_query_string(self):
        """Test handling of complex query strings"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        filepath = downloader._url_to_filepath(
            "http://example.com/search?q=test&page=2&sort=date"
        )
        # Should create a valid filepath
        assert filepath.parent == Path("test_output")
        assert "search" in str(filepath)


class TestInitialization:
    """Test downloader initialization"""

    def test_output_dir_path_object(self):
        """Test that output_dir is converted to Path"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert isinstance(downloader.output_dir, Path)
        assert downloader.output_dir == Path("test_output")

    def test_visited_urls_empty(self):
        """Test that visited URLs set is empty on init"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert len(downloader.visited_urls) == 0

    def test_url_queue_empty(self):
        """Test that URL queue is empty on init"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert len(downloader.url_queue) == 0


class TestWaybackURLSuffixes:
    """Test handling of Wayback Machine URL suffixes (cs_, js_, im_, etc.)"""

    def test_parse_wayback_url_with_css_suffix(self):
        """Test parsing Wayback URL with cs_ suffix"""
        url = "https://web.archive.org/web/20210414192058cs_/https://example.com/style.css"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.timestamp == "20210414192058"
        assert downloader.original_domain == "example.com"

    def test_parse_wayback_url_with_js_suffix(self):
        """Test parsing Wayback URL with js_ suffix"""
        url = "https://web.archive.org/web/20210414192058js_/https://example.com/script.js"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.timestamp == "20210414192058"
        assert downloader.original_domain == "example.com"

    def test_parse_wayback_url_with_im_suffix(self):
        """Test parsing Wayback URL with im_ suffix"""
        url = "https://web.archive.org/web/20210414192058im_/https://example.com/image.png"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.timestamp == "20210414192058"
        assert downloader.original_domain == "example.com"

    def test_rewrite_urls_cleans_css_suffix(self):
        """Test that URL rewriting handles cs_ suffix"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        html = '''<html><head>
        <link href="https://web.archive.org/web/20150101000000cs_/https://example.com/style.css" rel="stylesheet">
        </head><body></body></html>'''

        rewritten, resources = downloader._rewrite_urls_in_html(html, "http://example.com/")

        # The URL should be rewritten to a local path, not kept as archive.org
        assert "web.archive.org" not in rewritten or "style.css" in str(resources)

    def test_rewrite_urls_cleans_js_suffix(self):
        """Test that URL rewriting handles js_ suffix"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        html = '''<html><head>
        <script src="https://web.archive.org/web/20150101000000js_/https://example.com/app.js"></script>
        </head><body></body></html>'''

        rewritten, resources = downloader._rewrite_urls_in_html(html, "http://example.com/")

        # The URL should be rewritten to a local path
        assert "web.archive.org" not in rewritten or "app.js" in str(resources)

    def test_rewrite_urls_cleans_image_suffix(self):
        """Test that URL rewriting handles im_ suffix"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        html = '''<html><body>
        <img src="https://web.archive.org/web/20150101000000im_/https://example.com/photo.jpg">
        </body></html>'''

        rewritten, resources = downloader._rewrite_urls_in_html(html, "http://example.com/")

        # The URL should be rewritten to a local path
        assert "web.archive.org" not in rewritten or "photo.jpg" in str(resources)


class TestCheckUrlReachable:
    """Test URL reachability checking"""

    @patch("wayback_downloader.requests.Session.head")
    def test_check_url_reachable_success(self, mock_head):
        """Test URL reachability check returns True for successful response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._check_url_reachable("http://example.com") is True

    @patch("wayback_downloader.requests.Session.head")
    def test_check_url_reachable_redirect(self, mock_head):
        """Test URL reachability check returns True for redirect"""
        mock_response = Mock()
        mock_response.status_code = 301
        mock_head.return_value = mock_response

        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._check_url_reachable("http://example.com") is True

    @patch("wayback_downloader.requests.Session.head")
    def test_check_url_reachable_not_found(self, mock_head):
        """Test URL reachability check returns False for 404"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._check_url_reachable("http://example.com") is False

    @patch("wayback_downloader.requests.Session.head")
    def test_check_url_reachable_exception(self, mock_head):
        """Test URL reachability check returns False on exception"""
        import requests
        mock_head.side_effect = requests.exceptions.ConnectionError()

        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._check_url_reachable("http://example.com") is False


class TestBasePathScoping:
    """Test base path scoping functionality"""

    def test_parse_base_path_root(self):
        """Test parsing base path from root URL"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.base_path == ""

    def test_parse_base_path_with_directory(self):
        """Test parsing base path from URL with directory"""
        url = "https://web.archive.org/web/20150101000000/example.com/blog/"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.base_path == "/blog"

    def test_parse_base_path_nested_directory(self):
        """Test parsing base path from URL with nested directory"""
        url = "https://web.archive.org/web/20150101000000/example.com/content/posts"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader.base_path == "/content/posts"

    def test_is_within_base_path_root_scope(self):
        """Test that all URLs are within scope when base path is root"""
        url = "https://web.archive.org/web/20150101000000/example.com"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_within_base_path("/blog/post.html") is True
        assert downloader._is_within_base_path("/about.html") is True
        assert downloader._is_within_base_path("/content/page") is True

    def test_is_within_base_path_restricted_scope(self):
        """Test URL scoping with restricted base path"""
        url = "https://web.archive.org/web/20150101000000/example.com/blog/"
        downloader = WaybackDownloader(url, output_dir="test_output")

        # Within base path
        assert downloader._is_within_base_path("/blog/post.html") is True
        assert downloader._is_within_base_path("/blog/2021/article") is True
        assert downloader._is_within_base_path("http://example.com/blog/page") is True

        # Outside base path
        assert downloader._is_within_base_path("/about.html") is False
        assert downloader._is_within_base_path("/contact") is False
        assert downloader._is_within_base_path("http://example.com/docs/") is False

    def test_is_within_base_path_exact_match(self):
        """Test that exact base path match is within scope"""
        url = "https://web.archive.org/web/20150101000000/example.com/blog"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_within_base_path("/blog") is True
        assert downloader._is_within_base_path("/blog/") is True

    def test_is_within_base_path_relative_urls(self):
        """Test base path scoping with relative URLs"""
        url = "https://web.archive.org/web/20150101000000/example.com/blog/"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_within_base_path("/blog/post.html") is True
        assert downloader._is_within_base_path("/blog/category/tech") is True

    def test_is_within_base_path_external_domain(self):
        """Test that external domains are not within scope"""
        url = "https://web.archive.org/web/20150101000000/example.com/blog/"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert (
            downloader._is_within_base_path("http://other.com/blog/post.html") is False
        )

    def test_is_within_base_path_nested(self):
        """Test deeply nested paths within base path"""
        url = "https://web.archive.org/web/20150101000000/example.com/docs/"
        downloader = WaybackDownloader(url, output_dir="test_output")

        assert downloader._is_within_base_path("/docs/api/v1/reference") is True
        assert downloader._is_within_base_path("/docs/guide/intro.html") is True
        assert downloader._is_within_base_path("/api/v1/reference") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
