# ITSM AM2 Quiz Prototype

ITサービスマネージャ試験 午前IIのPDFを、静的な学習アプリ用データに変換して使うプロトタイプです。

## 方針

- 問題PDFは画像ページとして抽出した後、macOS標準OCRでテキスト化します。
- 図表が必要な問題は、本文・選択肢をテキスト化し、図表だけ切り抜き画像として表示します。
- 解答PDFから正解表を抽出します。
- アプリ実行時はIPAへアクセスせず、生成済みJSONを読み込みます。
- 学習履歴と直前ミスはブラウザのlocalStorageに保存します。

## 過去10回分データの生成

```sh
/Users/takaomakibuchi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_exams.py
```

現在の対象は次の10回分です。

- 2025年 春期
- 2024年 春期
- 2023年 春期
- 2022年 春期
- 2021年 春期
- 2019年 秋期
- 2018年 秋期
- 2017年 秋期
- 2016年 秋期
- 2015年 秋期

2020年度のIPA過去問題ページには、SM午前IIのPDFリンクが見当たらなかったため対象から外しています。

## 1回分だけ再生成

```sh
/Users/takaomakibuchi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/prepare_exam.py \
  --questions "/Users/takaomakibuchi/Downloads/2025r07h_sm_am2_qs.pdf" \
  --answers "/Users/takaomakibuchi/Downloads/2025r07h_sm_am2_ans.pdf" \
  --exam-id "2025-spring-sm-am2" \
  --title "2025年 春期 ITサービスマネージャ 午前II" \
  --year 2025 \
  --era "令和7年度" \
  --season "春期" \
  --ocr
```

## 起動

```sh
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000` を開きます。

## 解説データ

- 2021～2024年は、全25問にレビュー済みの選択肢別解説があります。
- 2025年は、全25問にドラフトの選択肢別解説があります。
- 解説の正本は `data/explanations/` に保存しています。
- PDFから試験データを再生成すると、同じ試験IDの解説が自動的に統合されます。
- 既存の試験JSONへ2021～2024年の解説を再適用する場合は、次を実行します。

```sh
python3 scripts/apply_explanations.py
```

レビュー内容とOCR補正箇所は `data/explanations/REVIEW-2021-2024.md` に記録しています。

## 現在の制約

- 問題本文はOCRを基にしているため、軽微な文字誤りが残る可能性があります。
- 図表つき問題は、現時点で17問をハイブリッド表示の対象にしています。
- 2015～2019年の解説と、全年度の分野分類は未入力です。
