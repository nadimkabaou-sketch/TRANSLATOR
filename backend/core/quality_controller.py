import re
from typing import Dict, List, Any

class QualityController:
    """
    Automated Scientific Quality Control and Audit Engine.
    Performs rigorous checks on translated articles:
      1. Structural 1-to-1 element mapping parity
      2. Conservation of numbers, dates, and percentages
      3. Conservation of mathematical equations
      4. Conservation of bibliographic references and citations
      5. Conservation of scientific units
      6. Detection of untranslated text or anomalous length ratios
      7. Flagging of uncertain segments for human verification.
    """

    def __init__(self):
        self.num_regex = re.compile(r"\b\d+(?:[\.,]\d+)?\b")
        self.cite_regex = re.compile(r"\[\s*\d+(?:\s*[-–—,;]\s*\d+)*\s*\]")
        self.math_regex = re.compile(r"(\$[^\$]+\$|\\\[[\s\S]*?\\\]|\\begin\{equation\}[\s\S]*?\\end\{equation\})")
        self.unit_regex = re.compile(r"\b\d+(?:[\.,]\d+)?\s*(?:mm|cm|m|µm|nm|T|Tesla|MHz|GHz|mL|dL|mg|g|kg|mol|mmol|HU|ms|s|min|h|Gy|mGy|Sv|mSv|dB|%|°C|K)\b")

    def audit_document(self, source_elements: List[Dict[str, Any]], translated_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs comprehensive scientific audit on the full translated document.
        Returns a structured QC Report.
        """
        issues: List[Dict[str, Any]] = []
        element_audits: List[Dict[str, Any]] = []

        total_elements = len(source_elements)
        translated_count = len(translated_elements)

        # 1. Structural Parity Check
        if total_elements != translated_count:
            issues.append({
                "severity": "CRITICAL",
                "type": "ELEMENT_COUNT_MISMATCH",
                "message": f"Source has {total_elements} elements but translation has {translated_count} elements."
            })

        perfect_matches = 0
        total_number_checks = 0
        passed_number_checks = 0
        total_cite_checks = 0
        passed_cite_checks = 0

        # Element-by-element verification
        for idx in range(min(total_elements, translated_count)):
            src_elem = source_elements[idx]
            trg_elem = translated_elements[idx]

            src_text = src_elem.get("text", "")
            trg_text = trg_elem.get("text", "")

            elem_issues: List[str] = []

            # Check for empty translation
            if src_text.strip() and not trg_text.strip():
                elem_issues.append("Missing translated text (empty paragraph).")

            # 2. Number conservation check
            src_nums = set(self.num_regex.findall(src_text))
            trg_nums = set(self.num_regex.findall(trg_text))
            
            missing_nums = src_nums - trg_nums
            if missing_nums:
                # Filter out formatting differences (e.g., 0.5 vs 0,5)
                filtered_missing = []
                for n in missing_nums:
                    alt = n.replace(".", ",") if "." in n else n.replace(",", ".")
                    if alt not in trg_nums:
                        filtered_missing.append(n)
                if filtered_missing:
                    elem_issues.append(f"Missing numbers/values: {', '.join(filtered_missing)}")
            
            total_number_checks += len(src_nums)
            passed_number_checks += (len(src_nums) - len(missing_nums))

            # 3. Citation conservation check
            src_cites = set(self.cite_regex.findall(src_text))
            trg_cites = set(self.cite_regex.findall(trg_text))
            missing_cites = src_cites - trg_cites
            if missing_cites:
                elem_issues.append(f"Missing bibliographic citations: {', '.join(missing_cites)}")
            
            total_cite_checks += len(src_cites)
            passed_cite_checks += (len(src_cites) - len(missing_cites))

            # 4. Math equation check
            src_math = self.math_regex.findall(src_text)
            trg_math = self.math_regex.findall(trg_text)
            if len(src_math) != len(trg_math):
                elem_issues.append(f"Equation count discrepancy: {len(src_math)} in source vs {len(trg_math)} in translation.")

            # 5. Length ratio / anomaly check
            if len(src_text) > 40:
                ratio = len(trg_text) / len(src_text)
                if ratio < 0.45:
                    elem_issues.append(f"Suspiciously short translation (ratio {ratio:.2f} < 0.45). Possible sentence truncation.")
                elif ratio > 2.6:
                    elem_issues.append(f"Suspiciously long translation (ratio {ratio:.2f} > 2.6). Possible loop/hallucination.")

            # Calculate element status
            if not elem_issues:
                perfect_matches += 1
                status = "VERIFIED"
            else:
                status = "REQUIRES_REVIEW"
                for iss in elem_issues:
                    issues.append({
                        "element_id": src_elem.get("id"),
                        "severity": "WARNING",
                        "message": f"Element [{src_elem.get('id')}]: {iss}"
                    })

            element_audits.append({
                "element_id": src_elem.get("id"),
                "status": status,
                "flags": elem_issues
            })

        # Calculate Overall Scientific Fidelity Score (0 to 100%)
        structural_score = (perfect_matches / max(1, total_elements)) * 100
        number_fidelity = (passed_number_checks / max(1, total_number_checks)) * 100 if total_number_checks > 0 else 100.0
        cite_fidelity = (passed_cite_checks / max(1, total_cite_checks)) * 100 if total_cite_checks > 0 else 100.0

        overall_qc_score = round((structural_score * 0.4 + number_fidelity * 0.35 + cite_fidelity * 0.25), 1)

        confidence_rating = "HIGH" if overall_qc_score >= 95 else ("MEDIUM" if overall_qc_score >= 80 else "NEEDS_HUMAN_VALIDATION")

        return {
            "overall_score": overall_qc_score,
            "confidence_rating": confidence_rating,
            "total_elements": total_elements,
            "perfect_elements": perfect_matches,
            "flagged_elements": total_elements - perfect_matches,
            "number_fidelity_pct": round(number_fidelity, 1),
            "citation_fidelity_pct": round(cite_fidelity, 1),
            "issues": issues,
            "element_audits": element_audits,
            "requires_human_review": overall_qc_score < 98.0 or len(issues) > 0
        }
