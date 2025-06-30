#!/usr/bin/env python3
"""
Scrapes ImovelWeb pages with *your* absolute XPath pattern and
saves every listing URL to imovelweb_links.csv.

No CSS shortcuts, no heuristic selectors.
"""

import csv
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError

# ---------- tweak here -------------------------------------------------------
START_PAGE = 1          # first page to visit (inclusive)
END_PAGE   = 3          # stop BEFORE this page number
CSV_FILE   = Path("imovelweb_links.csv")
HEADLESS   = False      # flip to True to hide the browser
# -----------------------------------------------------------------------------

BASE_URL_P1 = "https://www.imovelweb.com.br/casas-venda-sao-paulo-sp.html"
BASE_URL_N  = ("https://www.imovelweb.com.br/"
               "casas-venda-sao-paulo-sp-pagina-{}.html")

# your absolute XPath template (note the placeholder for idx)
XPATH_TEMPLATE = ("/html/body/div[1]/div[2]/div/div/div[2]/div[2]/div[2]/"
                  "div[{idx}]/div/div[1]/div[2]/div[1]/div[1]/h3/a")

XPATH_FIRST_CA = ('/html/body/div[1]/div[2]/div/div/div[2]/div[2]/div[2]/div[1]/div/div[1]/div[2]/div[1]/div[1]/h3/a')

def write_row(writer, fh, page_no: int, idx: int, href: str) -> None:
    writer.writerow({"page": page_no, "position": idx, "href": href})
    fh.flush()



def scrape():

    with CSV_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["page", "position", "href"])
        writer.writeheader()


        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=HEADLESS)
            page = browser.new_page(locale="pt-BR")

            for page_no in range(START_PAGE, END_PAGE):
                url = BASE_URL_P1 if page_no == 1 else BASE_URL_N.format(page_no)
                print(f"▶ page {page_no} → {url}")
                page.goto(url, timeout=60_000)

                # quick check: is the very first card present?
                try:
                    page.wait_for_selector(f"xpath={XPATH_FIRST_CA}", timeout=15_000)
                except TimeoutError:
                    print("Timed out waiting for the listing card; "
                        "page structure may have changed.")
                    browser.close()
                    return

                # walk idx until the XPath stops matching
                idx = 1
                while True:
                    xpath = XPATH_TEMPLATE.format(idx=idx)
                    anchor = page.query_selector(f"xpath={xpath}")
                    if not anchor:
                        break  # no more cards on this page
                    href = anchor.get_attribute("href")
                    if href:
                        write_row(writer, fh, page_no, idx, href)
                    idx += 1

                print(f"    ✓ captured {idx-1} links")

            browser.close()

if __name__ == "__main__":
    scrape()
