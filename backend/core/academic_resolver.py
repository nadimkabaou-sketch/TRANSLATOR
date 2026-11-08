import urllib.request
import json
import xml.etree.ElementTree as ET
import re
from typing import Dict, Any, Optional

class AcademicResolver:
    """
    Connects to Crossref and PubMed APIs to resolve DOIs, PMIDs,
    fetch article metadata, structured abstracts, author lists,
    and verified citations.
    """

    def __init__(self, email: str = "scientific_translator@academic.org"):
        self.headers = {
            "User-Agent": f"ScientificPaperTranslator/1.0 (mailto:{email})"
        }

    def resolve_doi(self, doi: str) -> Dict[str, Any]:
        """Resolves metadata via Crossref."""
        clean_doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", "", doi).strip()
        url = f"https://api.crossref.org/works/{clean_doi}"
        req = urllib.request.Request(url, headers=self.headers)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                msg = data.get("message", {})
                
                title = msg.get("title", [""])[0] if msg.get("title") else ""
                authors = []
                for a in msg.get("author", []):
                    authors.append(f"{a.get('given', '')} {a.get('family', '')}".strip())
                
                return {
                    "doi": clean_doi,
                    "title": title,
                    "authors": authors,
                    "publisher": msg.get("publisher", ""),
                    "journal": msg.get("container-title", [""])[0] if msg.get("container-title") else "",
                    "issued_year": msg.get("issued", {}).get("date-parts", [[None]])[0][0],
                    "abstract": msg.get("abstract", "")
                }
        except Exception as e:
            return {"doi": clean_doi, "error": str(e)}

    def fetch_pubmed(self, identifier: str) -> Dict[str, Any]:
        """
        Fetches structured metadata and abstract from PubMed by PMID or DOI.
        """
        # Determine if identifier is DOI or PMID
        clean_id = identifier.strip()
        if "10." in clean_id:
            # Search PMID by DOI first
            search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={clean_id}[doi]&retmode=json"
            req = urllib.request.Request(search_url, headers=self.headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res_data = json.loads(resp.read().decode())
                    id_list = res_data.get("esearchresult", {}).get("idlist", [])
                    if id_list:
                        pmid = id_list[0]
                    else:
                        return {"error": "PMID not found for DOI"}
            except Exception as e:
                return {"error": f"PubMed search failed: {e}"}
        else:
            pmid = clean_id

        # Fetch PubMed XML
        fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
        req = urllib.request.Request(fetch_url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_text = resp.read().decode("utf-8")
                root = ET.fromstring(xml_text)
                
                # Title
                title_elem = root.find(".//ArticleTitle")
                title = "".join(title_elem.itertext()) if title_elem is not None else ""

                # Abstract sections
                abstract_sections = []
                for a in root.findall(".//AbstractText"):
                    label = a.attrib.get("Label", "")
                    sec_text = "".join(a.itertext())
                    abstract_sections.append({"label": label, "text": sec_text})

                # Authors
                authors = []
                for auth in root.findall(".//Author"):
                    last = auth.find("LastName")
                    fore = auth.find("ForeName")
                    if last is not None and fore is not None:
                        authors.append(f"{fore.text} {last.text}")

                # Journal
                journal_elem = root.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else ""

                return {
                    "pmid": pmid,
                    "title": title,
                    "journal": journal,
                    "authors": authors,
                    "abstract_sections": abstract_sections
                }
        except Exception as e:
            return {"error": f"PubMed fetch failed: {e}"}
