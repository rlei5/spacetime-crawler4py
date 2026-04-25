import shelve
from urllib.parse import urlparse

SAVE_FILE = "crawler_data"
_SAVE_EVERY = 50  # save every 50 pages

_state = {
    "subdomains": {},
    "unique_pages": set(),
    "_visit_count": 0,
}

def _load():
    with shelve.open(SAVE_FILE) as db:
        _state["subdomains"] = {k: set(v) for k, v in db.get("subdomains", {}).items()}
        _state["unique_pages"] = set(db.get("unique_pages", set()))

def save():
    with shelve.open(SAVE_FILE) as db:
        db["subdomains"] = {k: list(v) for k, v in _state["subdomains"].items()}
        db["unique_pages"] = list(_state["unique_pages"])
        import analytics_utils
        db["word_freq"], db["longest_page"] = analytics_utils.get_report_data()

"""
def get_report_data():
    return word_freq, longest_page  # whatever they name their variables

"""

def record_subdomain(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.endswith(".uci.edu"):
        _state["subdomains"].setdefault(host, set()).add(url)

def record_visit(url):
    _state["unique_pages"].add(url)
    record_subdomain(url)
    _state["_visit_count"] += 1
    if _state["_visit_count"] % _SAVE_EVERY == 0:
        save()

#run manually after crawl is completely done
# python3 -c "from subdomain_utils import generate_report; generate_report()"

def generate_report(output_file="report.txt"): 
    with shelve.open(SAVE_FILE) as db:
        unique_pages = db.get("unique_pages", set())
        longest_page = db.get("longest_page", ("", 0))
        word_freq = db.get("word_freq", {})
        subdomains = {k: set(v) for k, v in db.get("subdomains", {}).items()}

    with open(output_file, "w") as f:
        f.write(f"1. Unique pages found: {len(unique_pages)}\n\n")
        f.write(f"2. Longest page: {longest_page[0]} ({longest_page[1]} words)\n\n")
        f.write("3. Top 50 most common words:\n")
        for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:50]:
            f.write(f"   {word} - {count}\n")
        f.write("\n4. Subdomains in uci.edu (alphabetical):\n")
        for subdomain in sorted(subdomains):
            f.write(f"   {subdomain}, {len(subdomains[subdomain])}\n")
    
    print(f"Report written to {output_file}")

# call _load in scraper.py, at the beginning