import pytest
from unittest.mock import patch

# Mock class to simulate WPF object
class MockWPF_without_results:
    def __init__(self):
        self.query_result = {}
        self.journal_label_en = 'Example Journal'
        self.wikidata_journal_link = 'http://www.wikidata.org/entity/Q12345'
        self.wdqs_query_link = lambda: 'http://example.com/sparql-query'

    def run(self):
        return "testing"

class MockWPF_with_results:
    def __init__(self):
        self.query_result = {
            'head': {'vars': ['article', 'articleLabel', 'volume', 'pages', 'publicationDate']},
            'results': {
                'bindings': [
                    {
                        'article': {'value': 'http://www.wikidata.org/entity/Q79486492'},
                        'articleLabel': {'value': 'The inactivation of streptomycin by cyanate'},
                        'pages': {'value': '223-228'},
                        'publicationDate': {'value': '1948-10-01'},
                        'volume': {'value': '176'}
                    }
                ]
            }
        }
        self.journal_label_en = 'Example Journal'
        self.wikidata_journal_link = 'http://www.wikidata.org/entity/Q12345'
        self.wdqs_query_link = lambda: 'http://example.com/sparql-query'

    def run(self):
        return "testing"


@pytest.fixture
def mock_wpf_with_result():
    with patch('app.WPF', autospec=True) as mock:
        mock.return_value = MockWPF_with_results()
        yield mock

@pytest.fixture
def mock_wpf_without_result():
    with patch('app.WPF', autospec=True) as mock:
        mock.return_value = MockWPF_without_results()
        yield mock

def test_search_route_with_results(client, mock_wpf_with_result):
    # Simulate a GET request to the /search route
    response = client.get('/search', query_string={'reference_text': 'some reference'})
    print(response.text)
    # exit()
    # Check if the response contains the rendered template
    assert b'WDQS Results' in response.data
    assert b'The inactivation of streptomycin by cyanate' in response.data
    assert b'Example Journal' in response.data
    assert b'http://example.com/sparql-query' in response.data

def test_search_route_without_results(client, mock_wpf_without_result):
    # Simulate a GET request to the /search route
    response = client.get('/search', query_string={'reference_text': 'some reference'})
    print(response.text)
    # exit()
    # Check if the response contains the rendered template
    assert b'WDQS Results' in response.data
    #assert b'The inactivation of streptomycin by cyanate' in response.data
    assert b'Example Journal' in response.data
    assert b'http://example.com/sparql-query' in response.data
