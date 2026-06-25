#!/usr/bin/env bash
set -euo pipefail

rm -rf _site
mkdir -p _site/data

cp index.html app.js styles.css _site/
cp -R data/exams data/assets _site/data/
touch _site/.nojekyll

test -f _site/index.html
test -f _site/data/exams/index.json
