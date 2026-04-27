import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    links = set()
    if resp is None or resp.status != 200:
        return []
    if resp.raw_response is None or resp.raw_response.content is None:
        return []
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")
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
            if clean_url:
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
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
