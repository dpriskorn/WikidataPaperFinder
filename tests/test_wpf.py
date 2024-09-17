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
                "P304": "233",
                "P478": "176",
                "P577": "1948",
            },
            journal_qid="Q27714801",
        )
        wpf.generate_sparql_query()
        assert wpf.sparql_query == ('\n'
 '        SELECT ?article ?articleLabel ?volume ?pages ?publicationDate WHERE '
 '{\n'
 '          BIND ( wd:Q27714801 AS ?journal ) .\n'
 '          BIND ( 1948 AS ?year ) .\n'
 '          BIND ( "176" AS ?volume ) .\n'
 '          BIND ( 233 AS ?startPage ) .\n'
 '          BIND ( 15 AS ?range ) .\n'
 '          \n'
 '          ?article wdt:P1433 ?journal; wdt:P478 ?volume; wdt:P304 ?pages; '
 'wdt:P577 ?publicationDate .\n'
 '        \n'
 '          FILTER( YEAR( ?publicationDate ) = ?year ) .\n'
 '          BIND( REPLACE( ?pages,"(\\\\d*).*","$1" ) AS ?start ) .\n'
 '          FILTER( ( xsd:integer(?start) < ?startPage + ?range ) && ( '
 'xsd:integer(?start) > ?startPage - ?range ) ) .\n'
 '          \n'
 '          SERVICE wikibase:label { bd:serviceParam wikibase:language '
 '"[AUTO_LANGUAGE],mul,en" . }\n'
 '        }\n'
 '        ORDER BY ASC(xsd:integer(?start))\n'
 '        ')

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

    def test_search_journal_qid_quad_nutr(self):
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

    def test_search_journal_qid_jchemsoc(self):
        wpf = WPF(
            reference_text="",
            ai_response={'P1433': 'J. Chem. Soc.', 'P577': '1947', 'P478': '25', 'P304': '1141–1145'},
        )
        wpf.search_journal_qid()
        assert wpf.journal_qid == "Q903605"

    def test_execute_query(self):
        wpf = WPF(
            reference_text="",
            ai_response={
                "P1433": "Quad. Nutr.",
                "P304": "233",
                "P478": "176",
                "P577": "1948",
            },
            journal_qid="Q27714801",
        )
        wpf.generate_sparql_query()
        print(wpf.sparql_query)
        wpf.execute_query()
        assert wpf.query_result == {'head': {'vars': ['article',
                   'articleLabel',
                   'volume',
                   'pages',
                   'publicationDate']},
 'results': {'bindings': [{'article': {'type': 'uri',
                                       'value': 'http://www.wikidata.org/entity/Q79486492'},
                           'articleLabel': {'type': 'literal',
                                            'value': 'The inactivation of '
                                                     'streptomycin by cyanate',
                                            'xml:lang': 'en'},
                           'pages': {'type': 'literal', 'value': '223-228'},
                           'publicationDate': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime',
                                               'type': 'literal',
                                               'value': '1948-10-01T00:00:00Z'},
                           'volume': {'type': 'literal', 'value': '176'}},
                          {'article': {'type': 'uri',
                                       'value': 'http://www.wikidata.org/entity/Q79486497'},
                           'articleLabel': {'type': 'literal',
                                            'value': 'The reduction of '
                                                     'cozymase by sodium '
                                                     'borohydride',
                                            'xml:lang': 'en'},
                           'pages': {'type': 'literal', 'value': '229-232'},
                           'publicationDate': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime',
                                               'type': 'literal',
                                               'value': '1948-10-01T00:00:00Z'},
                           'volume': {'type': 'literal', 'value': '176'}},
                          {'article': {'type': 'uri',
                                       'value': 'http://www.wikidata.org/entity/Q79486503'},
                           'articleLabel': {'type': 'literal',
                                            'value': 'Carbohydrate metabolism '
                                                     'in higher plants; pea '
                                                     'aldolase',
                                            'xml:lang': 'en'},
                           'pages': {'type': 'literal', 'value': '233-241'},
                           'publicationDate': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime',
                                               'type': 'literal',
                                               'value': '1948-10-01T00:00:00Z'},
                           'volume': {'type': 'literal', 'value': '176'}},
                          {'article': {'type': 'uri',
                                       'value': 'http://www.wikidata.org/entity/Q79486509'},
                           'articleLabel': {'type': 'literal',
                                            'value': 'The effect of '
                                                     'crystalline adrenal '
                                                     'cortical steroids, '
                                                     'di-thyroxine, and '
                                                     'epinephrine on the '
                                                     'alkaline and acid '
                                                     'phosphatases and '
                                                     'arginase of the liver '
                                                     'and kidney of the normal '
                                                     'adult rat',
                                            'xml:lang': 'en'},
                           'pages': {'type': 'literal', 'value': '243-247'},
                           'publicationDate': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime',
                                               'type': 'literal',
                                               'value': '1948-10-01T00:00:00Z'},
                           'volume': {'type': 'literal', 'value': '176'}}]}}

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


    def test_run_1(self):
        # random reference from wikipedia, see https://en.wikipedia.org/wiki/Molecular_Structure_of_Nucleic_Acids:_A_Structure_for_Deoxyribose_Nucleic_Acid
        wpf = WPF(reference_text="Creeth, J.M., Gulland, J.M. and Jordan, D.O. (1947) Deoxypentose nucleic acids. Part III. Viscosity and streaming birefringence of solutions of the sodium salt of the deoxypentose nucleic acid of calf thymus. J. Chem. Soc. 1947,25 1141–1145")
        wpf.ask_ai()
        assert wpf.ai_response == {'P1433': 'J. Chem. Soc.', 'P304': '1141–1145', 'P478': '25', 'P577': '1947'}
        #exit()
        wpf.search_journal_qid()
        assert wpf.journal_qid == "Q903605"
        #exit()
        wpf.generate_sparql_query()
        assert wpf.sparql_query == ('\n'
 '        SELECT ?article ?articleLabel ?volume ?pages ?publicationDate WHERE '
 '{\n'
 '          BIND ( wd:Q903605 AS ?journal ) .\n'
 '          BIND ( 1947 AS ?year ) .\n'
 '          BIND ( "25" AS ?volume ) .\n'
 '          BIND ( 1141 AS ?startPage ) .\n'
 '          BIND ( 15 AS ?range ) .\n'
 '          \n'
 '          ?article wdt:P1433 ?journal; wdt:P478 ?volume; wdt:P304 ?pages; '
 'wdt:P577 ?publicationDate .\n'
 '        \n'
 '          FILTER( YEAR( ?publicationDate ) = ?year ) .\n'
 '          BIND( REPLACE( ?pages,"(\\\\d*).*","$1" ) AS ?start ) .\n'
 '          FILTER( ( xsd:integer(?start) < ?startPage + ?range ) && ( '
 'xsd:integer(?start) > ?startPage - ?range ) ) .\n'
 '          \n'
 '          SERVICE wikibase:label { bd:serviceParam wikibase:language '
 '"[AUTO_LANGUAGE],mul,en" . }\n'
 '        }\n'
 '        ORDER BY ASC(xsd:integer(?start))\n'
 '        ')
        wpf.execute_query()
        print(wpf.wdqs_query_link())
        assert wpf.query_result == {'head': {'vars': ['article',
                   'articleLabel',
                   'volume',
                   'pages',
                   'publicationDate']},
 'results': {'bindings': [{'article': {'type': 'uri',
                                       'value': 'http://www.wikidata.org/entity/Q79596662'},
                           'articleLabel': {'type': 'literal',
                                            'value': 'Deoxypentose nucleic '
                                                     'acids; preparation of '
                                                     'the tetrasodium salt of '
                                                     'the deoxypentose nucleic '
                                                     'acid of calf thymus',
                                            'xml:lang': 'en'},
                           'pages': {'type': 'literal', 'value': '1129'},
                           'publicationDate': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime',
                                               'type': 'literal',
                                               'value': '1947-09-01T00:00:00Z'},
                           'volume': {'type': 'literal', 'value': '25'}},
                          {'article': {'type': 'uri',
                                       'value': 'http://www.wikidata.org/entity/Q79596665'},
                           'articleLabel': {'type': 'literal',
                                            'value': 'Deoxypentose nucleic '
                                                     'acids; electrometric '
                                                     'titration of the acidic '
                                                     'and the basic groups of '
                                                     'the deoxypentose nucleic '
                                                     'acid of calf thymus',
                                            'xml:lang': 'en'},
                           'pages': {'type': 'literal', 'value': '1131-1141'},
                           'publicationDate': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime',
                                               'type': 'literal',
                                               'value': '1947-09-01T00:00:00Z'},
                           'volume': {'type': 'literal', 'value': '25'}},
                          {'article': {'type': 'uri',
                                       'value': 'http://www.wikidata.org/entity/Q79596669'},
                           'articleLabel': {'type': 'literal',
                                            'value': 'Deoxypentose nucleic '
                                                     'acids; viscosity and '
                                                     'streaming birefringence '
                                                     'of solutions of the '
                                                     'sodium salt of the '
                                                     'deoxypentose nucleic '
                                                     'acid of calf thymus',
                                            'xml:lang': 'en'},
                           'pages': {'type': 'literal', 'value': '1141-1145'},
                           'publicationDate': {'datatype': 'http://www.w3.org/2001/XMLSchema#dateTime',
                                               'type': 'literal',
                                               'value': '1947-09-01T00:00:00Z'},
                           'volume': {'type': 'literal', 'value': '25'}}]}}
        assert wpf.run() == "Success, results were found"
