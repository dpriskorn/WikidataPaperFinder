from unittest import TestCase

from wpf import WPF


class TestWPF(TestCase):
    def test_ask_ai(self):
        wpf = WPF(reference_text="Ruffo, A. (1948). Quad. Nutr. 10, 283.")
        wpf.ask_ai()
        assert wpf.ai_response == {'P1433': 'Quad. Nutr.', 'P304': '283', 'P478': '10', 'P577': '1948'}

    def test_generate_sparql_query(self):
        self.fail()

    def test_is_valid_data(self):
        self.fail()

    def test_search_journal_qid(self):
        wpf = WPF(reference_text="",ai_response={'P1433': 'Quad. Nutr.', 'P304': '283', 'P478': '10', 'P577': '1948'})
        wpf.search_journal_qid()
        assert wpf.journal_qid == "test"

    def test_execute_query(self):
        self.fail()

    def test_run(self):
        self.fail()
