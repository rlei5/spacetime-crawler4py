import re
from urllib.parse import urlparse, urljoin, urldefrag, parse_qs
import analytics_utils
import subdomain_utils
from bs4 import BeautifulSoup

subdomain_utils._load()

def scraper(url: str, resp) -> list:
    links = extract_next_links(url, resp)

    if resp.status == 200 and resp.raw_response and resp.raw_response.content:
        content = resp.raw_response.content

        subdomain_utils.record_visit(url)

        # process text only if not a near-duplicate
        # if not analytics_utils.is_duplicate(content):
        analytics_utils.process_text(url, content)

    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    links = set()
    if resp is None or resp.status != 200:
        return []
    if resp.raw_response is None or resp.raw_response.content is None:
        return []
    # avoid dead pages with no content
    if len(resp.raw_response.content) < 100:
        return []
    # avoid very large files (5MB cap)
    if len(resp.raw_response.content) > 5 * 1024 * 1024:
        return []
    # only process html pages
    content_type = resp.raw_response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        return []
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
        # avoid pages with low textual content
        if len(soup.get_text(strip=True)) < 200:
            return []
        for tag in soup.find_all("a", href=True):
            href = tag.get("href")
            if href is None:
                continue
            href = href.strip()
            if href == "":
                continue
            if href.startswith("#"):
                continue
            if href.lower().startswith(("mailto:", "javascript:", "tel:")):
                continue
            absolute_url = urljoin(url, href)
            clean_url, _ = urldefrag(absolute_url)
            if not clean_url.startswith("http"):
                continue
            if len(clean_url) > 200: # too long
                continue
            links.add(clean_url)
    except Exception as e:
        print("Error extracting links from", url, ":", e)
    return list(links)

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # Make sure to crawl only the URls allowed by the assignment
        if not re.search(r"(^|\.)((ics|cs|informatics|stat)\.uci\.edu)$", parsed.hostname):
            return False
        # Avoid known trap domains
        if re.search(r"(wics\.ics|ngs\.ics|gitlab\.ics|grape\.ics)\.uci\.edu$", parsed.hostname):
            return False
        # Avoid known trap paths
        if re.search(r"~eppstein/pix", url.lower()):
            return False
        if re.search(r"doku\.php", parsed.path.lower()):
            if re.search(r"(do=|idx=|maint:|rev=|diff|oldid=|s\[\]=)", parsed.query.lower()):
                return False
        # Try to avoid links that have infinite length
        if parsed.path.count("/") > 20:
            return False
        # Detect repeating path segments (e.g. /a/b/a/b)
        segments = [s for s in parsed.path.split("/") if s]
        if len(segments) != len(set(segments)):
            return False
        # Avoid URLs with too many query parameters
        if len(parse_qs(parsed.query)) > 10:
            return False
        # Avoid common trap patterns in path or query
        if re.search(r"(calendar|filter|sort|offset|session)", parsed.path.lower()):
            return False
        if re.search(r"/\d{4}-\d{2}-\d{2}", parsed.path.lower()):
            return False
        if re.search(r"(tribe-bar-date|ical|eventDisplay|date=|page=|share=)", parsed.query.lower()):
            return False
        # block dale-cooper trap domain
        if re.search(r"dale-cooper", parsed.hostname):
            return False
        # block action=update pattern
        if re.search(r"action=update", parsed.query.lower()):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except (TypeError, ValueError):
        print("Invalid URL: ", url)
        return False
