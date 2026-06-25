#!/usr/bin/env python3
from __future__ import annotations

import json
import argparse
import subprocess
from pathlib import Path


EXAMS = [
    {
        "id": "2025-spring-sm-am2",
        "title": "2025年 春期 ITサービスマネージャ 午前II",
        "year": 2025,
        "era": "令和7年度",
        "season": "春期",
        "prefix": "2025r07h_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/nl10bi0000009lh8-att/2025r07h_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/nl10bi0000009lh8-att/2025r07h_sm_am2_ans.pdf",
    },
    {
        "id": "2024-spring-sm-am2",
        "title": "2024年 春期 ITサービスマネージャ 午前II",
        "year": 2024,
        "era": "令和6年度",
        "season": "春期",
        "prefix": "2024r06h_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/m42obm000000afqx-att/2024r06h_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/m42obm000000afqx-att/2024r06h_sm_am2_ans.pdf",
    },
    {
        "id": "2023-spring-sm-am2",
        "title": "2023年 春期 ITサービスマネージャ 午前II",
        "year": 2023,
        "era": "令和5年度",
        "season": "春期",
        "prefix": "2023r05h_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/ps6vr70000010d6y-att/2023r05h_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/ps6vr70000010d6y-att/2023r05h_sm_am2_ans.pdf",
    },
    {
        "id": "2022-spring-sm-am2",
        "title": "2022年 春期 ITサービスマネージャ 午前II",
        "year": 2022,
        "era": "令和4年度",
        "season": "春期",
        "prefix": "2022r04h_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt80000009sgk-att/2022r04h_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt80000009sgk-att/2022r04h_sm_am2_ans.pdf",
    },
    {
        "id": "2021-spring-sm-am2",
        "title": "2021年 春期 ITサービスマネージャ 午前II",
        "year": 2021,
        "era": "令和3年度",
        "season": "春期",
        "prefix": "2021r03h_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000d5ru-att/2021r03h_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000d5ru-att/2021r03h_sm_am2_ans.pdf",
    },
    {
        "id": "2019-autumn-sm-am2",
        "title": "2019年 秋期 ITサービスマネージャ 午前II",
        "year": 2019,
        "era": "令和元年度",
        "season": "秋期",
        "prefix": "2019r01a_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000dict-att/2019r01a_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000dict-att/2019r01a_sm_am2_ans.pdf",
    },
    {
        "id": "2018-autumn-sm-am2",
        "title": "2018年 秋期 ITサービスマネージャ 午前II",
        "year": 2018,
        "era": "平成30年度",
        "season": "秋期",
        "prefix": "2018h30a_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000f01f-att/2018h30a_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000f01f-att/2018h30a_sm_am2_ans.pdf",
    },
    {
        "id": "2017-autumn-sm-am2",
        "title": "2017年 秋期 ITサービスマネージャ 午前II",
        "year": 2017,
        "era": "平成29年度",
        "season": "秋期",
        "prefix": "2017h29a_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000fqpm-att/2017h29a_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000fqpm-att/2017h29a_sm_am2_ans.pdf",
    },
    {
        "id": "2016-autumn-sm-am2",
        "title": "2016年 秋期 ITサービスマネージャ 午前II",
        "year": 2016,
        "era": "平成28年度",
        "season": "秋期",
        "prefix": "2016h28a_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000g6fw-att/2016h28a_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000g6fw-att/2016h28a_sm_am2_ans.pdf",
    },
    {
        "id": "2015-autumn-sm-am2",
        "title": "2015年 秋期 ITサービスマネージャ 午前II",
        "year": 2015,
        "era": "平成27年度",
        "season": "秋期",
        "prefix": "2015h27a_sm_am2",
        "question_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000gxj0-att/2015h27a_sm_am2_qs.pdf",
        "answer_url": "https://www.ipa.go.jp/shiken/mondai-kaiotu/gmcbt8000000gxj0-att/2015h27a_sm_am2_ans.pdf",
    },
]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-only", action="store_true")
    args = parser.parse_args()

    pdf_dir = Path("tmp/ipa_pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)

    if not args.index_only:
        for exam in EXAMS:
            qs_path = pdf_dir / f"{exam['prefix']}_qs.pdf"
            ans_path = pdf_dir / f"{exam['prefix']}_ans.pdf"
            if not qs_path.exists():
                run(["curl", "-L", "-o", str(qs_path), exam["question_url"]])
            if not ans_path.exists():
                run(["curl", "-L", "-o", str(ans_path), exam["answer_url"]])
            run(
                [
                    "/Users/takaomakibuchi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",
                    "scripts/prepare_exam.py",
                    "--questions",
                    str(qs_path),
                    "--answers",
                    str(ans_path),
                    "--exam-id",
                    exam["id"],
                    "--title",
                    exam["title"],
                    "--year",
                    str(exam["year"]),
                    "--era",
                    exam["era"],
                    "--season",
                    exam["season"],
                    "--ocr",
                ]
            )

    index = [
        {
            "id": exam["id"],
            "title": exam["title"],
            "path": f"data/exams/{exam['id']}.json",
        }
        for exam in EXAMS
    ]
    Path("data/exams").mkdir(parents=True, exist_ok=True)
    Path("data/exams/index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
