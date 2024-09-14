import logging
from unittest import TestCase

import config
from wpf import WPF

logging.basicConfig(level=config.loglevel)


class TestWPF(TestCase):
    def test_ask_ai(self):
        wpf = WPF(reference_text="Ruffo, A. (1948). Quad. Nutr. 10, 283.")
        wpf.ask_ai()
        assert wpf.ai_response == {
            "P1433": "Quad. Nutr.",
            "P304": "283",
            "P478": "10",
            "P577": "1948",
        }

    def test_generate_sparql_query(self):
        wpf = WPF(
            reference_text="",
            ai_response={
                "P1433": "Quad. Nutr.",
                "P304": "283",
                "P478": "10",
                "P577": "1948",
            },
            journal_qid="Q27714801",
        )
        wpf.generate_sparql_query()
        assert wpf.sparql_query == (
            "\n"
            "        SELECT ?article ?articleLabel ?volume ?pages ?publicationDate WHERE "
            "{\n"
            "          BIND (1948 AS ?year )\n"
            '          BIND ("10" AS ?volume )\n'
            '          BIND (SUBSTR("283", 1, 3) AS ?startPage )\n'
            "\n"
            "          ?article wdt:P1433 wd:Q27714801;  # article is published in the "
            "specified journal\n"
            "                   wdt:P478 ?volume;      # article has volume\n"
            "                   wdt:P304 ?pages;       # article has pages\n"
            "                   wdt:P577 ?publicationDate.  # article has publication "
            "date\n"
            "\n"
            "          # Filter for the year, volume, and first 3 characters of the "
            "pages\n"
            "          FILTER(YEAR(?publicationDate) = ?year)  # Specify the year\n"
            "          FILTER(SUBSTR(?pages, 1, STRLEN(?startPage)) = ?startPage)   # "
            "Match first 3 characters of pages\n"
            "\n"
            "          # Return labels for articles and journals\n"
            "          SERVICE wikibase:label { bd:serviceParam wikibase:language "
            '"[AUTO_LANGUAGE],en". }\n'
            "        }\n"
            "        LIMIT 100\n"
            "        "
        )

    def test_is_valid_data(self):
        wpf = WPF(
            reference_text="",
            ai_response={
                "P1433": "Quad. Nutr.",
                "P304": "283",
                "P478": "10",
                "P577": "1948",
            },
        )
        assert wpf.is_valid_data() is True

    def test_search_journal_qid(self):
        wpf = WPF(
            reference_text="",
            ai_response={
                "P1433": "Quad. Nutr.",
                "P304": "283",
                "P478": "10",
                "P577": "1948",
            },
        )
        wpf.search_journal_qid()
        assert wpf.journal_qid == "Q27714801"

    def test_execute_query(self):
        wpf = WPF(
            reference_text="",
            ai_response={
                "P1433": "Quad. Nutr.",
                "P304": "283",
                "P478": "10",
                "P577": "1948",
            },
            journal_qid="Q27714801",
            sparql_query=(
                "\n"
                "        SELECT ?article ?articleLabel ?volume ?pages ?publicationDate WHERE "
                "{\n"
                "          BIND (1948 AS ?year )\n"
                '          BIND ("10" AS ?volume )\n'
                '          BIND (SUBSTR("283", 1, 3) AS ?startPage )\n'
                "\n"
                "          ?article wdt:P1433 wd:Q27714801;  # article is published in the "
                "specified journal\n"
                "                   wdt:P478 ?volume;      # article has volume\n"
                "                   wdt:P304 ?pages;       # article has pages\n"
                "                   wdt:P577 ?publicationDate.  # article has publication "
                "date\n"
                "\n"
                "          # Filter for the year, volume, and first 3 characters of the "
                "pages\n"
                "          FILTER(YEAR(?publicationDate) = ?year)  # Specify the year\n"
                "          FILTER(SUBSTR(?pages, 1, STRLEN(?startPage)) = ?startPage)   # "
                "Match first 3 characters of pages\n"
                "\n"
                "          # Return labels for articles and journals\n"
                "          SERVICE wikibase:label { bd:serviceParam wikibase:language "
                '"[AUTO_LANGUAGE],en". }\n'
                "        }\n"
                "        LIMIT 100\n"
                "        "
            ),
        )
        wpf.execute_query()
        assert wpf.query_result == "test"

    def test_empty_result(self):
        empty_result = {
            "head": {
                "vars": [
                    "article",
                    "articleLabel",
                    "volume",
                    "pages",
                    "publicationDate",
                ]
            },
            "results": {"bindings": []},
        }
        wpf = WPF(reference_text="",ai_response={'P1433': 'Quad. Nutr.', 'P304': '283', 'P478': '10', 'P577': '1948'}, query_result=empty_result)
        assert wpf.empty_result is True


    def test_run(self):
        self.fail()
