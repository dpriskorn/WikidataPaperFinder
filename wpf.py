from duckduckgo_search import DDGS
from pydantic import BaseModel
import json
from wikibaseintegrator import WikibaseIntegrator, wbi_backoff
from wikibaseintegrator.wbi_helpers import search_entities, execute_sparql_query


class WPF(BaseModel):
    reference_text: str
    ai_response: dict = {}
    journal_qid: str = ""
    sparql_query: str = ""
    query_result: dict = {}

    def ask_ai(self):
        ddgs = DDGS()
        prompt = (
            "Please extract the journal, year, volume, and page number from this reference in a paper "
            "and give me the result as one line unformatted JSON with the corresponding Wikidata property number as key, "
            "don't format as time, just return strings. Copy the journal name verbatim, only output the JSON: "
            f'"{self.reference_text}"'
        )
        text = ddgs.chat(prompt, model="gpt-4o-mini")  # You can change the model as needed
        text = text.replace("json", "").strip()
        print(text)
        try:
            # Attempt to parse the JSON response
            self.ai_response = json.loads(text)
        except json.JSONDecodeError:
            self.ai_response = {"error": "Failed to parse JSON from response"}

    def generate_sparql_query(self):
        if not self.is_valid_data():
            self.sparql_query = "Invalid data. Required fields: journal, year, volume, pages."
            return

        # Extract properties using Wikidata property IDs
        journal = self.ai_response.get("P1433", "")
        year = self.ai_response.get("P577", "")
        volume = self.ai_response.get("P478", "")
        pages = self.ai_response.get("P304", "")

        self.sparql_query = f"""
        SELECT ?article ?articleLabel ?volume ?pages ?publicationDate WHERE {{
          BIND ({year} AS ?year )
          BIND ("{volume}" AS ?volume )
          BIND (SUBSTR("{pages}", 1, 3) AS ?startPage )

          ?article wdt:P1433 wd:{self.journal_qid};  # article is published in the specified journal
                   wdt:P478 ?volume;      # article has volume
                   wdt:P304 ?pages;       # article has pages
                   wdt:P577 ?publicationDate.  # article has publication date

          # Filter for the year, volume, and first 3 characters of the pages
          FILTER(YEAR(?publicationDate) = ?year)  # Specify the year
          FILTER(SUBSTR(?pages, 1, STRLEN(?startPage)) = ?startPage)   # Match first 3 characters of pages

          # Return labels for articles and journals
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
        LIMIT 100
        """

    def is_valid_data(self):
        """Check if the required fields are present in the data."""
        required_fields = ["P1433", "P577", "P478", "P304"]
        return all(field in self.ai_response for field in required_fields)

    def search_journal_qid(self):
        journal_name = self.ai_response.get("P1433", "")
        if not journal_name:
            return ""

        search_results = search_entities(
            search_string=journal_name,
            search_type='item',
            dict_result=True
        )
        print(search_results)
        # Extract QID from search results
        if search_results and isinstance(search_results, list):
            for result in search_results:
                if 'id' in result and 'label' in result and result['label'].lower() == journal_name.lower() or result['match']['text'].lower() == journal_name.lower():
                    return result['id']  # Return the QID of the journal

        return ""  # Return None if no matching journal is found

    def execute_query(self, query: str):
        """Execute the SPARQL query and return the result."""
        result = execute_sparql_query(
            query=query,
            prefix=None,
            endpoint=None,
            user_agent=None,
            max_retries=1000,
            retry_after=60
        )
        return result

    def run(self):
        # Step 1: Ask the AI for the reference details
        self.ask_ai()
        if not self.is_valid_data():
            return f"Invalid data. Required fields: journal, year, volume, pages. '{self.ai_response}'"

        # Step 2: Find the journal QID
        self.journal_qid = self.search_journal_qid()
        if not self.journal_qid:
            return f"Journal QID not found for '{self.ai_response.get('P1433', '')}'"

        # Step 3: Generate the SPARQL query
        self.generate_sparql_query()
        if "Invalid data" in self.sparql_query:
            return self.sparql_query

        # Step 4: Execute the SPARQL query
        self.query_result = self.execute_query(self.sparql_query)
