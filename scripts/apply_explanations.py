#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


LABELS = {"ア", "イ", "ウ", "エ"}
EXAM_IDS = (
    "2015-autumn-sm-am2",
    "2016-autumn-sm-am2",
    "2017-autumn-sm-am2",
    "2018-autumn-sm-am2",
    "2019-autumn-sm-am2",
    "2021-spring-sm-am2",
    "2022-spring-sm-am2",
    "2023-spring-sm-am2",
    "2024-spring-sm-am2",
)


def main() -> None:
    errors: list[str] = []
    for exam_id in EXAM_IDS:
        year = exam_id.split("-", 1)[0]
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
    print("Applied and validated reviewed explanations for 2015-2019 and 2021-2024.")


if __name__ == "__main__":
    main()
