#!/usr/bin/env python3
"""Apply the reviewed calculation-question classification to generated exams."""
from __future__ import annotations

import json
from pathlib import Path


VALID_TYPES = {"calculation", "formula"}


def main() -> None:
    source_path = Path("data/calculations.json")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    counts = {"calculation": 0, "formula": 0, "knowledge": 0}

    for exam_path in sorted(Path("data/exams").glob("*.json")):
        if exam_path.name == "index.json":
            continue
        exam = json.loads(exam_path.read_text(encoding="utf-8"))
        classifications = source.get(exam["id"], {})
        valid_numbers = {str(question["questionNo"]) for question in exam["questions"]}
        unknown = set(classifications) - valid_numbers
        if unknown:
            errors.append(f"{exam['id']}: unknown question numbers {sorted(unknown)}")

        for question in exam["questions"]:
            classification = classifications.get(str(question["questionNo"]))
            if classification is None:
                question["questionType"] = "knowledge"
                question["calculationPattern"] = None
                counts["knowledge"] += 1
                continue
            question_type = classification.get("questionType")
            pattern = classification.get("calculationPattern")
            if question_type not in VALID_TYPES or not isinstance(pattern, str) or not pattern.strip():
                errors.append(f"{exam['id']} Q{question['questionNo']}: invalid classification")
                continue
            question["questionType"] = question_type
            question["calculationPattern"] = pattern
            counts[question_type] += 1

        exam_path.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Applied calculation classifications: {counts}")


if __name__ == "__main__":
    main()
