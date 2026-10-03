const state = {
  exams: [],
  examCache: {},
  exam: null,
  mode: "all",
  questionType: "all",
  calculationPattern: "all",
  queue: [],
  index: 0,
  sessionResults: {},
  selectedAnswer: null,
};

const els = {
  examSelect: document.querySelector("#examSelect"),
  questionTypeSelect: document.querySelector("#questionTypeSelect"),
  calculationPatternSelect: document.querySelector("#calculationPatternSelect"),
  filterSummary: document.querySelector("#filterSummary"),
  startButton: document.querySelector("#startButton"),
  resetExamButton: document.querySelector("#resetExamButton"),
  resetButton: document.querySelector("#resetButton"),
  exportHistoryButton: document.querySelector("#exportHistoryButton"),
  importHistoryButton: document.querySelector("#importHistoryButton"),
  historyFileInput: document.querySelector("#historyFileInput"),
  historyStatus: document.querySelector("#historyStatus"),
  modeButtons: [...document.querySelectorAll(".mode-button")],
  emptyState: document.querySelector("#emptyState"),
  quizCard: document.querySelector("#quizCard"),
  sourceLabel: document.querySelector("#sourceLabel"),
  questionTitle: document.querySelector("#questionTitle"),
  categoryLabel: document.querySelector("#categoryLabel"),
  calculationLabel: document.querySelector("#calculationLabel"),
  questionPosition: document.querySelector("#questionPosition"),
  ocrFlagButton: document.querySelector("#ocrFlagButton"),
  questionText: document.querySelector("#questionText"),
  figureList: document.querySelector("#figureList"),
  choiceList: document.querySelector("#choiceList"),
  submitAnswerButton: document.querySelector("#submitAnswerButton"),
  uncertainInput: document.querySelector("#uncertainInput"),
  feedback: document.querySelector("#feedback"),
  explanationPanel: document.querySelector("#explanationPanel"),
  prevButton: document.querySelector("#prevButton"),
  nextButton: document.querySelector("#nextButton"),
  progressList: document.querySelector("#progressList"),
  totalAnswered: document.querySelector("#totalAnswered"),
  accuracy: document.querySelector("#accuracy"),
  wrongCount: document.querySelector("#wrongCount"),
  categoryStatsBody: document.querySelector("#categoryStatsBody"),
};

const storageKey = "itsm-am2-progress-v1";
const historyExportVersion = 2;

function readProgress() {
  try {
    return normalizeProgress(JSON.parse(localStorage.getItem(storageKey)));
  } catch {
    return emptyProgress();
  }
}

function writeProgress(progress) {
  localStorage.setItem(storageKey, JSON.stringify(normalizeProgress(progress)));
}

function emptyProgress() {
  return { answers: {}, lastWrong: [], flags: {}, everWrong: {} };
}

function normalizeProgress(progress) {
  if (!progress || typeof progress !== "object") return emptyProgress();
  const answers = progress.answers && typeof progress.answers === "object" ? progress.answers : {};
  const lastWrong = Array.isArray(progress.lastWrong) ? progress.lastWrong.filter(Boolean) : [];
  const flags = progress.flags && typeof progress.flags === "object" ? progress.flags : {};
  const everWrong = progress.everWrong && typeof progress.everWrong === "object" ? progress.everWrong : {};
  Object.entries(answers).forEach(([id, record]) => {
    if (record && record.correct === false) everWrong[id] = true;
  });
  lastWrong.forEach((id) => { everWrong[id] = true; });
  return { answers, lastWrong, flags, everWrong };
}

function setHistoryStatus(message, isError = false) {
  els.historyStatus.textContent = message;
  els.historyStatus.classList.toggle("error", isError);
}

function exportHistory() {
  const progress = readProgress();
  const payload = {
    app: "itsm-am2-trainer",
    version: historyExportVersion,
    exportedAt: new Date().toISOString(),
    progress,
  };
  const text = JSON.stringify(payload, null, 2);
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const date = new Date().toISOString().slice(0, 10).replaceAll("-", "");
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `itsm-am2-history-${date}.txt`;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  setHistoryStatus("履歴ファイルを書き出しました。");
}

function parseHistoryFile(text) {
  const parsed = JSON.parse(text);
  if (parsed?.app === "itsm-am2-trainer" && parsed.progress) {
    return normalizeProgress(parsed.progress);
  }
  return normalizeProgress(parsed);
}

function mergeProgress(current, imported) {
  const merged = normalizeProgress(current);
  const importedProgress = normalizeProgress(imported);
  let importedCount = 0;
  let importedFlagCount = 0;

  Object.entries(importedProgress.answers).forEach(([id, record]) => {
    if (!record || typeof record !== "object") return;
    const existing = merged.answers[id];
    if (!existing || isImportedNewer(existing, record)) {
      merged.answers[id] = record;
      importedCount += 1;
    }
  });

  merged.lastWrong = [...new Set([...(merged.lastWrong || []), ...(importedProgress.lastWrong || [])])];
  merged.everWrong = { ...merged.everWrong, ...importedProgress.everWrong };
  Object.entries(importedProgress.flags).forEach(([id, flag]) => {
    if (!flag || typeof flag !== "object") return;
    const existing = merged.flags[id];
    if (!existing || isImportedNewer(existing, flag)) {
      merged.flags[id] = flag;
      importedFlagCount += 1;
    }
  });
  return { progress: merged, importedCount, importedFlagCount };
}

function isImportedNewer(existing, imported) {
  const existingTime = existing?.answeredAt || existing?.markedAt;
  const importedTime = imported?.answeredAt || imported?.markedAt;
  if (!existingTime) return true;
  if (!importedTime) return false;
  return new Date(importedTime).getTime() >= new Date(existingTime).getTime();
}

async function importHistoryFile(file) {
  if (!file) return;
  try {
    const imported = parseHistoryFile(await file.text());
    const { progress, importedCount, importedFlagCount } = mergeProgress(readProgress(), imported);
    writeProgress(progress);
    state.sessionResults = {};
    renderStats();
    renderProgress();
    renderQuestion();
    setHistoryStatus(`${importedCount}件の回答履歴、${importedFlagCount}件のOCRマークを読み込みました。`);
  } catch (error) {
    console.error(error);
    setHistoryStatus("履歴ファイルを読み込めませんでした。", true);
  } finally {
    els.historyFileInput.value = "";
  }
}

function shuffle(items) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

async function loadIndex() {
  const res = await fetch("data/exams/index.json", { cache: "no-store" });
  if (!res.ok) throw new Error("試験データの一覧を読み込めませんでした。");
  state.exams = await res.json();
  els.examSelect.innerHTML = state.exams
    .map((exam) => `<option value="${exam.id}">${exam.title}</option>`)
    .join("") + '<option value="all-exams">全年度（10回分）</option>';
  const loaded = await Promise.all(state.exams.map(async (exam) => {
    const res = await fetch(exam.path, { cache: "no-store" });
    if (!res.ok) throw new Error(`試験データを読み込めませんでした: ${exam.id}`);
    return [exam.id, await res.json()];
  }));
  state.examCache = Object.fromEntries(loaded);
  updateCalculationPatternOptions();
  updateSelectedExamResetButton();
  renderStats();
}

async function loadExam(id) {
  if (id === "all-exams") {
    state.exam = {
      id,
      title: "全年度",
      questions: Object.values(state.examCache).flatMap((exam) => (
        (exam.questions || []).map((question) => ({ ...question, examYear: exam.year }))
      )),
    };
    return;
  }
  if (state.examCache[id]) {
    state.exam = state.examCache[id];
    return;
  }
  const meta = state.exams.find((exam) => exam.id === id);
  const res = await fetch(meta.path, { cache: "no-store" });
  if (!res.ok) throw new Error("試験データを読み込めませんでした。");
  state.exam = await res.json();
}

function buildQueue() {
  const questions = state.exam.questions.filter((question) => {
    if (state.questionType !== "all" && question.questionType !== state.questionType) return false;
    if (state.calculationPattern !== "all" && question.calculationPattern !== state.calculationPattern) return false;
    return true;
  });
  const progress = readProgress();
  if (state.mode === "wrong") {
    const wrongSet = new Set(progress.lastWrong || []);
    state.queue = questions.filter((question) => wrongSet.has(question.id));
  } else if (state.mode === "weak") {
    state.queue = questions.filter((question) => (
      progress.everWrong?.[question.id] || progress.answers?.[question.id]?.uncertain === true
    ));
  } else if (state.mode === "random") {
    state.queue = shuffle(questions);
  } else {
    state.queue = [...questions];
  }
  state.index = 0;
  state.sessionResults = {};
}

function currentQuestion() {
  return state.queue[state.index];
}

function renderStats() {
  const progress = readProgress();
  const answers = Object.values(progress.answers || {});
  const total = answers.length;
  const correct = answers.filter((answer) => answer.correct).length;
  els.totalAnswered.textContent = String(total);
  els.accuracy.textContent = total ? `${Math.round((correct / total) * 100)}%` : "-";
  els.wrongCount.textContent = String((progress.lastWrong || []).length);
  renderCategoryStats(progress);
}

function allQuestions() {
  return Object.values(state.examCache).flatMap((exam) => exam.questions || []);
}

function questionsForSelectedExam() {
  if (els.examSelect.value === "all-exams") return allQuestions();
  return state.examCache[els.examSelect.value]?.questions || [];
}

function updateSelectedExamResetButton() {
  const allExamsSelected = els.examSelect.value === "all-exams";
  els.resetExamButton.disabled = allExamsSelected;
  els.resetExamButton.title = allExamsSelected
    ? "個別にクリアする試験回を選択してください。"
    : "選択中の試験回の回答結果だけをクリアします。";
}

function resetSelectedExamResults() {
  const examId = els.examSelect.value;
  if (examId === "all-exams") return;

  const questionIds = new Set(questionsForSelectedExam().map((question) => question.id));
  const progress = readProgress();
  const answerCount = [...questionIds].filter((id) => progress.answers?.[id]).length;
  const weakCount = [...questionIds].filter((id) => progress.everWrong?.[id]).length;
  const examTitle = state.exams.find((exam) => exam.id === examId)?.title || "選択中の試験回";

  if (!answerCount && !weakCount && !(progress.lastWrong || []).some((id) => questionIds.has(id))) {
    setHistoryStatus(`${examTitle}にクリアする回答結果はありません。`);
    return;
  }
  if (!window.confirm(`${examTitle}の回答結果をクリアします。OCR確認マークは残ります。よろしいですか？`)) {
    return;
  }

  questionIds.forEach((id) => {
    delete progress.answers[id];
    delete progress.everWrong[id];
    delete state.sessionResults[id];
  });
  progress.lastWrong = (progress.lastWrong || []).filter((id) => !questionIds.has(id));
  writeProgress(progress);

  if (state.exam?.id === examId) {
    buildQueue();
    renderQuestion();
  } else {
    renderStats();
    renderProgress();
  }
  setHistoryStatus(`${examTitle}の回答結果を${answerCount}件クリアしました。OCR確認マークは保持しています。`);
}

function resetAllProgress() {
  if (!window.confirm("全年度の回答履歴とOCR確認マークを全てリセットします。よろしいですか？")) return;
  writeProgress(emptyProgress());
  state.sessionResults = {};
  renderStats();
  renderProgress();
  renderQuestion();
  setHistoryStatus("全年度の履歴をリセットしました。");
}

function matchingFilterCount() {
  return questionsForSelectedExam().filter((question) => {
    if (state.questionType !== "all" && question.questionType !== state.questionType) return false;
    return state.calculationPattern === "all" || question.calculationPattern === state.calculationPattern;
  }).length;
}

function updateCalculationPatternOptions() {
  const previous = state.calculationPattern;
  const patterns = [...new Set(
    questionsForSelectedExam()
      .filter((question) => state.questionType !== "all" && question.questionType === state.questionType)
      .map((question) => question.calculationPattern)
      .filter(Boolean)
  )].sort((a, b) => a.localeCompare(b, "ja"));
  els.calculationPatternSelect.disabled = state.questionType === "all";
  els.calculationPatternSelect.innerHTML = '<option value="all">全パターン</option>'
    + patterns.map((pattern) => `<option value="${escapeHtml(pattern)}">${escapeHtml(pattern)}</option>`).join("");
  state.calculationPattern = patterns.includes(previous) ? previous : "all";
  els.calculationPatternSelect.value = state.calculationPattern;
  updateFilterSummary();
}

function updateFilterSummary() {
  const labels = { all: "すべての問題", calculation: "計算問題", formula: "公式・指標確認" };
  const scope = els.examSelect.value === "all-exams" ? "全年度" : "選択年度";
  const pattern = state.calculationPattern === "all" ? "" : `・${state.calculationPattern}`;
  els.filterSummary.textContent = `${scope}の${labels[state.questionType]}${pattern}：${matchingFilterCount()}問`;
}

function renderCategoryStats(progress) {
  const categories = new Map();
  allQuestions().forEach((question) => {
    const record = progress.answers?.[question.id];
    if (!record) return;
    const category = question.category || "その他";
    const stats = categories.get(category) || { answered: 0, correct: 0, uncertain: 0 };
    stats.answered += 1;
    if (record.correct === true) stats.correct += 1;
    if (record.uncertain === true) stats.uncertain += 1;
    categories.set(category, stats);
  });
  if (!categories.size) {
    els.categoryStatsBody.innerHTML = '<tr><td colspan="5" class="no-category-stats">回答後に表示されます</td></tr>';
    return;
  }
  els.categoryStatsBody.innerHTML = [...categories.entries()]
    .sort(([, a], [, b]) => (a.correct / a.answered) - (b.correct / b.answered))
    .map(([category, stats]) => `
      <tr>
        <th scope="row">${escapeHtml(category)}</th>
        <td>${stats.answered}</td>
        <td>${stats.correct}</td>
        <td>${Math.round((stats.correct / stats.answered) * 100)}%</td>
        <td>${stats.uncertain}</td>
      </tr>`).join("");
}

function renderProgress() {
  const progress = readProgress();
  els.progressList.innerHTML = state.queue
    .map((question, idx) => {
      const record = progress.answers?.[question.id];
      const flag = progress.flags?.[question.id];
      const classes = ["progress-pill"];
      if (idx === state.index) classes.push("current");
      if (record?.correct) classes.push("correct");
      if (record && !record.correct) classes.push("wrong");
      if (flag) classes.push("flagged");
      const flagMark = flag ? `<span class="progress-flag-mark" aria-label="OCR要確認">!</span>` : "";
      const label = question.examYear ? `${String(question.examYear).slice(-2)}-${question.questionNo}` : question.questionNo;
      const title = question.examYear ? `${question.examYear}年 問${question.questionNo}` : `問${question.questionNo}`;
      return `<button type="button" class="${classes.join(" ")}" data-index="${idx}" title="${title}">${label}${flagMark}</button>`;
    })
    .join("");
}

function renderQuestion() {
  const question = currentQuestion();
  if (!question) {
    els.emptyState.classList.remove("hidden");
    els.quizCard.classList.add("hidden");
    els.emptyState.querySelector("h2").textContent = "対象の問題がありません";
    els.emptyState.querySelector("p").textContent = state.mode === "weak"
      ? "現在の条件に一致する苦手問題はありません。"
      : state.mode === "wrong"
        ? "現在の条件に一致する直前ミスはありません。"
        : "試験回・問題種別・計算パターンの条件を変更してください。";
    renderStats();
    renderProgress();
    return;
  }

  els.emptyState.classList.add("hidden");
  els.quizCard.classList.remove("hidden");
  els.sourceLabel.textContent = question.source;
  els.categoryLabel.textContent = question.category || "その他";
  if (question.questionType === "calculation" || question.questionType === "formula") {
    const typeLabel = question.questionType === "calculation" ? "計算問題" : "公式・指標確認";
    els.calculationLabel.textContent = `${typeLabel}・${question.calculationPattern}`;
    els.calculationLabel.classList.remove("hidden");
  } else {
    els.calculationLabel.textContent = "";
    els.calculationLabel.classList.add("hidden");
  }
  els.questionTitle.textContent = question.examYear ? `${question.examYear}年 問${question.questionNo}` : `問${question.questionNo}`;
  els.questionPosition.textContent = `${state.index + 1} / ${state.queue.length}`;
  renderOcrFlagButton(question);
  els.questionText.textContent = question.question || question.rawText || "問題文を読み込めませんでした。";
  els.figureList.innerHTML = renderFigures(question.figures || []);
  els.choiceList.innerHTML = renderChoices(question.choices || {});
  state.selectedAnswer = null;
  els.uncertainInput.checked = false;
  els.uncertainInput.disabled = false;
  els.submitAnswerButton.disabled = true;
  els.submitAnswerButton.textContent = "回答する";
  els.feedback.className = "feedback";
  els.feedback.textContent = "選択肢を選んでから、回答するボタンで判定してください。";
  els.explanationPanel.classList.add("hidden");
  els.explanationPanel.innerHTML = "";
  els.prevButton.disabled = state.index === 0;
  els.nextButton.textContent = state.index === state.queue.length - 1 ? "終了" : "次へ";
  renderStats();
  renderProgress();
}

function renderOcrFlagButton(question) {
  const progress = readProgress();
  const flagged = Boolean(progress.flags?.[question.id]);
  els.ocrFlagButton.classList.toggle("active", flagged);
  els.ocrFlagButton.setAttribute("aria-pressed", String(flagged));
  els.ocrFlagButton.textContent = flagged ? "OCR確認マーク済み" : "OCR要確認";
}

function renderFigures(figures) {
  if (!figures.length) return "";
  return figures
    .map((figure) => (
      `<figure class="question-figure">` +
      `<img src="${escapeHtml(figure.src)}" alt="${escapeHtml(figure.alt || "問題図")}" loading="lazy">` +
      `</figure>`
    ))
    .join("");
}

function renderChoices(choices) {
  const labels = ["ア", "イ", "ウ", "エ"];
  return labels
    .map((label) => {
      const text = choices[label] || "未抽出";
      return `
        <button type="button" class="choice-item" data-answer="${label}" aria-pressed="false">
          <span>${label}</span>
          <p>${escapeHtml(text)}</p>
        </button>
      `;
    })
    .join("");
}

function selectChoice(answer) {
  const question = currentQuestion();
  const answerButtons = [...els.choiceList.querySelectorAll("[data-answer]")];
  if (!question || answerButtons.some((button) => button.disabled)) return;

  state.selectedAnswer = answer;
  answerButtons.forEach((button) => {
    const selected = button.dataset.answer === answer;
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  els.submitAnswerButton.disabled = false;
  els.feedback.className = "feedback";
  els.feedback.textContent = `${answer} を選択中です。回答するボタンで判定します。`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function answerQuestion(answer) {
  const question = currentQuestion();
  const answerButtons = [...els.choiceList.querySelectorAll("[data-answer]")];
  if (!question || !answer || answerButtons.some((button) => button.disabled)) return;

  const correct = answer === question.answer;
  const uncertain = els.uncertainInput.checked;
  const progress = readProgress();
  progress.answers ||= {};
  progress.answers[question.id] = {
    answer,
    correct,
    uncertain,
    answeredAt: new Date().toISOString(),
  };
  state.sessionResults[question.id] = correct;
  if (!correct) progress.everWrong[question.id] = true;
  progress.lastWrong = Object.entries(state.sessionResults)
    .filter(([, isCorrect]) => !isCorrect)
    .map(([id]) => id);
  writeProgress(progress);

  answerButtons.forEach((button) => {
    const value = button.dataset.answer;
    button.disabled = true;
    if (value === question.answer) button.classList.add("correct");
    if (value === answer && !correct) button.classList.add("wrong");
    if (value === answer) button.classList.add("selected");
  });
  els.submitAnswerButton.disabled = true;
  els.uncertainInput.disabled = true;
  els.submitAnswerButton.textContent = "回答済み";
  els.feedback.className = `feedback ${correct ? "correct" : "wrong"}`;
  els.feedback.textContent = correct
    ? `正解です。答えは ${question.answer} です。${uncertain ? "「迷った」と記録しました。" : ""}`
    : `不正解です。正解は ${question.answer} です。${uncertain ? "「迷った」と記録しました。" : ""}`;
  renderExplanation(question, answer);
  renderStats();
  renderProgress();
}

function toggleOcrFlag() {
  const question = currentQuestion();
  if (!question) return;
  const progress = readProgress();
  progress.flags ||= {};
  if (progress.flags[question.id]) {
    delete progress.flags[question.id];
  } else {
    progress.flags[question.id] = {
      type: "ocr",
      markedAt: new Date().toISOString(),
    };
  }
  writeProgress(progress);
  renderOcrFlagButton(question);
  renderProgress();
}

function renderExplanation(question, selectedAnswer) {
  const explanation = question.explanation;
  if (!explanation || typeof explanation !== "object") {
    els.explanationPanel.classList.add("hidden");
    els.explanationPanel.innerHTML = "";
    return;
  }

  const choices = explanation.choices || {};
  const labels = ["ア", "イ", "ウ", "エ"];
  const statusLabel = explanation.reviewed ? "校正済み" : "ドラフト";
  els.explanationPanel.classList.remove("hidden");
  els.explanationPanel.innerHTML = `
    <div class="explanation-head">
      <div>
        <p class="explanation-kicker">解説 ${escapeHtml(statusLabel)}</p>
        <h3>なぜ ${escapeHtml(question.answer)} が正解か</h3>
      </div>
    </div>
    ${explanation.summary ? `<p class="explanation-summary">${escapeHtml(explanation.summary)}</p>` : ""}
    ${explanation.correct ? `<p class="explanation-correct">${escapeHtml(explanation.correct)}</p>` : ""}
    <div class="choice-explanations">
      ${labels
        .map((label) => {
          const classes = ["choice-explanation"];
          if (label === question.answer) classes.push("correct");
          if (label === selectedAnswer) classes.push("selected");
          const badges = [
            label === question.answer ? "正解" : "不正解",
            label === selectedAnswer ? "あなたの回答" : "",
          ].filter(Boolean);
          return `
            <article class="${classes.join(" ")}">
              <div class="choice-explanation-title">
                <strong>${label}</strong>
                <span>${badges.map(escapeHtml).join(" / ")}</span>
              </div>
              <p>${escapeHtml(choices[label] || "この選択肢の解説は未作成です。")}</p>
            </article>
          `;
        })
        .join("")}
    </div>
    ${explanation.note ? `<p class="explanation-note">${escapeHtml(explanation.note)}</p>` : ""}
  `;
}

async function start() {
  await loadExam(els.examSelect.value);
  buildQueue();
  renderQuestion();
}

function bindEvents() {
  els.modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.mode = button.dataset.mode;
      els.modeButtons.forEach((item) => item.classList.toggle("active", item === button));
    });
  });

  els.examSelect.addEventListener("change", () => {
    updateCalculationPatternOptions();
    updateSelectedExamResetButton();
  });
  els.questionTypeSelect.addEventListener("change", () => {
    state.questionType = els.questionTypeSelect.value;
    state.calculationPattern = "all";
    updateCalculationPatternOptions();
  });
  els.calculationPatternSelect.addEventListener("change", () => {
    state.calculationPattern = els.calculationPatternSelect.value;
    updateFilterSummary();
  });

  els.startButton.addEventListener("click", start);
  els.resetExamButton.addEventListener("click", resetSelectedExamResults);
  els.resetButton.addEventListener("click", resetAllProgress);
  els.ocrFlagButton.addEventListener("click", toggleOcrFlag);
  els.exportHistoryButton.addEventListener("click", exportHistory);
  els.importHistoryButton.addEventListener("click", () => {
    els.historyFileInput.click();
  });
  els.historyFileInput.addEventListener("change", (event) => {
    importHistoryFile(event.target.files?.[0]);
  });
  els.choiceList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-answer]");
    if (!button) return;
    selectChoice(button.dataset.answer);
  });
  els.submitAnswerButton.addEventListener("click", () => {
    answerQuestion(state.selectedAnswer);
  });
  els.prevButton.addEventListener("click", () => {
    if (state.index > 0) {
      state.index -= 1;
      renderQuestion();
    }
  });
  els.nextButton.addEventListener("click", () => {
    if (state.index < state.queue.length - 1) {
      state.index += 1;
      renderQuestion();
    } else {
      els.quizCard.classList.add("hidden");
      els.emptyState.classList.remove("hidden");
      els.emptyState.querySelector("h2").textContent = "完了しました";
      els.emptyState.querySelector("p").textContent = "直前ミス・苦手モードで復習できます。";
    }
  });
  els.progressList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-index]");
    if (!button) return;
    state.index = Number(button.dataset.index);
    renderQuestion();
  });
}

async function init() {
  bindEvents();
  renderStats();
  try {
    await loadIndex();
  } catch (error) {
    els.emptyState.querySelector("h2").textContent = "データ未生成です";
    els.emptyState.querySelector("p").textContent = "READMEの手順でPDFからデータを生成してください。";
    console.error(error);
  }
}

init();
