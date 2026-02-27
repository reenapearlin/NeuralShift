from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.models.scraped_case import ScrapedCase
from app.services.precedent_scraper import ScrapedPage, get_or_scrape, scrape_case, search_case_links


class TestPrecedentScraper(unittest.TestCase):
    @patch("app.services.precedent_scraper._fetch_html")
    @patch("app.services.precedent_scraper._is_allowed_by_robots")
    @patch("app.services.precedent_scraper._build_session")
    def test_search_case_links_extracts_doc_urls(
        self,
        mock_build_session: Mock,
        mock_is_allowed: Mock,
        mock_fetch_html: Mock,
    ) -> None:
        mock_build_session.return_value = Mock()
        mock_is_allowed.return_value = True
        mock_fetch_html.return_value = """
            <html><body>
                <a href="/doc/12345/">Case 1</a>
                <a href="/doc/12345/?foo=1">Case 1 duplicate</a>
                <a href="/doc/67890/">Case 2</a>
                <a href="/not-a-case/1">Ignore</a>
            </body></html>
        """

        links = search_case_links("section 138 cheque bounce")

        self.assertEqual(
            links,
            [
                "https://indiankanoon.org/doc/12345/",
                "https://indiankanoon.org/doc/67890/",
            ],
        )

    @patch("app.services.precedent_scraper._fetch_html")
    @patch("app.services.precedent_scraper._fetch_pdf_text")
    @patch("app.services.precedent_scraper._is_allowed_by_robots")
    @patch("app.services.precedent_scraper._build_session")
    def test_scrape_case_extracts_title_and_text(
        self,
        mock_build_session: Mock,
        mock_is_allowed: Mock,
        mock_fetch_pdf_text: Mock,
        mock_fetch_html: Mock,
    ) -> None:
        mock_build_session.return_value = Mock()
        mock_is_allowed.return_value = True
        mock_fetch_pdf_text.return_value = "Extracted PDF legal content"
        mock_fetch_html.return_value = """
            <html>
                <head><title>Sample Judgment</title></head>
                <body>
                    <a href="/doc/12345/?type=pdf">Get PDF</a>
                    <div id="judgments">
                        <p>Cheque was dishonoured due to insufficient funds.</p>
                    </div>
                </body>
            </html>
        """

        result = scrape_case("https://indiankanoon.org/doc/12345/")

        self.assertEqual(result.title, "Sample Judgment")
        self.assertIn("Cheque was dishonoured", result.raw_text)
        self.assertIn("Extracted PDF legal content", result.raw_text)
        self.assertEqual(result.pdf_url, "https://indiankanoon.org/doc/12345/?type=pdf")
        self.assertEqual(result.pdf_text, "Extracted PDF legal content")

    @patch("app.services.precedent_scraper.scrape_case")
    @patch("app.services.precedent_scraper._get_cached_case")
    def test_get_or_scrape_uses_cache(
        self,
        mock_get_cached_case: Mock,
        mock_scrape_case: Mock,
    ) -> None:
        db = Mock()
        cached = ScrapedCase(
            url="https://indiankanoon.org/doc/12345/",
            title="Cached",
            raw_text="Cached text",
            embeddings=[0.1, 0.2],
        )
        mock_get_cached_case.return_value = cached

        result = get_or_scrape(cached.url, db)

        self.assertIs(result, cached)
        mock_scrape_case.assert_not_called()
        db.add.assert_not_called()
        db.commit.assert_not_called()

    @patch("app.services.precedent_scraper.scrape_case")
    @patch("app.services.precedent_scraper._get_cached_case")
    def test_get_or_scrape_scrapes_and_stores_when_missing(
        self,
        mock_get_cached_case: Mock,
        mock_scrape_case: Mock,
    ) -> None:
        db = Mock()
        mock_get_cached_case.return_value = None
        mock_scrape_case.return_value = ScrapedPage(
            url="https://indiankanoon.org/doc/777/",
            title="New Case",
            raw_text="Fresh scraped text",
        )

        result = get_or_scrape("https://indiankanoon.org/doc/777/", db)

        self.assertEqual(result.url, "https://indiankanoon.org/doc/777/")
        self.assertEqual(result.title, "New Case")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()


if __name__ == "__main__":
    unittest.main()
