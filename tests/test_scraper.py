import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import scraper
from lxml import etree
from types import SimpleNamespace
from unittest import mock


def build_sample_page(num_links=2):
    """Build HTML with anchors located at the expected xpath."""
    def ensure_child(parent, tag, index=None):
        if index is None:
            child = etree.SubElement(parent, tag)
            return child
        existing = [c for c in parent if c.tag == tag]
        while len(existing) < index:
            etree.SubElement(parent, tag)
            existing = [c for c in parent if c.tag == tag]
        return existing[index - 1]

    root = etree.Element("html")
    body = etree.SubElement(root, "body")
    for i in range(1, num_links + 1):
        parent = body
        path = [
            ("div", 1),
            ("div", 2),
            ("div", None),
            ("div", None),
            ("div", 1),
            ("div", 2),
            ("div", 2),
            ("div", i),
            ("div", None),
            ("div", 1),
            ("div", 2),
            ("div", 1),
            ("div", 1),
            ("h3", None),
            ("a", None),
        ]
        for tag, idx in path:
            parent = ensure_child(parent, tag, idx)
        parent.set("href", f"link{i}.html")
        parent.text = f"Link {i}"
    return etree.tostring(root, encoding="utf-8")


def build_listing_page(script_text="DATA"):
    root = etree.Element("html")
    head = etree.SubElement(root, "head")
    for i in range(1, 12):
        s = etree.SubElement(head, "script")
        s.text = f"script {i}"
    head.xpath("//script[11]")[0].text = script_text
    return etree.tostring(root, encoding="utf-8")


class FakeResponse(SimpleNamespace):
    def raise_for_status(self):
        pass


def test_get_listing_links():
    html_bytes = build_sample_page(num_links=2)
    with mock.patch("requests.get") as m:
        m.return_value = FakeResponse(content=html_bytes)
        links = scraper.get_listing_links(pages=1)
        assert links == ["link1.html", "link2.html"]


def test_extract_script_content():
    html_bytes = build_listing_page(script_text="hello world")
    with mock.patch("requests.get") as m:
        m.return_value = FakeResponse(content=html_bytes)
        text = scraper.extract_script_content("dummy")
        assert "hello world" in text

