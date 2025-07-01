#!/usr/bin/env python3
"""
Read listing URLs from imovelweb_links.csv, visit each page once, extract the
rich JSON-LD block in <head> along with the imobiliária name, and append the
requested fields to imovelweb_details.csv (one row per listing). URLs already
present in the CSV are skipped.
"""

import csv, json, re, time
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError

# ────────── config ──────────
LINKS_CSV   = Path("imovelweb_links.csv")
OUTPUT_CSV  = Path("imovelweb_details.csv")
HEADLESS    = False
BASE        = "https://www.imovelweb.com.br"
PAGE_WAIT   = 15_000
# ────────────────────────────


def load_links() -> list[str]:
    with LINKS_CSV.open(newline="", encoding="utf-8") as fh:
        return [row["href"] for row in csv.DictReader(fh)]


def load_processed() -> set[str]:
    """Return URLs already saved to OUTPUT_CSV, if file exists."""
    if not OUTPUT_CSV.exists():
        return set()
    with OUTPUT_CSV.open(newline="", encoding="utf-8") as fh:
        return {row["url"] for row in csv.DictReader(fh)}


def extract_jsonld(html: str) -> dict | None:
    """Return the first JSON dict that has `"telephone"`."""
    for m in re.finditer(
        r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>',
        html,
        re.S | re.I,
    ):
        try:
            data = json.loads(m.group(1))
            if isinstance(data, dict) and data.get("telephone"):
                return data
        except json.JSONDecodeError:
            continue
    return None


def format_row(d: dict, url: str, imobiliaria: str) -> dict:
    """Return a flat dict with the columns we want."""
    addr = d.get("address", {})
    if isinstance(addr, dict):
        address = ", ".join(
            x
            for x in [
                addr.get("streetAddress", ""),
                addr.get("addressLocality", ""),
                addr.get("addressRegion", ""),
            ]
            if x
        )
    else:
        address = ""

    return {
        "url": url,
        "telephone": d.get("telephone", ""),
        "name": d.get("name", ""),
        "atype": d.get("@type", ""),
        "description": d.get("description", ""),
        "numberOfRooms": d.get("numberOfRooms", ""),
        "floorSize": (
            d.get("floorSize", {}).get("value", "")
            if isinstance(d.get("floorSize"), dict)
            else ""
        ),
        "numberOfBathroomsTotal": d.get("numberOfBathroomsTotal", ""),
        "numberOfBedrooms": d.get("numberOfBedrooms", ""),
        "address": address,
        "imobiliaria": imobiliaria,
    }


def main() -> None:
    links = load_links()
    print(f"Loaded {len(links)} hrefs")

    processed = load_processed()
    if processed:
        print(f"{len(processed)} URLs already saved; will skip them")

    header = [
        "url",
        "telephone",
        "name",
        "atype",
        "description",
        "numberOfRooms",
        "floorSize",
        "numberOfBathroomsTotal",
        "numberOfBedrooms",
        "address",
        "imobiliaria",
    ]

    with OUTPUT_CSV.open("a", newline="", encoding="utf-8") as out_fh:
        writer = csv.DictWriter(out_fh, fieldnames=header)
        if out_fh.tell() == 0:
            writer.writeheader()

        with sync_playwright() as pw:

            for n, href in enumerate(links, 1):
                url = href if href.startswith("http") else urljoin(BASE, href)
                if url in processed:
                    print(f"[{n}/{len(links)}] {url} → skipping (already saved)")
                    continue
                print(f"[{n}/{len(links)}] {url}")
                browser = pw.chromium.launch(headless=HEADLESS)
                page = browser.new_page(locale="pt-BR")
                page.goto(url, timeout=60_000, wait_until="domcontentloaded")

                html = page.content()
                data = extract_jsonld(html)

                imobiliaria_el = page.query_selector(
                    "xpath=/html/body/div[2]/main/div/div/article/div/section[5]/div/div[1]/div/div[2]/h3"
                )
                imobiliaria = (
                    imobiliaria_el.inner_text().strip() if imobiliaria_el else ""
                )

                if data:
                    writer.writerow(format_row(data, url, imobiliaria))
                    out_fh.flush()
                    processed.add(url)
                    print("    ✓ saved row")
                else:
                    print("    … JSON-LD with telephone not found")

                browser.close()

                time.sleep(1.2)  # friendly delay

    print(f"\n💾 details saved to {OUTPUT_CSV.resolve()}")


if __name__ == "__main__":
    main()
