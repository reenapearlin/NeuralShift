from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from app.services.precedent_service import get_precedent_view, search_precedents


class _Row:
    def __init__(self, url: str, title: str, raw_text: str, embeddings=None) -> None:
        self.url = url
        self.title = title
        self.raw_text = raw_text
        self.embeddings = embeddings


class _FakeEmbeddingModel:
    def embed_query(self, query: str) -> list[float]:
        if "cheque" in query.lower():
            return [1.0, 0.0]
        return [0.0, 1.0]

    def embed_documents(self, chunks: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for chunk in chunks:
            if "cheque" in chunk.lower():
                vectors.append([0.9, 0.1])
            else:
                vectors.append([0.1, 0.9])
        return vectors


class TestPrecedentService(unittest.TestCase):
    @patch("app.services.precedent_service.get_embedding_model")
    @patch("app.services.precedent_service.get_or_scrape")
    @patch("app.services.precedent_service.search_case_links")
    def test_ranks_results_by_similarity(
        self,
        mock_search_links: Mock,
        mock_get_or_scrape: Mock,
        mock_get_embedding_model: Mock,
    ) -> None:
        db = Mock()
        mock_search_links.return_value = [
            "https://indiankanoon.org/doc/1/",
            "https://indiankanoon.org/doc/2/",
        ]
        rows = {
            "https://indiankanoon.org/doc/1/": _Row(
                url="https://indiankanoon.org/doc/1/",
                title="Cheque Dishonour Judgment",
                raw_text="This case discusses cheque dishonour liability.",
                embeddings=None,
            ),
            "https://indiankanoon.org/doc/2/": _Row(
                url="https://indiankanoon.org/doc/2/",
                title="Unrelated Property Dispute",
                raw_text="This case is about property boundaries.",
                embeddings=None,
            ),
        }
        mock_get_or_scrape.side_effect = lambda url, db: rows[url]
        mock_get_embedding_model.return_value = _FakeEmbeddingModel()

        response = search_precedents(db=db, query="cheque bounce limitation", top_n=2)

        self.assertEqual(response["query"], "cheque bounce limitation")
        self.assertEqual(len(response["results"]), 2)
        self.assertGreaterEqual(response["results"][0]["score"], response["results"][1]["score"])
        self.assertEqual(response["results"][0]["title"], "Cheque Dishonour Judgment")
        self.assertTrue(db.commit.called)

    @patch("app.services.precedent_service.search_case_links")
    def test_returns_empty_when_no_links(self, mock_search_links: Mock) -> None:
        db = Mock()
        mock_search_links.return_value = []

        response = search_precedents(db=db, query="section 138", top_n=5)

        self.assertEqual(response["query"], "section 138")
        self.assertEqual(response["results"], [])

    @patch("app.services.precedent_service.get_embedding_model")
    @patch("app.services.precedent_service.extract_legal_keywords")
    @patch("app.services.precedent_service.generate_structured_report")
    @patch("app.services.precedent_service.generate_summary")
    @patch("app.services.precedent_service.scrape_case")
    def test_precedent_view_prefers_pdf_text_for_generation(
        self,
        mock_scrape_case: Mock,
        mock_generate_summary: Mock,
        mock_generate_structured_report: Mock,
        mock_extract_legal_keywords: Mock,
        mock_get_embedding_model: Mock,
    ) -> None:
        db = Mock()
        fake_query = Mock()
        fake_query.first.return_value = None
        db.query.return_value.filter.return_value = fake_query

        mock_scrape_case.return_value = Mock(
            url="https://indiankanoon.org/doc/12345/",
            title="Sample PDF Case",
            raw_text="HTML case text",
            pdf_url="https://indiankanoon.org/doc/12345/?type=pdf",
            pdf_text="PDF text with cheque dishonour and section 138 analysis",
        )
        mock_generate_summary.return_value = "Facts: ...\nLegal Issue: ..."
        mock_generate_structured_report.return_value = {
            "case_title": "Sample PDF Case",
            "court": "Not Specified",
            "legal_issue": "Not Specified",
            "relevant_sections": ["Section 138"],
            "limitation_analysis": "Not Specified",
            "penalty": "Not Specified",
            "judgement": "Not Specified",
            "key_principles": ["Dishonour of cheque"],
        }
        mock_extract_legal_keywords.return_value = ["Section 138", "Dishonour Of Cheque"]
        mock_get_embedding_model.return_value = _FakeEmbeddingModel()

        payload = get_precedent_view(db=db, url="https://indiankanoon.org/doc/12345/")

        self.assertEqual(payload["case_title"], "Sample PDF Case")
        self.assertEqual(payload["pdf_path"], "https://indiankanoon.org/doc/12345/?type=pdf")
        self.assertEqual(payload["key_points"], ["Section 138", "Dishonour Of Cheque"])
        self.assertEqual(payload["highlighted_keywords"], ["Section 138", "Dishonour Of Cheque"])
        self.assertEqual(payload["source_url"], "https://indiankanoon.org/doc/12345/")
        self.assertTrue(db.add.called)
        self.assertTrue(db.commit.called)


if __name__ == "__main__":
    unittest.main()
