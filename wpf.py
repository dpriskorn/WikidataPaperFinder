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
    sparql_query: str = ""
    query_result: dict = {}
    status: str = ""
    query_executed: bool = False

    def ask_ai(self):
        ddgs = DDGS()
        prompt = (
            "Please extract the journal, year, volume, and page number from this reference in a paper "
            "and give me the result as one line unformatted JSON with the corresponding Wikidata property number as key, "
            "don't format as time, just return strings. Copy the journal name verbatim, only output the JSON: "
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

    def generate_sparql_query(self) -> None:
        if not self.is_valid_data():
            self.status = (
                "Invalid data from GPT4o."
            )
            return
        if not self.journal_qid:
            self.status = ("Missing journal qid")
            return

        # Extract properties using Wikidata property IDs
        # journal = self.ai_response.get("P1433", "")
        year = int(self.ai_response.get("P577", ""))
        volume = self.ai_response.get("P478", "")
        # Handle weird unicode
        pages = self.ai_response.get("P304", "").replace("\u2013", "-")
        try:
            if "-" in pages:
                start_page = int(pages.split("-")[0])
            else:
                start_page = int(pages)
        except ValueError:
            self.status = f"Could not convert '{pages}' to a number."
            return
        self.sparql_query = f"""
        SELECT ?article ?articleLabel ?volume ?pages ?publicationDate WHERE {{
          BIND ( wd:{self.journal_qid} AS ?journal ) .
          BIND ( {year} AS ?year ) .
          BIND ( "{volume}" AS ?volume ) .
          BIND ( {start_page} AS ?startPage ) .
          BIND ( 15 AS ?range ) .
          
          ?article wdt:P1433 ?journal; wdt:P478 ?volume; wdt:P304 ?pages; wdt:P577 ?publicationDate .
        
          FILTER( YEAR( ?publicationDate ) = ?year ) .
          BIND( REPLACE( ?pages,"(\\\\d*).*","$1" ) AS ?start ) .
          FILTER( ( xsd:integer(?start) < ?startPage + ?range ) && ( xsd:integer(?start) > ?startPage - ?range ) ) .
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en" . }}
        }}
        ORDER BY ASC(xsd:integer(?start))
        """

    def is_valid_data(self):
        """Check if the required fields are present in the data."""
        required_fields = ["P1433", "P577", "P478", "P304"]
        return all(field in self.ai_response for field in required_fields)

    def extract_journal_name(self):
        self.journal_name = self.ai_response.get("P1433", "")
        if not self.journal_name:
            logger.error("Got no journal_name")
            return


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
        # Step 1: Ask the AI for the reference details
        if not self.ai_response:
            self.ask_ai()
            if not self.is_valid_data():
                self.status = f"Invalid data. Required fields: journal, year, volume, pages. '{self.ai_response}'"

        # Step: Extract journal name
        if not self.journal_name:
            self.extract_journal_name()
            if not self.journal_name:
                self.status = "Journal name could not be extracted by ChatGPT using GPT-4o"

        # Step 2: Find the journal QID
        if not self.journal_qid:
            self.search_journal_qid()
            if not self.journal_qid:
                self.status = (
                    f"Journal QID not found for '{self.ai_response.get('P1433', '')}'"
                )

        # Step 3: Generate the SPARQL query
        if not self.sparql_query:
            self.generate_sparql_query()
            if not self.sparql_query:
                self.status += " Could not generate sparql query"

        # Step 4: Execute the SPARQL query
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
    def wdqs_query_link(self):
        if self.sparql_query:
            return f"https://query.wikidata.org/#{quote(self.sparql_query)}"
        else:
            return ""

    @property
    def wikidata_journal_link(self):
        if self.journal_qid:
            return f"https://wikidata.org/wiki/{self.journal_qid}"
        else:
            return ""
