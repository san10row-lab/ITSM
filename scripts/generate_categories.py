#!/usr/bin/env python3
"""Build the initial ITSM-oriented category map from question and explanation text."""
from __future__ import annotations

import json
import re
from pathlib import Path


RULES = [
    ("インシデント管理", r"インシデント|エスカレーション|障害受付|復旧優先"),
    ("問題管理", r"問題管理|既知の誤り|既知エラー|根本原因|ワークアラウンド"),
    ("変更・リリース管理", r"変更管理|変更要求|変更諮問|CAB|リリース及び展開|リリース管理|展開管理|本番移行|切替え移行"),
    ("構成管理", r"構成管理|構成アイテム|構成品目|\bCI\b|CMDB|構成ベースライン"),
    ("サービスレベル・契約管理", r"サービスレベル|\bSLA\b|\bOLA\b|サービス水準|サービス報告|契約管理"),
    ("可用性管理", r"可用性|稼働率|\bMTBF\b|\bMTTR\b|\bMTRS\b"),
    ("キャパシティ管理", r"キャパシティ|容量・能力|容量管理|性能管理|スループット|ターンアラウンドタイム"),
    ("ITサービス継続性管理", r"サービス継続|事業継続|BCMS|BCP|RPO|RTO|MTPD|災害時|バックアップサイト|スタンバイ|復旧対策"),
    ("情報セキュリティ管理", r"情報セキュリティ|ISMS|暗号|認証|デジタル署名|証明書|マルウェア|脆弱性|リスクマトリックス|真正性|完全性|機密性|WPA|シングルサインオン|セキュリティ"),
    ("サービスデスク", r"サービスデスク|コールセンタ|\bWFM\b|サービス要求|一次解決"),
    ("サービスカタログ・ポートフォリオ", r"サービス・?カタログ|サービスポートフォリオ|サービス・?ポートフォリオ|サービスパイプライン"),
    ("供給者・事業関係管理", r"供給者管理|サプライヤ|供給者|事業関係管理|顧客関係|利害関係者"),
    ("KPI・測定・改善", r"KPI|重要業績評価指標|継続的.*改善|7ステップ|SMART|測定|パフォーマンス評価|マネジメントレビュー"),
    ("サービスマネジメントシステム", r"JIS [Q0 ]*20000|サービスマネジメントシステム|SMS|サービスライフサイクル|ITIL|サービス・バリュー|力量"),
    ("運用・ファシリティ管理", r"運用管理|運用作業|データセンタ|データセンター|ファシリティ|空調|消火設備|PUE|バックアップ|ジョブ|監視|イベント管理"),
    ("プロジェクト管理", r"プロジェクト|PMBOK|EVM|アーンドバリュー|クリティカルパス|クリティカルチェーン|スケジュール|ステークホルダ|スコープ|調達マネジメント|品質の計画"),
    ("監査・ガバナンス・法務", r"監査|内部統制|法令|法律|契約|下請|労働基準法|36協定|ガバナンス|著作権|個人情報"),
]


def classify(question: dict) -> str:
    explanation = question.get("explanation") or {}
    text = " ".join([question.get("question") or "", explanation.get("summary") or "", explanation.get("correct") or ""])
    matches = [(len(re.findall(pattern, text, re.IGNORECASE)), category) for category, pattern in RULES]
    score, category = max(matches, key=lambda item: item[0])
    return category if score else "その他"


def main() -> None:
    output_dir = Path("data/categories")
    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for exam_path in sorted(Path("data/exams").glob("*.json")):
        if exam_path.name == "index.json":
            continue
        exam = json.loads(exam_path.read_text(encoding="utf-8"))
        categories = {}
        for question in exam["questions"]:
            category = classify(question)
            categories[str(question["questionNo"])] = category
            counts[category] = counts.get(category, 0) + 1
        (output_dir / exam_path.name).write_text(
            json.dumps(categories, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
