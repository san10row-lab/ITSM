#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


LABELS = {"ア", "イ", "ウ", "エ"}
YEARS = (2021, 2022, 2023, 2024)


def main() -> None:
    errors: list[str] = []
    for year in YEARS:
        exam_id = f"{year}-spring-sm-am2"
        exam_path = Path("data/exams") / f"{exam_id}.json"
        explanation_path = Path("data/explanations") / f"{exam_id}.json"
        exam = json.loads(exam_path.read_text(encoding="utf-8"))
        explanations = json.loads(explanation_path.read_text(encoding="utf-8"))

        if set(map(int, explanations)) != set(range(1, 26)):
            errors.append(f"{year}: explanation question numbers must be 1-25")
            continue

        for question in exam["questions"]:
            number = question["questionNo"]
            explanation = explanations[str(number)]
            if explanation.get("reviewed") is not True:
                errors.append(f"{year} Q{number}: reviewed must be true")
            if explanation.get("status") != "reviewed":
                errors.append(f"{year} Q{number}: status must be reviewed")
            if set(explanation.get("choices", {})) != LABELS:
                errors.append(f"{year} Q{number}: four choice explanations required")
            if question.get("answer") not in explanation.get("choices", {}):
                errors.append(f"{year} Q{number}: correct answer explanation missing")
            question["explanation"] = explanation

        exam["notes"] = (
            "問題PDFは画像OCRでテキスト化。図表が必要な問題は切り抜き画像を併用。"
            "選択肢別解説はレビュー済み。分野分類は未実施。"
            "OCR結果には軽微な誤字が残る場合があります。"
        )
        exam_path.write_text(
            json.dumps(exam, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if errors:
        raise SystemExit("\n".join(errors))
    print("Applied and validated reviewed explanations for 2021-2024.")


if __name__ == "__main__":
    main()
