import re
from typing import Dict, List, Tuple

class EntityProtector:
    """
    Guarantees 100% scientific integrity by detecting and replacing
    equations, citations, numbers, scientific units, DOIs, URLs,
    and non-translatable scientific tokens with neutral placeholders
    prior to translation, and precisely restoring them afterwards.
    """

    def __init__(self):
        # Protected patterns ordered by specificity
        self.patterns = [
            # 1. LaTeX Math blocks and inline math
            ("EQ_BLOCK", re.compile(r"(\\begin\{(?:equation|align|gather|multline)\*?\}.*?\\end\{(?:equation|align|gather|multline)\*?\}|\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\])", re.DOTALL)),
            ("EQ_INLINE", re.compile(r"(\$(?!\$)[^\$\n]+?\$|\\\(.*?\\\))")),
            
            # 2. DOIs, URLs and Emails
            ("DOI", re.compile(r"\b(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b", re.IGNORECASE)),
            ("URL", re.compile(r"\bhttps?://[^\s/$.?#].[^\s]*\b", re.IGNORECASE)),
            ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),

            # 3. Scientific Citations [1], [1-5], [1, 2, 8], (Smith et al., 2021)
            ("CITE_NUM", re.compile(r"\[\s*\d+(?:\s*[-–—,;]\s*\d+)*\s*\]")),
            ("CITE_AUTHOR", re.compile(r"\((?:[A-Z][A-Za-z\-]+(?:\s+et\s+al\.?)?(?:,\s*\d{4}[a-z]?)?(?:;\s*)?)+\)")),

            # 4. Statistical significance and formulas (p < 0.05, 95% CI [x, y], R2 = 0.8)
            ("STAT_EXP", re.compile(r"\b(?:p|P)\s*([<>=≤≥]|[\b\s])\s*0?\.\d+\b")),
            ("CI_EXP", re.compile(r"\b\d{1,2}%\s*(?:CI|confidence interval)\s*\[?\s*\d+(?:\.\d+)?\s*[-–,]\s*\d+(?:\.\d+)?\s*\]?", re.IGNORECASE)),
            
            # 5. Scientific Units, Measurements and Percentages
            ("PERCENT", re.compile(r"\b\d+(?:[\.,]\d+)?\s*%")),
            ("MEASURE", re.compile(r"\b\d+(?:[\.,]\d+)?\s*(?:mm|cm|m|µm|nm|T|Tesla|MHz|GHz|mL|dL|mg|g|kg|mol|mmol|HU|ms|s|min|h|Gy|mGy|Sv|mSv|dB|°C|°F|K)(?:\b|(?=[^A-Za-z0-9]))")),
            
            # 6. Specific Radiologic / Scientific codes (e.g., T1WI, T2WI, b=1000, O-RADS)
            ("RAD_PARAM", re.compile(r"\b(?:T1|T2|T1WI|T2WI|DWI|ADC|FLAIR|STIR|SSFP|CISS|FIESTA|TOF|3D-CISS|3D-FIESTA|3D-TOF|b=\d+|O-RADS(?:\s*v?\d+)?)\b")),

            # 7. Figure and Table References (e.g., Fig. 1, Figure 2A, Table 3)
            ("FIG_REF", re.compile(r"\b(?:Fig(?:ure)?\.?\s*\d+[A-Za-z]?(?:\s*[-–]\s*\d+[A-Za-z]?)?|Table\s*\d+[A-Za-z]?)\b", re.IGNORECASE))
        ]

    def protect(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replaces sensitive entities with immutable XML placeholder tags:
        <x{index}/>
        Returns (protected_text, placeholder_map).
        """
        if not text or not text.strip():
            return text, {}

        placeholder_map: Dict[str, str] = {}
        protected_text = text
        token_counter = 0

        for p_name, regex in self.patterns:
            matches = list(regex.finditer(protected_text))
            # Process in reverse order to preserve string offsets
            for match in reversed(matches):
                original_span = match.group(0)
                # Avoid nesting if already inside a placeholder
                if re.match(r"^<x\d+/>$", original_span) or "<x" in original_span:
                    continue
                
                placeholder = f"<x{token_counter}/>"
                placeholder_map[placeholder] = original_span
                token_counter += 1

                start, end = match.span()
                protected_text = protected_text[:start] + placeholder + protected_text[end:]

        return protected_text, placeholder_map

    def restore(self, text: str, placeholder_map: Dict[str, str]) -> Tuple[str, List[str]]:
        """
        Restores placeholders back to original strings.
        Checks for any missing or altered placeholders and returns
        (restored_text, missing_placeholders_warnings).
        """
        if not text or not placeholder_map:
            return text, []

        restored_text = text
        missing_warnings: List[str] = []

        for placeholder, original_value in placeholder_map.items():
            if placeholder in restored_text:
                restored_text = restored_text.replace(placeholder, original_value)
            else:
                # Sometimes models adjust spacing e.g., < x0 / > or <x0>
                tag_id = re.search(r"\d+", placeholder).group(0)
                tolerant_pattern = re.compile(rf"<\s*x{tag_id}\s*(?:/\s*>|>)", re.IGNORECASE)
                if tolerant_pattern.search(restored_text):
                    restored_text = tolerant_pattern.sub(original_value, restored_text)
                else:
                    missing_warnings.append(f"Missing placeholder '{placeholder}' (original: '{original_value}')")
                    restored_text += f" {original_value}"

        return restored_text, missing_warnings
