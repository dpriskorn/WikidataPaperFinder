import json
import logging
from urllib.parse import quote

from duckduckgo_search import DDGS
from pydantic import BaseModel
from wikibaseintegrator.wbi_helpers import search_entities, execute_sparql_query

logger = logging.getLogger(__name__)


class WPF(BaseModel):
    reference_text: str
    ai_response: dict = {}
    journal_qid: str = ""
    journal_label_en: str = ""
    journal_name: str = ""
    year: int = 0
    volume: str = ""
    pages: str = ""
    start_page: str = ""
    sparql_query: str = ""
    query_result: dict = {}
    status: str = ""
    query_executed: bool = False
    wdqs_base_url: str = "https://query.wikidata.org/#"

    def ask_ai(self):
        ddgs = DDGS()
        prompt = (
            "Please extract the title, journal, year, volume, and page number from this reference in a paper "
            "and give me the result as an one line unformatted JSON object with the keys ['title', 'journal', 'year', 'volume', 'pages'], "
            "don't format as time, just return strings or empty strings. Copy the journal name verbatim, only output the JSON: "
            f'"{self.reference_text}"'
        )
        text = ddgs.chat(
            prompt, model="gpt-4o-mini"
        )  # You can change the model as needed
        text = text.replace("json", "").strip()
        logger.debug(text)
        try:
            # Attempt to parse the JSON response
            self.ai_response = json.loads(text)
        except json.JSONDecodeError:
            self.ai_response = {"error": "Failed to parse JSON from response"}
        if not self.is_valid_data():
            self.status = f"Got invalid data form AI. Required fields: journal, year, volume, pages. '{self.ai_response}'"

    def generate_full_sparql_query(self) -> None:
        if (
            not self.journal_qid
            or not self.year
            or not self.volume
            or not self.start_page
        ):
            self.status = "Missing data."
            return
        self.sparql_query = f"""
        SELECT 
          ?article 
          ?articleLabel 
          ?volume 
          ?pages 
          ?publicationDate 
          (GROUP_CONCAT(?authorName; separator="; ") AS ?authorNames) 
          # authorLabel should be auto-populated by the label service 
          (GROUP_CONCAT(?authorLabel; separator="; ") AS ?authorLabels)
        WHERE {{
          BIND ( wd:{self.journal_qid} AS ?journal ) .
          BIND ( {self.year} AS ?year ) .
          BIND ( "{self.volume}" AS ?volume ) .
          BIND ( {self.start_page} AS ?startPage ) .
          BIND ( 15 AS ?range ) .

          ?article wdt:P1433 ?journal; wdt:P478 ?volume; wdt:P304 ?pages; wdt:P577 ?publicationDate .

          OPTIONAL {{ ?article wdt:P2093 ?authorName . }}  # Author name string (P2093)
          OPTIONAL {{ ?article wdt:P50 ?author . }}       # Author (P50)

          FILTER( YEAR( ?publicationDate ) = ?year ) .
          BIND( REPLACE( ?pages,"(\\\\d*).*","$1" ) AS ?start ) .
          FILTER( ( xsd:integer(?start) < ?startPage + ?range ) && ( xsd:integer(?start) > ?startPage - ?range ) ) .

          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en" . }}
        }}
        GROUP BY ?article ?articleLabel ?volume ?pages ?publicationDate
        ORDER BY ASC(xsd:integer(?start))
        """

    @property
    def generate_year_volume_sparql_query(self) -> str:
        """This is only used as a url so we don't store it in the object for now"""
        if (
                not self.journal_qid
                or not self.year
                or not self.volume
        ):
            self.status = "Missing data."
            return ""
        return f"""
        SELECT ?article ?articleLabel ?volume ?pages ?publicationDate WHERE {{
          BIND ( wd:{self.journal_qid} AS ?journal ) .
          BIND ( {self.year} AS ?year ) .
          BIND ( "{self.volume}" AS ?volume ) .

          ?article wdt:P1433 ?journal; wdt:P478 ?volume; wdt:P304 ?pages; wdt:P577 ?publicationDate .

          FILTER( YEAR( ?publicationDate ) = ?year ) .

          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en" . }}
        }}
        ORDER BY ASC(xsd:integer(?pages))
        """

    def is_valid_data(self):
        """Check if the required fields are present in the data."""
        required_fields = ["journal", "year", "volume", "pages"]
        return all(field in self.ai_response for field in required_fields)

    def extract_journal_name(self):
        self.journal_name = self.ai_response.get("journal", "")
        if not self.journal_name:
            self.status = "Got no journal name from the AI"
            return

    def extract_year(self):
        self.year = int(self.ai_response.get("year", ""))
        if not self.year:
            self.status = "Got no year from the AI"
            return

    def extract_volume(self):
        self.volume = self.ai_response.get("volume", "")
        if not self.volume:
            self.status = "Got no volume from the AI"
            return

    def extract_pages(self):
        # Handle weird unicode
        self.pages = self.ai_response.get("pages", "").replace("\u2013", "-")
        if not self.pages:
            self.status = "Got no pages from the AI"
            return

    def extract_ai_response(self):
        """Helper method to extract the data we need"""
        self.extract_journal_name()
        self.extract_year()
        self.extract_volume()
        self.extract_pages()
        self.extract_start_page()

    def extract_start_page(self):
        if self.pages:
            if "-" in self.pages:
                self.start_page = self.pages.split("-")[0]
                logger.info("Split pages along '-'")
            else:
                self.start_page = self.pages

    def search_journal_qid(self):
        if self.journal_name:
            search_results = search_entities(
                search_string=self.journal_name, search_type="item", dict_result=True
            )
            if not search_results:
                logger.error(f"No journal QID found for name {self.journal_name}")
                return
            # print(search_results)
            # Extract QID from search results
            if search_results and isinstance(search_results, list):
                logger.debug("got search results")
                for result in search_results:
                    if (
                        "id" in result
                        and "label" in result
                        and result["label"].lower() == self.journal_name.lower()
                        or result["match"]["text"].lower() == self.journal_name.lower()
                    ):
                        logger.debug(f'found match: {result["id"]}')
                        self.journal_qid = result["id"]  # Return the QID of the journal
                        self.journal_label_en = result["label"]
        else:
            logger.error("no journal_name")

    def execute_query(self):
        """Execute the SPARQL query and return the result."""
        result = execute_sparql_query(
            query=self.sparql_query,
            prefix=None,
            endpoint=None,
            user_agent=None,
            max_retries=1000,
            retry_after=60,
        )
        self.query_result = result
        self.query_executed = True

    def run(self) -> None:
        """Run all the methods and store the status"""
        # Step: Ask the AI for the reference details
        if not self.ai_response:
            self.ask_ai()

        # Step: Extract data
        self.extract_ai_response()

        # Step: Find the journal QID
        if not self.journal_qid:
            self.search_journal_qid()
            if not self.journal_qid:
                self.status = (
                    f"Journal QID not found for '{self.ai_response.get('P1433', '')}'"
                )

        # Step: Generate the SPARQL query
        if not self.sparql_query:
            self.generate_full_sparql_query()
            if not self.sparql_query:
                self.status += " Could not generate sparql query"

        # Step: Execute the SPARQL query
        if self.sparql_query and not self.query_result:
            logger.info("Running query and reporting status")
            self.execute_query()
        if self.query_executed:
            if self.empty_result:
                self.status = "Got empty result from WDQS"
            else:
                self.status = "Success, results were found"

    @property
    def empty_result(self):
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
        if not self.query_result or self.query_result == empty_result:
            return True
        return False

    @property
    def wdqs_full_query_link(self):
        if self.sparql_query:
            return f"{self.wdqs_base_url}{quote(self.sparql_query)}"
        else:
            return ""

    @property
    def wikidata_journal_link(self) -> str:
        if self.journal_qid:
            return f"https://wikidata.org/wiki/{self.journal_qid}"
        else:
            return ""

    @property
    def wdqs_year_volume_query_link(self) -> str:
        return f"{self.wdqs_base_url}{quote(self.generate_year_volume_sparql_query)}"
