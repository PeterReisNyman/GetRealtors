import requests
import cloudscraper
from lxml import html

BASE_URL = "https://www.imovelweb.com.br/casas-venda-sao-paulo-sp-pagina-{}.html"


def _fetch(url, headers):
    """Fetch a URL using requests, falling back to cloudscraper on 403."""
    resp = requests.get(url, headers=headers)
    if hasattr(resp, "status_code") and resp.status_code == 403:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, headers=headers)
    return resp


def get_listing_links(pages=3):
    links = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
    }
    for page in range(1, pages + 1):
        url = BASE_URL.format(page)
        print(f"Fetching page {page}: {url}")
        resp = _fetch(url, headers)
        resp.raise_for_status()
        tree = html.fromstring(resp.content)
        index = 1
        while True:
            xpath = f"/html/body/div[1]/div[2]/div/div/div[1]/div[2]/div[2]/div[{index}]/div/div[1]/div[2]/div[1]/div[1]/h3/a"
            nodes = tree.xpath(xpath)
            if not nodes:
                break
            link = nodes[0].get('href')
            if link and link not in links:
                links.append(link)
            index += 1
    return links


def extract_script_content(url, script_index=11):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
    }
    resp = _fetch(url, headers)
    resp.raise_for_status()
    tree = html.fromstring(resp.content)
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
