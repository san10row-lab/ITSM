#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from PIL import Image
from pypdf import PdfReader


@dataclass
class QuestionSlice:
    raw_text: str
    page_no: int


MANUAL_CHOICE_PATCHES_BY_EXAM = {
    "2025-spring-sm-am2": {
        # OCR drops the "イ 2" line on the diagram-heavy schedule question.
        19: {"イ": "2"},
    },
    "2024-spring-sm-am2": {
        19: {"ア": "1", "イ": "2"},
    },
    "2021-spring-sm-am2": {
        22: {
            "ア": "MTBF: R / MTTR: S",
            "イ": "MTBF: R / MTTR: 2S",
            "ウ": "MTBF: R/2 / MTTR: S",
            "エ": "MTBF: R/2 / MTTR: 2S",
        },
    },
    "2022-spring-sm-am2": {
        4: {
            "イ": "サービス・カタログは、一つのサービス・ポートフォリオに対して一つであり、1対1に対応している。",
        },
        16: {
            "ウ": "政府が求めるセキュリティ要求を満たしていることが確認されたクラウドサービスがISMAPクラウドサービスリストに登録される。",
            "エ": "政府機関がクラウドサービスを利用するに当たり、適切にクラウドサービス事業者を選定しているかどうかを監査機関が審査し、認定された政府機関がISMAPクラウドサービスリストに登録される。",
        },
        22: {"ウ": "7,000", "エ": "9,000"},
    },
    "2015-autumn-sm-am2": {
        16: {
            "ア": "A社: 顧客 / B社: 納入者 / D社: 母体組織",
            "イ": "A社: 顧客 / B社: 母体組織 / D社: 納入者",
            "ウ": "A社: 母体組織 / B社: 顧客 / D社: 納入者",
            "エ": "A社: 母体組織 / B社: 納入者 / D社: 顧客",
        },
        17: {"イ": "120"},
    },
}

MANUAL_FIGURE_CROPS_BY_EXAM = {
    "2025-spring-sm-am2": {
        6: [
            {
                "page": 6,
                "box": (185, 665, 1230, 1625),
                "alt": "旧システムから新システムへの切替え移行作業の流れ図",
            }
        ],
        19: [
            {
                "page": 12,
                "box": (190, 365, 1390, 1120),
                "alt": "当初の計画と変更後の計画を示すプロジェクトスケジュール図",
            }
        ],
    },
    "2024-spring-sm-am2": {
        19: [
            {
                "page": 11,
                "box": (320, 1160, 1220, 1585),
                "alt": "アローダイアグラムで表されるプロジェクト日程",
            }
        ],
    },
    "2023-spring-sm-am2": {
        7: [
            {
                "page": 6,
                "box": (175, 450, 1240, 1575),
                "alt": "旧システムから新システムへの切替え移行作業の流れ図",
            }
        ],
        19: [
            {
                "page": 12,
                "box": (210, 720, 1265, 1085),
                "alt": "ローコード開発ツールごとのプログラム本数と所要工数の表",
            }
        ],
    },
    "2022-spring-sm-am2": {
        22: [
            {
                "page": 13,
                "box": (300, 520, 1060, 1325),
                "alt": "指数関数F(t)=exp(-lambda t)のグラフ",
            }
        ],
        23: [
            {
                "page": 14,
                "box": (260, 380, 1130, 1035),
                "alt": "2相コミットプロトコルの正常処理の流れ図",
            }
        ],
        24: [
            {
                "page": 15,
                "box": (210, 330, 1220, 730),
                "alt": "クライアントからプロキシサーバを経由してWebサーバを利用する経路図",
            }
        ],
    },
    "2021-spring-sm-am2": {
        6: [
            {
                "page": 5,
                "box": (175, 450, 1240, 1575),
                "alt": "旧システムから新システムへの切替え移行作業の流れ図",
            }
        ],
    },
    "2019-autumn-sm-am2": {
        19: [
            {
                "page": 13,
                "box": (315, 1240, 1160, 1545),
                "alt": "フェッチされた命令の格納順序を表すプロセッサ構成図",
            }
        ],
        22: [
            {
                "page": 15,
                "box": (190, 330, 1210, 760),
                "alt": "クライアントからプロキシサーバを経由してWebサーバを利用する経路図",
            }
        ],
    },
    "2018-autumn-sm-am2": {
        10: [
            {
                "page": 7,
                "box": (430, 470, 1005, 785),
                "alt": "ITサービスを提供するサプライチェーン関係の例",
            }
        ],
    },
    "2017-autumn-sm-am2": {
        22: [
            {
                "page": 12,
                "box": (185, 690, 1210, 1075),
                "alt": "クライアントからプロキシサーバを経由してWebサーバを利用する経路図",
            }
        ],
    },
    "2016-autumn-sm-am2": {
        9: [
            {
                "page": 6,
                "box": (430, 430, 1005, 800),
                "alt": "ITサービスを提供するサプライチェーン関係の例",
            }
        ],
    },
    "2015-autumn-sm-am2": {
        3: [
            {
                "page": 4,
                "box": (385, 260, 1100, 1180),
                "alt": "ITILサービスライフサイクルの各段階の説明と流れ",
            }
        ],
        16: [
            {
                "page": 11,
                "box": (190, 620, 960, 1025),
                "alt": "プロジェクトとステークホルダ各社の関係表",
            }
        ],
        17: [
            {
                "page": 11,
                "box": (430, 1280, 1015, 1650),
                "alt": "アーンドバリュー分析の管理項目と金額の表",
            }
        ],
    },
}

MANUAL_QUESTION_TEXT_CUTOFFS_BY_EXAM = {
    "2025-spring-sm-am2": {
        6: "\n移行開始",
        19: "\n•",
    },
    "2024-spring-sm-am2": {19: "\nB"},
    "2023-spring-sm-am2": {7: "\n移行開始", 19: "\n〔ローコード"},
    "2022-spring-sm-am2": {22: "\n指数関数", 23: "\nシステム A", 24: "\nクライ"},
    "2021-spring-sm-am2": {6: "\n移行開始"},
    "2019-autumn-sm-am2": {19: "\nプロセッサ", 22: "\nクライ"},
    "2018-autumn-sm-am2": {10: "\n顧客"},
    "2017-autumn-sm-am2": {22: "\nクライ"},
    "2016-autumn-sm-am2": {9: "\n顧客"},
    "2015-autumn-sm-am2": {3: "\na", 16: "\nプロジェクトとステークホルダ", 17: "\n管理項目"},
}


def first_image_in_xobjects(xobjects):
    for obj in xobjects.values():
        resolved = obj.get_object()
        if resolved.get("/Subtype") == "/Image":
            return resolved
        nested = (resolved.get("/Resources") or {}).get("/XObject") or {}
        found = first_image_in_xobjects(nested)
        if found is not None:
            return found
    return None


def extract_page_images(questions_pdf: Path, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(questions_pdf))
    paths: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        xobjects = (page.get("/Resources") or {}).get("/XObject") or {}
        image = first_image_in_xobjects(xobjects)
        if image is None:
            continue
        ext = ".jpg" if image.get("/Filter") == "/DCTDecode" else ".bin"
        out = output_dir / f"page-{index:02d}{ext}"
        out.write_bytes(image.get_data())
        paths.append(str(out))
    return paths


def crop_question_figures(
    image_paths: list[str],
    exam_id: str,
    data_dir: Path,
) -> dict[int, list[dict[str, str]]]:
    figures_dir = data_dir / "assets" / exam_id / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    figures: dict[int, list[dict[str, str]]] = {}
    for question_no, crop_defs in MANUAL_FIGURE_CROPS_BY_EXAM.get(exam_id, {}).items():
        question_figures = []
        for index, crop_def in enumerate(crop_defs, start=1):
            page_index = crop_def["page"] - 1
            image = Image.open(image_paths[page_index]).convert("RGB")
            cropped = image.crop(crop_def["box"])
            filename = f"q-{question_no:02d}-{index}.jpg"
            out = figures_dir / filename
            cropped.save(out, quality=92)
            question_figures.append(
                {
                    "src": f"data/assets/{exam_id}/figures/{filename}",
                    "alt": crop_def["alt"],
                }
            )
        figures[question_no] = question_figures
    return figures


def parse_answers(answers_pdf: Path) -> dict[int, str]:
    text_parts: list[str] = []
    with pdfplumber.open(str(answers_pdf)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    text = "\n".join(text_parts)
    pairs = re.findall(r"問\s*(\d+)\s*([アイウエ])", text)
    answers = {int(number): answer for number, answer in pairs}
    if len(answers) != 25:
        raise ValueError(f"Expected 25 answers, found {len(answers)}")
    return answers


def ocr_pages(image_paths: list[str], swift_script: Path) -> dict[int, str]:
    page_text: dict[int, str] = {}
    for index, image_path in enumerate(image_paths, start=1):
        result = subprocess.run(
            ["swift", str(swift_script), image_path],
            check=True,
            capture_output=True,
            text=True,
        )
        page_text[index] = cleanup_ocr_text(result.stdout)
    return page_text


def cleanup_ocr_text(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.fullmatch(r"[-ー―\s]*\d+[-ー―\s]*", line):
            continue
        if line.startswith("令和") and "IT サービスマネージャ試験" in line:
            continue
        lines.append(line)
    return "\n".join(lines)


def slice_questions(page_text: dict[int, str]) -> dict[int, QuestionSlice]:
    markers: list[tuple[int, int, int]] = []
    for page_no, text in page_text.items():
        for match in re.finditer(r"[問間]\s*(\d{1,2})(?!\d)", text):
            question_no = int(match.group(1))
            if 1 <= question_no <= 25 and is_question_marker(text, match):
                markers.append((question_no, page_no, match.start()))

    first_markers: dict[int, tuple[int, int]] = {}
    for question_no, page_no, pos in sorted(markers, key=lambda item: (item[0], item[1], item[2])):
        first_markers.setdefault(question_no, (page_no, pos))

    slices: dict[int, QuestionSlice] = {}
    for question_no in range(1, 26):
        if question_no not in first_markers:
            slices[question_no] = QuestionSlice("", 0)
            continue
        page_no, start = first_markers[question_no]
        text = page_text.get(page_no, "")
        end = len(text)
        next_marker = first_markers.get(question_no + 1)
        if next_marker and next_marker[0] == page_no:
            end = next_marker[1]
        slices[question_no] = QuestionSlice(text[start:end].strip(), page_no)
    return slices


def is_question_marker(text: str, match: re.Match[str]) -> bool:
    """Reject OCR hits from the cover instructions, such as "問1〜問25"."""
    after_number = text[match.end():]
    after_stripped = after_number.lstrip()
    if after_stripped.startswith(("～", "〜", "~", "-", "ー", "－", ":", "：")):
        return False
    if re.match(r"選択方法\b", after_stripped):
        return False

    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.start())
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end].strip()
    if "選択方法" in line or "全問必須" in line:
        return False

    context = text[match.start(): match.start() + 500]
    if "答案用紙" in context and "例題" in context:
        return False
    return True


def split_prompt_and_choices(text: str) -> tuple[str, dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", {}

    current_choice = None
    prompt_lines: list[str] = []
    choices: dict[str, list[str]] = {}

    for line in lines:
        match = re.match(r"^([アイウエィ工I1↑])\s*(.*)$", line)
        if match:
            current_choice = normalize_choice_label(match.group(1))
            choices[current_choice] = [match.group(2).strip()]
            continue
        if current_choice is not None:
            choices[current_choice].append(line)
        else:
            prompt_lines.append(line)

    normalized_choices = {
        key: normalize_spacing("".join(parts))
        for key, parts in choices.items()
    }
    return "\n".join(prompt_lines).strip(), normalized_choices


def normalize_choice_label(label: str) -> str:
    return {
        "ィ": "イ",
        "1": "イ",
        "↑": "イ",
        "I": "エ",
        "工": "エ",
    }.get(label, label)


def normalize_spacing(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([。，、．：；])", r"\1", text)
    return text.strip()


def trim_prompt_for_figure(exam_id: str, question_no: int, prompt: str) -> str:
    cutoff = MANUAL_QUESTION_TEXT_CUTOFFS_BY_EXAM.get(exam_id, {}).get(question_no)
    if not cutoff:
        return prompt
    return prompt.split(cutoff, 1)[0].strip()


def has_figure_hint(question_no: int, prompt: str, figures: dict[int, list[dict[str, str]]]) -> bool:
    if figures.get(question_no):
        return True
    return any(token in prompt for token in ["図は", "図1", "図 1", "表は", "次の図", "次の表"])


def build_exam(
    answers: dict[int, str],
    exam_id: str,
    page_text: dict[int, str] | None = None,
    figures: dict[int, list[dict[str, str]]] | None = None,
    title: str = "ITサービスマネージャ 午前II",
    year: int | None = None,
    era: str = "",
    season: str = "",
    explanations: dict[int, dict] | None = None,
) -> dict:
    questions = []
    page_text = page_text or {}
    figures = figures or {}
    explanations = explanations or {}
    question_slices = slice_questions(page_text)
    choice_patches = MANUAL_CHOICE_PATCHES_BY_EXAM.get(exam_id, {})
    for question_no in range(1, 26):
        question_slice = question_slices[question_no]
        page_no = question_slice.page_no
        raw_text = question_slice.raw_text
        prompt, choices = split_prompt_and_choices(raw_text)
        prompt = trim_prompt_for_figure(exam_id, question_no, prompt)
        choices.update(choice_patches.get(question_no, {}))
        questions.append(
            {
                "id": f"{exam_id}-{question_no:03d}",
                "questionNo": question_no,
                "pageNo": page_no,
                "rawText": raw_text,
                "question": prompt,
                "choices": choices,
                "figures": figures.get(question_no, []),
                "hasFigureHint": has_figure_hint(question_no, prompt, figures),
                "answer": answers[question_no],
                "category": None,
                "explanation": explanations.get(question_no),
                "source": f"{era} {season} ITサービスマネージャ試験 午前II 問{question_no}".strip(),
            }
        )
    return {
        "id": exam_id,
        "title": title,
        "year": year,
        "era": era,
        "season": season,
        "seasonLabel": season,
        "exam": "ITサービスマネージャ",
        "section": "午前II",
        "questionCount": 25,
        "notes": (
            "問題PDFは画像OCRでテキスト化。図表が必要な問題は切り抜き画像を併用。"
            + ("選択肢別解説はレビュー済み。分野分類は未実施。"
               if explanations else "解説、分野分類は未実施。")
            + "OCR結果には軽微な誤字が残る場合があります。"
        ),
        "questions": questions,
    }


def load_explanations(data_dir: Path, exam_id: str) -> dict[int, dict]:
    path = data_dir / "explanations" / f"{exam_id}.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {int(question_no): explanation for question_no, explanation in payload.items()}


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upsert_exam_index(index_path: Path, exam_id: str, title: str, exam_path: Path) -> None:
    if index_path.exists():
        items = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        items = []
    item = {
        "id": exam_id,
        "title": title,
        "path": str(exam_path),
    }
    replaced = False
    for idx, existing in enumerate(items):
        if existing.get("id") == exam_id:
            items[idx] = item
            replaced = True
            break
    if not replaced:
        items.append(item)
    write_json(index_path, items)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--exam-id", default="2025-spring-sm-am2")
    parser.add_argument("--title", default=None)
    parser.add_argument("--year", type=int)
    parser.add_argument("--era", default="")
    parser.add_argument("--season", default="春期")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--ocr-script", type=Path, default=Path("scripts/ocr_image.swift"))
    args = parser.parse_args()

    assets_dir = args.data_dir / "assets" / args.exam_id / "pages"
    image_paths = extract_page_images(args.questions, assets_dir)
    figures = crop_question_figures(image_paths, args.exam_id, args.data_dir)
    answers = parse_answers(args.answers)
    page_text = ocr_pages(image_paths, args.ocr_script) if args.ocr else None
    explanations = load_explanations(args.data_dir, args.exam_id)
    title = args.title or f"{args.year or ''}年 {args.season} ITサービスマネージャ 午前II".strip()
    exam = build_exam(
        answers,
        args.exam_id,
        page_text,
        figures,
        title=title,
        year=args.year,
        era=args.era,
        season=args.season,
        explanations=explanations,
    )
    exam_path = args.data_dir / "exams" / f"{args.exam_id}.json"
    write_json(exam_path, exam)
    upsert_exam_index(args.data_dir / "exams" / "index.json", args.exam_id, exam["title"], exam_path)
    print(f"Wrote {exam_path}")


if __name__ == "__main__":
    main()
