const state = {
  exams: [],
  exam: null,
  mode: "all",
  queue: [],
  index: 0,
  sessionResults: {},
};

const els = {
  examSelect: document.querySelector("#examSelect"),
  startButton: document.querySelector("#startButton"),
  resetButton: document.querySelector("#resetButton"),
  modeButtons: [...document.querySelectorAll(".mode-button")],
  emptyState: document.querySelector("#emptyState"),
  quizCard: document.querySelector("#quizCard"),
  sourceLabel: document.querySelector("#sourceLabel"),
  questionTitle: document.querySelector("#questionTitle"),
  questionPosition: document.querySelector("#questionPosition"),
  questionText: document.querySelector("#questionText"),
  figureList: document.querySelector("#figureList"),
  choiceList: document.querySelector("#choiceList"),
  feedback: document.querySelector("#feedback"),
  explanationPanel: document.querySelector("#explanationPanel"),
  prevButton: document.querySelector("#prevButton"),
  nextButton: document.querySelector("#nextButton"),
  progressList: document.querySelector("#progressList"),
  totalAnswered: document.querySelector("#totalAnswered"),
  accuracy: document.querySelector("#accuracy"),
  wrongCount: document.querySelector("#wrongCount"),
};

const storageKey = "itsm-am2-progress-v1";

function readProgress() {
  try {
    return JSON.parse(localStorage.getItem(storageKey)) || { answers: {}, lastWrong: [] };
  } catch {
    return { answers: {}, lastWrong: [] };
  }
}

function writeProgress(progress) {
  localStorage.setItem(storageKey, JSON.stringify(progress));
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
  const res = await fetch("data/exams/index.json");
  if (!res.ok) throw new Error("試験データの一覧を読み込めませんでした。");
  state.exams = await res.json();
  els.examSelect.innerHTML = state.exams
    .map((exam) => `<option value="${exam.id}">${exam.title}</option>`)
    .join("");
}

async function loadExam(id) {
  const meta = state.exams.find((exam) => exam.id === id);
  const res = await fetch(meta.path);
  if (!res.ok) throw new Error("試験データを読み込めませんでした。");
  state.exam = await res.json();
}

function buildQueue() {
  const questions = state.exam.questions;
  const progress = readProgress();
  if (state.mode === "wrong") {
    const wrongSet = new Set(progress.lastWrong || []);
    state.queue = questions.filter((question) => wrongSet.has(question.id));
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
}

function renderProgress() {
  const progress = readProgress();
  els.progressList.innerHTML = state.queue
    .map((question, idx) => {
      const record = progress.answers?.[question.id];
      const classes = ["progress-pill"];
      if (idx === state.index) classes.push("current");
      if (record?.correct) classes.push("correct");
      if (record && !record.correct) classes.push("wrong");
      return `<button type="button" class="${classes.join(" ")}" data-index="${idx}">${question.questionNo}</button>`;
    })
    .join("");
}

function renderQuestion() {
  const question = currentQuestion();
  if (!question) {
    els.emptyState.classList.remove("hidden");
    els.quizCard.classList.add("hidden");
    els.emptyState.querySelector("h2").textContent = "対象の問題がありません";
    els.emptyState.querySelector("p").textContent = "全問モードで一度回答すると、直前ミスを試せます。";
    renderStats();
    renderProgress();
    return;
  }

  els.emptyState.classList.add("hidden");
  els.quizCard.classList.remove("hidden");
  els.sourceLabel.textContent = question.source;
  els.questionTitle.textContent = `問${question.questionNo}`;
  els.questionPosition.textContent = `${state.index + 1} / ${state.queue.length}`;
  els.questionText.textContent = question.question || question.rawText || "問題文を読み込めませんでした。";
  els.figureList.innerHTML = renderFigures(question.figures || []);
  els.choiceList.innerHTML = renderChoices(question.choices || {});
  els.feedback.className = "feedback";
  els.feedback.textContent = "選択肢を選んでください。問題文はOCRで抽出したテキストです。";
  els.explanationPanel.classList.add("hidden");
  els.explanationPanel.innerHTML = "";
  els.prevButton.disabled = state.index === 0;
  els.nextButton.textContent = state.index === state.queue.length - 1 ? "終了" : "次へ";
  renderStats();
  renderProgress();
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
        <button type="button" class="choice-item" data-answer="${label}">
          <span>${label}</span>
          <p>${escapeHtml(text)}</p>
        </button>
      `;
    })
    .join("");
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
  if (!question || answerButtons.some((button) => button.disabled)) return;

  const correct = answer === question.answer;
  const progress = readProgress();
  progress.answers ||= {};
  progress.answers[question.id] = {
    answer,
    correct,
    answeredAt: new Date().toISOString(),
  };
  state.sessionResults[question.id] = correct;
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
  els.feedback.className = `feedback ${correct ? "correct" : "wrong"}`;
  els.feedback.textContent = correct
    ? `正解です。答えは ${question.answer} です。`
    : `不正解です。正解は ${question.answer} です。`;
  renderExplanation(question, answer);
  renderStats();
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

  els.startButton.addEventListener("click", start);
  els.resetButton.addEventListener("click", () => {
    writeProgress({ answers: {}, lastWrong: [] });
    state.sessionResults = {};
    renderStats();
    renderProgress();
  });
  els.choiceList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-answer]");
    if (!button) return;
    answerQuestion(button.dataset.answer);
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
      els.emptyState.querySelector("p").textContent = "直前ミスモードで復習できます。";
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
