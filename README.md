# Wayback Machine Blog Downloader

A Python tool to download and recover archived websites from the Wayback Machine (web.archive.org). This tool crawls an archived snapshot, downloads all content (HTML, images, CSS, JavaScript), and rewrites URLs to create a fully functional static copy that works offline.

## Features

- Downloads complete website snapshots from Wayback Machine
- Automatically discovers and follows all internal links
- Downloads all assets: HTML, CSS, JavaScript, images
- Rewrites URLs for local browsing (no internet connection needed)
- Removes Wayback Machine toolbar and scripts
- Preserves original site structure
- **Smart rate limiting** with configurable delays (default: 1 second between requests)
- **Automatic retry logic** with exponential backoff for rate limit errors (HTTP 429)
- **Connection pooling** for improved performance
- **Custom User-Agent** to identify the tool

## Requirements

- Python 3.8 or higher
- requests library
- beautifulsoup4 library

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python wayback_downloader.py "WAYBACK_URL"
```

Where `WAYBACK_URL` is the full Wayback Machine URL including timestamp.

### Finding Your Wayback URL

1. Go to https://web.archive.org
2. Enter your old blog URL
3. Browse the calendar to find a snapshot
4. Click on a timestamp to view the archived page
5. Copy the full URL from the browser address bar

The URL should look like:
```
https://web.archive.org/web/20150315000000/yourblog.com
```

### Examples

Download a blog to the default directory:
```bash
python wayback_downloader.py "https://web.archive.org/web/20150315000000/myblog.com"
```

Specify a custom output directory:
```bash
python wayback_downloader.py "https://web.archive.org/web/20150315000000/myblog.com" -o my_recovered_blog
```

Limit download to first 50 pages (useful for testing):
```bash
python wayback_downloader.py "https://web.archive.org/web/20150315000000/myblog.com" --max-pages 50
```

Adjust delay between requests (for faster or slower downloads):
```bash
python wayback_downloader.py "https://web.archive.org/web/20150315000000/myblog.com" --delay 2.0
```

### Command-Line Options

- `wayback_url`: (Required) Full Wayback Machine URL with timestamp
- `-o, --output`: Output directory (default: `downloaded_site`)
- `--max-pages`: Maximum number of pages to download (default: unlimited)
- `--delay`: Delay in seconds between requests (default: 1.0, recommended: 1.0-2.0)

## Rate Limiting

The tool includes built-in rate limiting to be respectful to the Internet Archive's servers:

- **Default delay**: 1 second between requests (recommended)
- **Automatic retry**: HTTP 429 (rate limit) responses trigger exponential backoff
- **Max retries**: 5 attempts with increasing delays (2s, 4s, 8s, 16s, 32s)
- **User-Agent**: Identifies requests as coming from this tool

**Important**: The Internet Archive enforces rate limits to manage server load:
- Exceeding ~60 requests/minute may trigger HTTP 429 responses
- Persistent violations can result in temporary IP blocks (1+ hours)
- Use `--delay 1.0` or higher for large downloads to avoid issues

If you need faster downloads, you can reduce the delay (e.g., `--delay 0.5`), but monitor for rate limit errors. If you see "Rate limited (429)" messages, the tool will automatically slow down.

## How It Works

1. **URL Parsing**: Extracts the timestamp and original domain from the Wayback Machine URL
2. **Crawling**: Starts from the initial URL and follows all internal links
3. **Downloading**: Downloads HTML pages and all referenced resources (images, CSS, JS)
4. **URL Rewriting**: Converts all links to relative paths for local browsing
5. **Cleanup**: Removes Wayback Machine toolbar and scripts

## Output

The downloaded site will be saved in the specified output directory with the same structure as the original site. To view your recovered blog:

1. Navigate to the output directory
2. Open `index.html` in your web browser
3. Browse the site normally - all links will work locally

## Tips

- Start with `--max-pages 10` to test before downloading entire sites
- Large sites may take a long time - the default 1 second delay between requests ensures respectful usage
- Not all archived pages may be available - the tool will skip missing resources
- Check your output directory periodically to monitor progress
- If you encounter rate limiting (429 errors), the tool will automatically retry with exponential backoff
- For very large sites, consider increasing the delay to 2.0 seconds: `--delay 2.0`

## Troubleshooting

**Missing dependencies error:**
```bash
pip install requests beautifulsoup4
```

**Invalid Wayback URL error:**
Make sure your URL includes the timestamp and follows this format:
```
https://web.archive.org/web/TIMESTAMP/ORIGINAL_URL
```

**Rate limit errors (HTTP 429):**
The tool automatically handles rate limiting with exponential backoff. If you see repeated rate limit messages:
- Increase the delay: `--delay 2.0` or higher
- The tool will automatically retry up to 5 times with increasing delays
- Persistent rate limiting may indicate an IP block (wait 1+ hours)

**Slow downloads:**
This is normal and intentional. The tool uses a 1-second delay between requests to be respectful to archive.org. You can monitor progress in the terminal output. For faster downloads, reduce the delay at your own risk: `--delay 0.5`

## Limitations

- Only downloads content available in the Wayback Machine
- Some dynamic features may not work (JavaScript-heavy sites, AJAX)
- External resources (from other domains) are not downloaded
- Very large sites may take considerable time to download

## Development

### Running Tests

The project includes a comprehensive test suite. To run the tests:

1. Install development dependencies:
```bash
pip install pytest pytest-mock
```

Or with uv (recommended):
```bash
uv sync --dev
```

2. Run the test suite:
```bash
pytest
```

Or with uv:
```bash
uv run pytest
```

Run with verbose output:
```bash
uv run pytest -v
```

Run with coverage report (requires pytest-cov):
```bash
uv run pytest --cov=wayback_downloader --cov-report=html
```

### Test Coverage

The test suite covers:
- URL parsing and validation
- File type detection
- Internal vs external URL detection
- URL to filepath conversion
- Rate limiting and retry logic
- HTTP 429 handling with exponential backoff
- Session management and headers

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

Please be respectful of the Internet Archive's resources and use reasonable rate limiting when downloading archived content.
