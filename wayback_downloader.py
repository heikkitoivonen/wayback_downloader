#!/usr/bin/env python3
"""
Wayback Machine Downloader
Downloads archived websites from web.archive.org and builds a static local copy.
"""

import os
import re
import sys
import argparse
import logging
from urllib.parse import urlparse, urljoin
from pathlib import Path
from collections import deque
import time

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not found.")
    print("Please install dependencies: pip install requests beautifulsoup4")
    sys.exit(1)


# Set up logging
logger = logging.getLogger(__name__)


class WaybackDownloader:
    def __init__(
        self,
        wayback_url: str,
        output_dir: str = "downloaded_site",
        max_pages: int | None = None,
        delay: float = 1.0,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the Wayback Machine downloader.

        Args:
            wayback_url: Full Wayback Machine URL (e.g., https://web.archive.org/web/20150101000000/example.com)
            output_dir: Directory to save downloaded content
            max_pages: Maximum number of pages to download (None for unlimited)
            delay: Delay in seconds between requests (default: 1.0)
            verbose: Enable verbose output (default: False)
        """
        self.wayback_url = wayback_url
        self.output_dir = Path(output_dir)
        self.max_pages = max_pages
        self.delay = delay
        self.verbose = verbose

        # Parse the Wayback URL to extract timestamp and original URL
        self.timestamp, self.original_domain, self.base_path = self._parse_wayback_url(
            wayback_url
        )

        # Set to track visited URLs (to avoid duplicates)
        self.visited_urls = set()

        # Queue for URLs to process
        self.url_queue = deque()

        # Session for connection pooling and custom headers
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "WaybackDownloader/1.0 (https://github.com/heikkitoivonen/wayback_downloader)"
            }
        )

        # Statistics
        self.stats = {
            "pages": 0,
            "images": 0,
            "css": 0,
            "js": 0,
            "other": 0,
            "retries": 0,
        }

    def _parse_wayback_url(self, url: str) -> tuple[str, str, str]:
        """Extract timestamp, original URL, and base path from Wayback Machine URL."""
        # Pattern: https://web.archive.org/web/TIMESTAMP/ORIGINAL_URL
        pattern = r"https?://web\.archive\.org/web/(\d+)/(.*)"
        match = re.match(pattern, url)

        if not match:
            raise ValueError(f"Invalid Wayback Machine URL: {url}")

        timestamp = match.group(1)
        original_url = match.group(2)

        # Extract domain from original URL
        if not original_url.startswith("http"):
            original_url = "http://" + original_url

        parsed = urlparse(original_url)
        domain = parsed.netloc
        base_path = parsed.path.rstrip("/")  # Remove trailing slash for consistency

        logger.info(f"Timestamp: {timestamp}")
        logger.info(f"Original domain: {domain}")
        logger.info(f"Base path: {base_path if base_path else '/'}")

        return timestamp, domain, base_path

    def _build_wayback_url(self, original_url: str) -> str:
        """Convert an original URL to its Wayback Machine equivalent."""
        # Handle relative URLs
        if not original_url.startswith("http"):
            original_url = f"http://{self.original_domain}{original_url}"

        return f"https://web.archive.org/web/{self.timestamp}/{original_url}"

    def _is_internal_url(self, url: str) -> bool:
        """Check if URL belongs to the original domain."""
        if not url:
            return False

        # Handle relative URLs
        if url.startswith("/") and not url.startswith("//"):
            return True

        # Handle protocol-relative URLs
        if url.startswith("//"):
            url = "http:" + url

        # Skip anchors, mailto, javascript, etc.
        if url.startswith(("#", "mailto:", "javascript:", "tel:")):
            return False

        try:
            parsed = urlparse(url)
            return parsed.netloc == self.original_domain or parsed.netloc == ""
        except (ValueError, AttributeError):
            return False

    def _is_within_base_path(self, url: str) -> bool:
        """Check if URL is within the base path specified in the starting URL."""
        if not url:
            return False

        # If base_path is root, everything is within scope
        if not self.base_path or self.base_path == "/":
            return True

        # Handle relative URLs
        if url.startswith("/") and not url.startswith("//"):
            path = url
        elif url.startswith("//"):
            parsed = urlparse("http:" + url)
            path = parsed.path
        else:
            parsed = urlparse(url)
            # Only check path if it's on our domain
            if parsed.netloc and parsed.netloc != self.original_domain:
                return False
            path = parsed.path

        # Remove trailing slash for comparison
        path = path.rstrip("/")

        # Check if path starts with base_path
        return path.startswith(self.base_path) or path == self.base_path.rstrip("/")

    def _get_file_type(self, url: str) -> str:
        """Determine the file type based on URL."""
        url_lower = url.lower()

        if any(
            url_lower.endswith(ext)
            for ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".svg",
                ".webp",
                ".ico",
            ]
        ):
            return "image"
        elif url_lower.endswith(".css"):
            return "css"
        elif url_lower.endswith(".js"):
            return "js"
        elif (
            any(
                url_lower.endswith(ext)
                for ext in [".html", ".htm", ".php", ".asp", ".aspx"]
            )
            or "." not in Path(urlparse(url).path).name
        ):
            return "html"
        else:
            return "other"

    def _url_to_filepath(self, url: str) -> Path:
        """Convert a URL to a local file path."""
        parsed = urlparse(url)
        path = parsed.path

        # Handle root path
        if not path or path == "/":
            path = "/index.html"

        # Add index.html if path ends with /
        if path.endswith("/"):
            path += "index.html"

        # If no extension, add .html
        if "." not in Path(path).name:
            path += ".html"

        # Remove leading slash and clean up
        path = path.lstrip("/")

        # Handle query parameters by creating a filename
        if parsed.query:
            path = (
                path.replace("?", "_")
                + "_"
                + parsed.query.replace("&", "_").replace("=", "_")
            )

        return self.output_dir / path

    def _check_url_reachable(self, url: str) -> bool:
        """Check if a URL is reachable via HEAD request."""
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code < 400
        except requests.exceptions.RequestException:
            return False

    def _download_file(self, wayback_url: str, original_url: str) -> requests.Response | None:
        """Download a file from Wayback Machine with retry logic."""
        try:
            # Check if already downloaded
            if original_url in self.visited_urls:
                return None

            self.visited_urls.add(original_url)

            # Retry logic for rate limiting
            max_retries = 5
            retry_delay = 2.0  # Start with 2 seconds
            response: requests.Response | None = None

            for attempt in range(max_retries):
                try:
                    # Get the file
                    response = self.session.get(wayback_url, timeout=30)

                    # Handle rate limiting (HTTP 429)
                    if response.status_code == 429:
                        if attempt < max_retries - 1:
                            self.stats["retries"] += 1
                            wait_time = retry_delay * (
                                2**attempt
                            )  # Exponential backoff
                            logger.warning(
                                f"Rate limited (429). Waiting {wait_time:.1f} seconds before retry {attempt + 1}/{max_retries}..."
                            )
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.warning(
                                "Rate limited (429). Max retries exceeded, skipping."
                            )
                            return None

                    response.raise_for_status()
                    break  # Success, exit retry loop

                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1 and "429" in str(e):
                        self.stats["retries"] += 1
                        wait_time = retry_delay * (2**attempt)
                        logger.warning(
                            f"Rate limited. Waiting {wait_time:.1f} seconds before retry {attempt + 1}/{max_retries}..."
                        )
                        time.sleep(wait_time)
                        continue
                    raise  # Re-raise if not 429 or max retries exceeded

            assert response is not None  # Loop always succeeds or raises

            # Determine local path
            filepath = self._url_to_filepath(original_url)

            # Create directory if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Save file
            if self._get_file_type(original_url) in ["image", "other"]:
                # Binary files
                with open(filepath, "wb") as f:
                    f.write(response.content)
            else:
                # Text files
                with open(filepath, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(response.text)

            return response

        except Exception as e:
            logger.error(f"Error downloading {wayback_url}: {e}")
            return None

    def _rewrite_urls_in_html(self, html_content: str, base_url: str) -> tuple[str, list[str]]:
        """Rewrite URLs in HTML to point to local files."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Track found resources
        resources = []

        # Rewrite links in various tags
        for tag_name, attr in [
            ("a", "href"),
            ("link", "href"),
            ("script", "src"),
            ("img", "src"),
            ("source", "src"),
            ("video", "src"),
            ("audio", "src"),
            ("iframe", "src"),
        ]:
            for tag in soup.find_all(tag_name):
                if tag.has_attr(attr):
                    tag_url = str(tag[attr])

                    # Skip Wayback Machine's own resources
                    if "web.archive.org" in tag_url and "/static/" in tag_url:
                        tag.decompose()  # Remove Wayback toolbar/scripts
                        continue

                    # Check if this is a Wayback URL and extract original
                    was_wayback_url = "web.archive.org/web/" in tag_url
                    original_url = tag_url

                    if was_wayback_url:
                        # Extract original URL from Wayback URL
                        match = re.search(
                            r"web\.archive\.org/web/\d+/(.*)", tag_url
                        )
                        if match:
                            original_url = match.group(1)
                            if not original_url.startswith("http"):
                                original_url = "http://" + original_url

                    # Make absolute URL
                    absolute_url = urljoin(base_url, original_url)

                    # Process internal URLs
                    if self._is_internal_url(absolute_url):
                        # Check if URL is within our base path scope
                        if self._is_within_base_path(absolute_url):
                            # Convert to relative local path
                            local_path = self._url_to_filepath(absolute_url)
                            current_path = self._url_to_filepath(base_url)

                            try:
                                relative_path = os.path.relpath(
                                    local_path, current_path.parent
                                )
                                tag[attr] = relative_path

                                # Track resource for downloading
                                resources.append(absolute_url)
                            except (ValueError, OSError):
                                pass
                        else:
                            # Link is on same domain but outside base path
                            # Keep it as-is (or convert to absolute path on the domain)
                            # This preserves the link but doesn't download the resource
                            pass
                    elif was_wayback_url:
                        # External link that was a Wayback URL
                        # Check if original URL is reachable
                        if self._check_url_reachable(absolute_url):
                            # Original site is up, use the original URL
                            tag[attr] = absolute_url
                        # else: keep the Wayback URL (tag_url) as-is

        # Remove Wayback Machine toolbar and scripts
        for script in soup.find_all("script"):
            if script.string and (
                "archive.org" in script.string or "wombat" in script.string.lower()
            ):
                script.decompose()

        return str(soup), resources

    def _crawl_page(self, original_url: str) -> None:
        """Download a page and extract links to other pages/resources."""
        wayback_url = self._build_wayback_url(original_url)

        logger.debug(f"Downloading: {original_url}")
        logger.debug(f"From: {wayback_url}")

        response = self._download_file(wayback_url, original_url)

        if not response:
            return

        file_type = self._get_file_type(original_url)

        # Output progress indicator
        if self.verbose:
            # Show local path in verbose mode
            local_path = self._url_to_filepath(original_url)
            rel_path = local_path.relative_to(self.output_dir)
            print(f"  {rel_path}")
        else:
            # Just print a dot for normal mode
            print(".", end="", flush=True)

        # Update statistics
        if file_type == "html":
            self.stats["pages"] += 1
        elif file_type == "image":
            self.stats["images"] += 1
        elif file_type == "css":
            self.stats["css"] += 1
        elif file_type == "js":
            self.stats["js"] += 1
        else:
            self.stats["other"] += 1

        # Process HTML to extract links and rewrite URLs
        if file_type == "html":
            rewritten_html, resources = self._rewrite_urls_in_html(
                response.text, original_url
            )

            # Save rewritten HTML
            filepath = self._url_to_filepath(original_url)
            with open(filepath, "w", encoding="utf-8", errors="ignore") as f:
                f.write(rewritten_html)

            # Parse for links to other pages
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = str(link["href"])

                # Clean Wayback URLs
                if "web.archive.org/web/" in href:
                    match = re.search(r"web\.archive\.org/web/\d+/(.*)", href)
                    if match:
                        href = match.group(1)
                        if not href.startswith("http"):
                            href = "http://" + href

                # Make absolute
                absolute_url = urljoin(original_url, href)

                # Add internal HTML pages to queue (only if within base path)
                if (
                    self._is_internal_url(absolute_url)
                    and self._is_within_base_path(absolute_url)
                    and self._get_file_type(absolute_url) == "html"
                ):
                    if absolute_url not in self.visited_urls:
                        self.url_queue.append(absolute_url)

            # Add resources to queue
            for resource_url in resources:
                if (
                    resource_url not in self.visited_urls
                    and self._get_file_type(resource_url) != "html"
                ):
                    self.url_queue.append(resource_url)

        # Be nice to the server
        time.sleep(self.delay)

    def download(self) -> None:
        """Start the download process."""
        logger.info("=" * 60)
        logger.info("Wayback Machine Downloader")
        logger.info("=" * 60)
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Starting URL: {self.wayback_url}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Extract the original URL from the Wayback URL
        match = re.search(r"web\.archive\.org/web/\d+/(.*)", self.wayback_url)
        if match:
            original_start_url = match.group(1)
            if not original_start_url.startswith("http"):
                original_start_url = "http://" + original_start_url
        else:
            raise ValueError("Could not parse starting URL")

        # Start with the initial URL
        self.url_queue.append(original_start_url)

        # Process queue
        while self.url_queue:
            # Check max pages limit
            if self.max_pages and len(self.visited_urls) >= self.max_pages:
                if not self.verbose:
                    print()  # New line after dots
                logger.info(f"Reached maximum page limit ({self.max_pages})")
                break

            url = self.url_queue.popleft()
            self._crawl_page(url)

        # Ensure we end with a newline after dots
        if not self.verbose:
            print()

        # Print statistics
        logger.info("=" * 60)
        logger.info("Download Complete!")
        logger.info("=" * 60)
        logger.info(f"Pages downloaded: {self.stats['pages']}")
        logger.info(f"Images downloaded: {self.stats['images']}")
        logger.info(f"CSS files downloaded: {self.stats['css']}")
        logger.info(f"JS files downloaded: {self.stats['js']}")
        logger.info(f"Other files downloaded: {self.stats['other']}")
        total_files = sum(v for k, v in self.stats.items() if k != "retries")
        logger.info(f"Total files: {total_files}")
        if self.stats["retries"] > 0:
            logger.info(f"Rate limit retries: {self.stats['retries']}")
        logger.info(f"\nFiles saved to: {self.output_dir.absolute()}")
        logger.info(
            f"Open {self.output_dir}/index.html in your browser to view the site"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download archived websites from Wayback Machine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://web.archive.org/web/20150101000000/example.com"
  %(prog)s "https://web.archive.org/web/20150101000000/example.com" -o my_site
  %(prog)s "https://web.archive.org/web/20150101000000/example.com" --max-pages 50
  %(prog)s "https://web.archive.org/web/20150101000000/example.com" --delay 2.0
        """,
    )

    parser.add_argument("wayback_url", help="Full Wayback Machine URL")
    parser.add_argument(
        "-o",
        "--output",
        default="downloaded_site",
        help="Output directory (default: downloaded_site)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to download (default: unlimited)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between requests (default: 1.0, recommended: 1.0-2.0)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (shows each file being downloaded)",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    try:
        downloader = WaybackDownloader(
            args.wayback_url, args.output, args.max_pages, args.delay, args.verbose
        )
        downloader.download()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
