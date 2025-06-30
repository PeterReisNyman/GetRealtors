import json
import time
from urllib.parse import urljoin

import cloudscraper
from lxml import html

# Reuse one Cloudflare-aware scraper session for all requests
SCRAPER = cloudscraper.create_scraper()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

BASE_URL = "https://www.imovelweb.com.br/casas-venda-sao-paulo-sp-pagina-{}.html"


def _fetch(url, headers=HEADERS):
    """Fetch a URL using a persistent cloudscraper session."""
    resp = SCRAPER.get(url, headers=headers)
    print(resp.url, resp.status_code, len(resp.text))
    return resp


def get_listing_links(pages=3):
    """Collect listing URLs from the paginated results."""
    links = []
    for page in range(1, pages + 1):
        url = BASE_URL.format(page)
        print(f"Fetching page {page}: {url}")
        resp = _fetch(url, HEADERS)
        resp.raise_for_status()
        tree = html.fromstring(resp.text)

        found = False
        for a in tree.cssselect("article h3 a[href]"):
            href = a.get("href")
            if href and href not in links:
                links.append(urljoin(url, href))
                found = True

        if not found:
            script_nodes = tree.xpath('//script[@id="__NUXT__" or @id="__NEXT_DATA__"]/text()')
            if script_nodes:
                try:
                    data = json.loads(script_nodes[0])
                    adverts = data.get("data", [{}])[0].get("adverts", [])
                    for advert in adverts:
                        href = advert.get("url") or advert.get("ad_url")
                        if href and href not in links:
                            links.append(href)
                except Exception:
                    pass

        time.sleep(1)
    return links


def extract_script_content(url, script_index=11):
    resp = _fetch(url, HEADERS)
    resp.raise_for_status()
    tree = html.fromstring(resp.text)
    xpath = f"/html/head/script[{script_index}]"
    nodes = tree.xpath(xpath)
    if nodes:
        return nodes[0].text_content()
    return ""


def main():
    links = get_listing_links(3)
    print(f"Collected {len(links)} listing links")
    data = []
    for link in links:
        print(f"Fetching listing: {link}")
        content = extract_script_content(link)
        data.append({"url": link, "script": content})
    for item in data:
        print(f"URL: {item['url']}")
        print(f"Script:\n{item['script'][:200]}...\n")


if __name__ == "__main__":
    main()
