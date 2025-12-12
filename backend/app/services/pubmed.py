import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


@dataclass
class PaperMetadata:
    pmid: str
    title: str
    abstract: str
    authors: List[str]
    journal: str
    publication_date: Optional[datetime]
    doi: Optional[str]
    keywords: List[str]
    mesh_terms: List[str]
    citation_count: Optional[int]
    pdf_url: Optional[str]


class PubMedAPIError(Exception):
    """Custom exception for PubMed API errors"""
    pass


class PubMedCollector:
    """
    PubMed API based paper metadata collector.
    Uses E-utilities API for searching and fetching papers.
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    RATE_LIMIT_DELAY = 0.34  # ~3 requests per second without API key

    def __init__(self):
        self.api_key = settings.PUBMED_API_KEY
        # With API key: 10 req/sec, without: 3 req/sec
        if self.api_key:
            self.rate_limit_delay = 0.1
        else:
            self.rate_limit_delay = self.RATE_LIMIT_DELAY

    def _build_params(self, params: dict) -> dict:
        """Add API key to parameters if available"""
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(
        self,
        endpoint: str,
        params: dict
    ) -> str:
        """Make HTTP request to PubMed API with retry logic"""
        url = f"{self.BASE_URL}{endpoint}"
        params = self._build_params(params)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)

            if response.status_code != 200:
                raise PubMedAPIError(
                    f"PubMed API error: {response.status_code} - {response.text}"
                )

            return response.text

    async def search_papers(
        self,
        query: str,
        max_results: int = 100,
        date_range: Optional[Tuple[str, str]] = None
    ) -> List[str]:
        """
        Search PubMed for papers matching query.

        Args:
            query: Search query (e.g., "cancer immunotherapy[Title/Abstract]")
            max_results: Maximum number of results
            date_range: (start_date, end_date) in YYYY/MM/DD format

        Returns:
            List of PMIDs
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance"
        }

        if date_range:
            params["mindate"] = date_range[0]
            params["maxdate"] = date_range[1]
            params["datetype"] = "pdat"

        response_text = await self._make_request("esearch.fcgi", params)

        try:
            import json
            data = json.loads(response_text)
            pmids = data.get("esearchresult", {}).get("idlist", [])
            return pmids
        except (json.JSONDecodeError, KeyError) as e:
            raise PubMedAPIError(f"Failed to parse search results: {e}")

    async def fetch_paper_details(self, pmid: str) -> Optional[PaperMetadata]:
        """Fetch detailed metadata for a single paper"""
        papers = await self.batch_fetch([pmid])
        return papers[0] if papers else None

    async def batch_fetch(
        self,
        pmid_list: List[str],
        batch_size: int = 100
    ) -> List[PaperMetadata]:
        """
        Fetch metadata for multiple papers.

        Args:
            pmid_list: List of PMIDs to fetch
            batch_size: Number of papers per request

        Returns:
            List of PaperMetadata objects
        """
        all_papers = []

        for i in range(0, len(pmid_list), batch_size):
            batch = pmid_list[i:i + batch_size]

            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "xml",
                "rettype": "abstract"
            }

            response_text = await self._make_request("efetch.fcgi", params)
            papers = self._parse_pubmed_xml(response_text)
            all_papers.extend(papers)

            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

        return all_papers

    def _parse_pubmed_xml(self, xml_text: str) -> List[PaperMetadata]:
        """Parse PubMed XML response into PaperMetadata objects"""
        papers = []

        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                try:
                    paper = self._parse_article(article)
                    if paper:
                        papers.append(paper)
                except Exception:
                    continue

        except ET.ParseError as e:
            raise PubMedAPIError(f"Failed to parse XML: {e}")

        return papers

    def _parse_article(self, article: ET.Element) -> Optional[PaperMetadata]:
        """Parse single article element"""
        medline = article.find(".//MedlineCitation")
        if medline is None:
            return None

        # PMID
        pmid_elem = medline.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else None
        if not pmid:
            return None

        # Article info
        article_elem = medline.find(".//Article")
        if article_elem is None:
            return None

        # Title
        title_elem = article_elem.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else ""

        # Abstract
        abstract_elem = article_elem.find(".//Abstract/AbstractText")
        abstract = abstract_elem.text if abstract_elem is not None else ""

        # Handle structured abstracts
        abstract_parts = article_elem.findall(".//Abstract/AbstractText")
        if len(abstract_parts) > 1:
            abstract = " ".join(
                f"{part.get('Label', '')}: {part.text}"
                for part in abstract_parts
                if part.text
            )

        # Authors
        authors = []
        for author in article_elem.findall(".//AuthorList/Author"):
            last_name = author.find("LastName")
            fore_name = author.find("ForeName")
            if last_name is not None and fore_name is not None:
                authors.append(f"{fore_name.text} {last_name.text}")
            elif last_name is not None:
                authors.append(last_name.text)

        # Journal
        journal_elem = article_elem.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""

        # Publication date
        pub_date = self._parse_pub_date(article_elem)

        # DOI
        doi = None
        for id_elem in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
            if id_elem.get("IdType") == "doi":
                doi = id_elem.text
                break

        # Keywords
        keywords = []
        for keyword_elem in medline.findall(".//KeywordList/Keyword"):
            if keyword_elem.text:
                keywords.append(keyword_elem.text)

        # MeSH terms
        mesh_terms = []
        for mesh_elem in medline.findall(".//MeshHeadingList/MeshHeading/DescriptorName"):
            if mesh_elem.text:
                mesh_terms.append(mesh_elem.text)

        return PaperMetadata(
            pmid=pmid,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            publication_date=pub_date,
            doi=doi,
            keywords=keywords,
            mesh_terms=mesh_terms,
            citation_count=None,
            pdf_url=None
        )

    def _parse_pub_date(self, article_elem: ET.Element) -> Optional[datetime]:
        """Parse publication date from article element"""
        pub_date_elem = article_elem.find(".//Journal/JournalIssue/PubDate")
        if pub_date_elem is None:
            return None

        year = pub_date_elem.find("Year")
        month = pub_date_elem.find("Month")
        day = pub_date_elem.find("Day")

        if year is None:
            return None

        try:
            year_val = int(year.text)
            month_val = self._parse_month(month.text) if month is not None else 1
            day_val = int(day.text) if day is not None else 1
            return datetime(year_val, month_val, day_val)
        except (ValueError, TypeError):
            return None

    def _parse_month(self, month_str: str) -> int:
        """Parse month string (could be number or name)"""
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "may": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }

        if month_str.isdigit():
            return int(month_str)

        return month_map.get(month_str.lower()[:3], 1)

    async def get_related_papers(
        self,
        pmid: str,
        limit: int = 10
    ) -> List[str]:
        """Get related papers using PubMed's elink API"""
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "cmd": "neighbor_score",
            "retmode": "json"
        }

        response_text = await self._make_request("elink.fcgi", params)

        try:
            import json
            data = json.loads(response_text)
            link_sets = data.get("linksets", [])
            if not link_sets:
                return []

            links = link_sets[0].get("linksetdbs", [])
            for link_db in links:
                if link_db.get("linkname") == "pubmed_pubmed":
                    link_ids = link_db.get("links", [])
                    return link_ids[:limit]

            return []
        except (json.JSONDecodeError, KeyError, IndexError):
            return []


class PDFProcessor:
    """Process PDF files to extract text content"""

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            return "\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to extract PDF text: {e}")

    @staticmethod
    def extract_sections(text: str) -> dict:
        """
        Split paper text into sections.

        Returns:
            Dict mapping section names to text content
        """
        sections = {}

        # Common section patterns
        patterns = {
            "abstract": r"ABSTRACT[:\s]*",
            "introduction": r"(?:INTRODUCTION|1\.\s*INTRODUCTION)[:\s]*",
            "methods": r"(?:METHODS|MATERIALS AND METHODS|2\.\s*METHODS)[:\s]*",
            "results": r"(?:RESULTS|3\.\s*RESULTS)[:\s]*",
            "discussion": r"(?:DISCUSSION|4\.\s*DISCUSSION)[:\s]*",
            "conclusion": r"(?:CONCLUSION|CONCLUSIONS|5\.\s*CONCLUSION)[:\s]*",
            "references": r"(?:REFERENCES|BIBLIOGRAPHY)[:\s]*",
        }

        # Find section boundaries
        section_positions = []
        for section_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                section_positions.append((match.start(), section_name))

        # Sort by position
        section_positions.sort(key=lambda x: x[0])

        # Extract section content
        for i, (pos, name) in enumerate(section_positions):
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                end_pos = len(text)

            section_text = text[pos:end_pos].strip()
            # Remove section header
            section_text = re.sub(patterns[name], "", section_text, count=1, flags=re.IGNORECASE)
            sections[name] = section_text.strip()

        return sections

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extracted text"""
        # Remove page numbers
        text = re.sub(r"\n\d+\n", "\n", text)

        # Remove reference numbers
        text = re.sub(r"\[\d+\]", "", text)

        # Remove URLs
        text = re.sub(r"http\S+", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove special characters but keep basic punctuation
        text = re.sub(r"[^\w\s.,;:?!()\-'\"]", " ", text)

        return text
