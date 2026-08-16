#!/usr/bin/env python3
"""Assign one reviewed taxonomy label to every generated exam question.

The labels are kept in data/categories so regenerating OCR data does not erase them.
"""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    category_dir = Path("data/categories")
    errors: list[str] = []
    applied = 0
    for exam_path in sorted(Path("data/exams").glob("*.json")):
        if exam_path.name == "index.json":
            continue
        exam = json.loads(exam_path.read_text(encoding="utf-8"))
        category_path = category_dir / exam_path.name
        if not category_path.exists():
            errors.append(f"missing category file: {category_path}")
            continue
        categories = json.loads(category_path.read_text(encoding="utf-8"))
        expected = {str(question["questionNo"]) for question in exam["questions"]}
        if set(categories) != expected:
            errors.append(f"{exam['id']}: category question numbers do not match")
            continue
        for question in exam["questions"]:
            category = categories[str(question["questionNo"])]
            if not isinstance(category, str) or not category.strip():
                errors.append(f"{exam['id']} Q{question['questionNo']}: invalid category")
                continue
            question["category"] = category
            applied += 1
        exam_path.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Applied categories to {applied} questions.")


if __name__ == "__main__":
    main()
