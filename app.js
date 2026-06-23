const PDF_WORKER_URL =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

const INTENT_KEYWORDS = {
  book_travel: [
    "book",
    "flight",
    "hotel",
    "travel",
    "trip",
    "reservation",
    "reserve",
    "airport",
  ],
  cancel_order: ["cancel", "refund", "return", "stop", "void", "order", "purchase"],
  customer_support: [
    "help",
    "support",
    "problem",
    "issue",
    "broken",
    "error",
    "ticket",
    "case",
  ],
  schedule_meeting: [
    "schedule",
    "meeting",
    "call",
    "calendar",
    "appointment",
    "invite",
    "sync",
  ],
  sales_lead: [
    "pricing",
    "quote",
    "demo",
    "buy",
    "purchase",
    "sales",
    "interested",
    "plan",
  ],
};

const STOP_WORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "at",
  "for",
  "from",
  "i",
  "in",
  "is",
  "me",
  "my",
  "of",
  "on",
  "please",
  "the",
  "to",
  "we",
  "with",
]);

const ENTITY_PATTERNS = {
  emails: /\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b/g,
  phones: /(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}/g,
  dates: /\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b/g,
  money: /(?:\$|usd\s*)\d+(?:,\d{3})*(?:\.\d{2})?/gi,
  order_ids: /\b(?:order|ticket|case)[\s#:.-]*([a-z0-9-]{4,})\b/gi,
};

const elements = {
  chooseFile: document.querySelector("#choose-file"),
  chunks: document.querySelector("#chunks"),
  confidence: document.querySelector("#confidence"),
  dropZone: document.querySelector("#drop-zone"),
  entities: document.querySelector("#entities"),
  explanation: document.querySelector("#explanation"),
  fileInput: document.querySelector("#pdf-input"),
  fileName: document.querySelector("#file-name"),
  intent: document.querySelector("#intent"),
  keywords: document.querySelector("#keywords"),
  pages: document.querySelector("#pages"),
  results: document.querySelector("#results"),
  status: document.querySelector("#status"),
  textPreview: document.querySelector("#text-preview"),
  words: document.querySelector("#words"),
};

function normalize(text) {
  return text.toLowerCase().trim().replace(/\s+/g, " ");
}

function tokenize(text) {
  return text
    .replace(/[!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
}

function unique(values) {
  return [...new Set(values)];
}

function extractKeywords(tokens) {
  return unique(tokens.filter((token) => !STOP_WORDS.has(token)));
}

function extractEntities(text) {
  const orderIds = [];
  for (const match of text.matchAll(ENTITY_PATTERNS.order_ids)) {
    orderIds.push(match[1]);
  }

  return {
    emails: text.match(ENTITY_PATTERNS.emails) || [],
    phones: (text.match(ENTITY_PATTERNS.phones) || []).map((phone) => phone.trim()),
    dates: text.match(ENTITY_PATTERNS.dates) || [],
    money: text.match(ENTITY_PATTERNS.money) || [],
    order_ids: orderIds,
  };
}

function scoreIntents(tokens) {
  const tokenSet = new Set(tokens);

  return Object.entries(INTENT_KEYWORDS)
    .map(([intent, keywords]) => {
      const matchedKeywords = keywords.filter((keyword) => tokenSet.has(keyword)).sort();
      return {
        intent,
        score: Number((matchedKeywords.length / keywords.length).toFixed(3)),
        matched_keywords: matchedKeywords,
      };
    })
    .sort((left, right) => right.score - left.score);
}

function parseText(text) {
  if (!text || !text.trim()) {
    throw new Error("No extractable text was found in this PDF.");
  }

  const normalizedText = normalize(text);
  const tokens = tokenize(normalizedText);
  const keywords = extractKeywords(tokens);
  const entities = extractEntities(text);
  const intentScores = scoreIntents(tokens);
  const best = intentScores[0];

  if (best.score === 0) {
    return {
      original_text: text,
      normalized_text: normalizedText,
      intent: "unknown",
      confidence: 0,
      entities,
      keywords,
      explanation: "No configured intent keywords were found, so the parser returned unknown.",
      intent_scores: intentScores,
    };
  }

  return {
    original_text: text,
    normalized_text: normalizedText,
    intent: best.intent,
    confidence: best.score,
    entities,
    keywords,
    explanation: `Matched intent '${best.intent}' because the message contained these keywords: ${best.matched_keywords.join(", ")}.`,
    intent_scores: intentScores,
  };
}

function splitDocument(text) {
  const chunks = text
    .split(/\n\s*\n/g)
    .map((chunk) => chunk.trim())
    .filter(Boolean);

  return chunks.length ? chunks : text.trim() ? [text.trim()] : [];
}

function documentStats(text, pageCount) {
  return {
    characters: text.length,
    words: tokenize(normalize(text)).length,
    lines: text.split(/\r?\n/).length,
    chunks: splitDocument(text).length,
    pages: pageCount,
  };
}

function parseDocument(text, source, pageCount) {
  const overall = parseText(text);
  const chunks = splitDocument(text).map((chunkText, index) => {
    const parsed = parseText(chunkText);
    return {
      chunk_number: index + 1,
      text: chunkText,
      intent: parsed.intent,
      confidence: parsed.confidence,
      entities: parsed.entities,
      keywords: parsed.keywords,
      explanation: parsed.explanation,
    };
  });

  return {
    source,
    document_stats: documentStats(text, pageCount),
    overall,
    chunks,
  };
}

async function extractPdfText(file) {
  if (!window.pdfjsLib) {
    throw new Error("PDF.js could not load. Check your internet connection and refresh.");
  }

  window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDF_WORKER_URL;

  const buffer = await file.arrayBuffer();
  const pdf = await window.pdfjsLib.getDocument({ data: buffer }).promise;
  const pages = [];

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    setStatus(`Reading page ${pageNumber} of ${pdf.numPages}...`);
    const page = await pdf.getPage(pageNumber);
    const content = await page.getTextContent();
    const pageText = content.items.map((item) => item.str).join(" ");
    pages.push(pageText.trim());
  }

  return {
    pageCount: pdf.numPages,
    text: pages.filter(Boolean).join("\n\n"),
  };
}

function setStatus(message, type = "") {
  elements.status.textContent = message;
  elements.status.className = `status ${type}`.trim();
}

function setBusy(isBusy) {
  elements.chooseFile.disabled = isBusy;
  elements.dropZone.setAttribute("aria-busy", String(isBusy));
}

function renderList(label, values) {
  const row = document.createElement("div");
  row.className = "entity-row";

  const title = document.createElement("span");
  title.textContent = label.replace("_", " ");

  const value = document.createElement("div");
  value.textContent = values.length ? unique(values).join(", ") : "None found";

  row.append(title, value);
  return row;
}

function renderChips(container, values) {
  container.replaceChildren();

  if (!values.length) {
    container.textContent = "No keywords found.";
    return;
  }

  values.slice(0, 24).forEach((keyword) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = keyword;
    container.append(chip);
  });
}

function renderChunks(chunks) {
  elements.chunks.replaceChildren();

  chunks.slice(0, 12).forEach((chunk) => {
    const card = document.createElement("div");
    card.className = "chunk";

    const header = document.createElement("div");
    header.className = "chunk-header";

    const title = document.createElement("span");
    title.className = "chunk-title";
    title.textContent = `Chunk ${chunk.chunk_number}`;

    const intent = document.createElement("span");
    intent.className = "chunk-intent";
    intent.textContent = `${chunk.intent} (${Math.round(chunk.confidence * 100)}%)`;

    const text = document.createElement("p");
    text.className = "chunk-text";
    text.textContent = chunk.text;

    header.append(title, intent);
    card.append(header, text);
    elements.chunks.append(card);
  });

  if (chunks.length > 12) {
    const remaining = document.createElement("p");
    remaining.className = "panel-copy";
    remaining.textContent = `${chunks.length - 12} more chunks are hidden in this preview.`;
    elements.chunks.append(remaining);
  }
}

function renderResult(file, result) {
  const { overall, document_stats: stats } = result;

  elements.fileName.textContent = file.name;
  elements.intent.textContent = overall.intent;
  elements.confidence.textContent = `${Math.round(overall.confidence * 100)}%`;
  elements.pages.textContent = String(stats.pages);
  elements.words.textContent = String(stats.words);
  elements.explanation.textContent = overall.explanation;
  elements.textPreview.textContent =
    overall.original_text.slice(0, 5000) ||
    "No text preview is available for this document.";

  elements.entities.replaceChildren(
    renderList("emails", overall.entities.emails),
    renderList("phones", overall.entities.phones),
    renderList("dates", overall.entities.dates),
    renderList("money", overall.entities.money),
    renderList("order_ids", overall.entities.order_ids),
  );
  renderChips(elements.keywords, overall.keywords);
  renderChunks(result.chunks);

  elements.results.hidden = false;
}

async function handleFile(file) {
  if (!file) {
    return;
  }

  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    setStatus("Please choose a PDF file.", "error");
    return;
  }

  try {
    setBusy(true);
    setStatus(`Loading ${file.name}...`);
    const extracted = await extractPdfText(file);
    setStatus("Parsing extracted PDF text...");
    const result = parseDocument(extracted.text, file.name, extracted.pageCount);
    renderResult(file, result);
    setStatus(`Parsed ${file.name}.`, "success");
  } catch (error) {
    const message =
      error && error.message
        ? error.message
        : "Could not parse this PDF. It may be encrypted, scanned, or unreadable.";
    setStatus(message, "error");
  } finally {
    setBusy(false);
  }
}

elements.chooseFile.addEventListener("click", (event) => {
  event.stopPropagation();
  elements.fileInput.click();
});
elements.dropZone.addEventListener("click", () => elements.fileInput.click());
elements.dropZone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    elements.fileInput.click();
  }
});

elements.fileInput.addEventListener("change", (event) => {
  handleFile(event.target.files[0]);
});

["dragenter", "dragover"].forEach((eventName) => {
  elements.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  elements.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    elements.dropZone.classList.remove("dragging");
  });
});

elements.dropZone.addEventListener("drop", (event) => {
  handleFile(event.dataTransfer.files[0]);
});
