const fallbackVocabulary = [
  {
    word: "computer",
    chunks: ["com", "pu", "ter"],
    phonetic: "/kəmˈpjuː.t̬ɚ/",
    meaning: "计算机",
  },
];

const vocabulary = Array.isArray(window.VOCABULARY) && window.VOCABULARY.length
  ? window.VOCABULARY
  : Array.isArray(window.vocabulary) && window.vocabulary.length
    ? window.vocabulary
    : fallbackVocabulary;

const elements = {
  wordCard: document.getElementById("wordCard"),
  wordText: document.getElementById("wordText"),
  phoneticText: document.getElementById("phoneticText"),
  meaningText: document.getElementById("meaningText"),
  bubbleLane: document.getElementById("bubbleLane"),
  memoryForm: document.getElementById("memoryForm"),
  memoryInput: document.getElementById("memoryInput"),
  prevButton: document.getElementById("prevButton"),
  nextButton: document.getElementById("nextButton"),
};

function buildShuffledOrder(excludeIndex = null) {
  const order = vocabulary.map((_, index) => index);

  for (let index = order.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [order[index], order[swapIndex]] = [order[swapIndex], order[index]];
  }

  if (excludeIndex !== null && order.length > 1 && order[0] === excludeIndex) {
    const swapIndex = 1 + Math.floor(Math.random() * (order.length - 1));
    [order[0], order[swapIndex]] = [order[swapIndex], order[0]];
  }

  return order;
}

const state = {
  order: buildShuffledOrder(),
  currentPosition: 0,
};

let availableVoices = [];
let autoPronounceTimer = null;

function getCurrentWord() {
  const currentIndex = state.order[state.currentPosition] ?? 0;
  return vocabulary[currentIndex];
}

function animateCard() {
  elements.wordCard.classList.remove("pulse");
  requestAnimationFrame(() => elements.wordCard.classList.add("pulse"));
}

function updateWordTypography(word, chunks) {
  const chunkCount = chunks.length;
  const letters = word.word.length;
  const stickyPairs = /(rr|mm|nn|ll|tt|ff|rn|rm|mn|vv|ww)/i.test(word.word);
  const seamPairs = chunks.slice(0, -1).map((chunk, index) => {
    const nextChunk = chunks[index + 1];
    return `${chunk.at(-1) || ""}${nextChunk[0] || ""}`.toLowerCase();
  });
  const seamSensitive = seamPairs.some((pair) =>
    /^(ve|we|ye|va|vo|wo|wa|fo|fe|rv|ry|rn|rm|nn|mm|ll|tt|ff)$/.test(pair)
  );

  elements.wordText.classList.toggle("word-mark-single", chunkCount === 1);

  let wordTrack = "-0.02em";
  let chunkSeam = "0em";

  if (chunkCount === 1) {
    wordTrack = stickyPairs || letters <= 5 ? "0.01em" : "-0.004em";
  } else if (letters >= 11) {
    wordTrack = "-0.014em";
    chunkSeam = seamSensitive ? "-0.05em" : "-0.036em";
  } else if (letters <= 6) {
    wordTrack = "-0.008em";
    chunkSeam = seamSensitive ? "-0.055em" : "-0.044em";
  } else {
    wordTrack = "-0.012em";
    chunkSeam = seamSensitive ? "-0.052em" : "-0.04em";
  }

  elements.wordText.style.setProperty("--word-track", wordTrack);
  elements.wordText.style.setProperty("--chunk-seam", chunkSeam);

  const phoneticLength = (word.phonetic || "").replaceAll("/", "").length;
  const phoneticTrack = phoneticLength <= 6 ? "0.05em" : phoneticLength >= 12 ? "0.03em" : "0.04em";
  elements.phoneticText.style.setProperty("--phonetic-track", phoneticTrack);
}

function renderWordChunks(word) {
  const fragment = document.createDocumentFragment();
  const chunks = word.chunks?.length ? word.chunks : [word.word];

  updateWordTypography(word, chunks);

  chunks.forEach((chunk, index) => {
    const span = document.createElement("span");
    const colorIndex = (index % 4) + 1;
    span.className = `word-chunk word-chunk-${colorIndex}`;
    span.textContent = chunk;
    fragment.appendChild(span);
  });

  elements.wordText.replaceChildren(fragment);
}

function render() {
  const currentWord = getCurrentWord();
  renderWordChunks(currentWord);
  elements.phoneticText.textContent = currentWord.phonetic;
  elements.meaningText.textContent = currentWord.meaning;
  animateCard();
  scheduleAutoPronunciation();
}

function nextWord(step) {
  if (step < 0) {
    if (state.currentPosition === 0) {
      return;
    }

    state.currentPosition -= 1;
    render();
    return;
  }

  if (state.currentPosition < state.order.length - 1) {
    state.currentPosition += 1;
    render();
    return;
  }

  const currentIndex = state.order[state.currentPosition];
  state.order.push(...buildShuffledOrder(currentIndex));
  state.currentPosition += 1;
  render();
}

function normalizeWord(value) {
  return value.trim().toLowerCase();
}

function randomBetween(min, max) {
  return Math.random() * (max - min) + min;
}

function createMemoryBubble(value, isCorrect) {
  const bubble = document.createElement("div");
  const laneWidth = elements.bubbleLane.clientWidth || elements.wordCard.clientWidth || 600;
  const laneHeight = elements.bubbleLane.clientHeight || elements.wordCard.clientHeight || 420;
  const mainWordSize = parseFloat(window.getComputedStyle(elements.wordText).fontSize) || 96;
  const widthBasedSize = (laneWidth * 0.72) / Math.max(value.length * 0.56, 1);
  const fontSize = Math.max(30, Math.min(mainWordSize * 0.55, widthBasedSize, 88));
  const startTilt = randomBetween(-5, 5);
  const midTilt = startTilt + randomBetween(-6, 6);
  const endTilt = midTilt + randomBetween(-7, 7);
  const duration = randomBetween(2550, 3400);

  bubble.className = `memory-bubble ${isCorrect ? "memory-bubble-success" : "memory-bubble-error"}`;
  bubble.textContent = value;
  bubble.style.fontSize = `${fontSize}px`;
  elements.bubbleLane.appendChild(bubble);

  const bubbleWidth = bubble.offsetWidth || fontSize * Math.max(value.length * 0.55, 3);
  const bubbleHeight = bubble.offsetHeight || fontSize;
  const sidePadding = 24;
  const lowerBand = Math.max(60, Math.min(180, laneHeight * 0.24));
  const startLeft = randomBetween(
    sidePadding,
    Math.max(sidePadding, laneWidth - bubbleWidth - sidePadding)
  );
  const startBottom = randomBetween(24, lowerBand);
  const maxLeftDrift = -startLeft + 14;
  const maxRightDrift = laneWidth - startLeft - bubbleWidth - 14;
  const curveOneX = randomBetween(
    Math.max(-150, maxLeftDrift),
    Math.min(150, maxRightDrift)
  );
  const curveTwoX = curveOneX + randomBetween(-120, 120);
  const endX = curveTwoX + randomBetween(-120, 120);
  const finalX = endX + randomBetween(-70, 70);
  const rise = -randomBetween(laneHeight * 0.52, laneHeight - bubbleHeight - 18);

  bubble.style.left = `${startLeft}px`;
  bubble.style.bottom = `${startBottom}px`;

  const keyframes = [
    {
      opacity: 0,
      filter: "blur(1px)",
      transform: `translate3d(0px, 0px, 0) scale(0.9) rotate(${startTilt}deg)`,
    },
    {
      offset: 0.14,
      opacity: 1,
      filter: "blur(0px)",
      transform: `translate3d(${Math.round(curveOneX)}px, -24px, 0) scale(1) rotate(${startTilt * 0.4}deg)`,
    },
    {
      offset: 0.42,
      opacity: 0.98,
      filter: "blur(0px)",
      transform: `translate3d(${Math.round(curveTwoX)}px, ${Math.round(rise * 0.42)}px, 0) scale(1.03) rotate(${midTilt}deg)`,
    },
    {
      offset: 0.74,
      opacity: 0.52,
      filter: "blur(0.25px)",
      transform: `translate3d(${Math.round(endX)}px, ${Math.round(rise * 0.76)}px, 0) scale(1.06) rotate(${endTilt}deg)`,
    },
    {
      opacity: 0,
      filter: "blur(1.4px)",
      transform: `translate3d(${Math.round(finalX)}px, ${Math.round(rise)}px, 0) scale(1.09) rotate(${endTilt + randomBetween(-3, 3)}deg)`,
    },
  ];

  if (typeof bubble.animate === "function") {
    const animation = bubble.animate(keyframes, {
      duration,
      easing: "cubic-bezier(0.22, 0.61, 0.36, 1)",
      fill: "forwards",
    });

    animation.onfinish = () => {
      bubble.remove();
    };
    return;
  }

  bubble.style.opacity = "1";
  bubble.style.transform = `translate3d(${Math.round(curveOneX)}px, -24px, 0)`;
  window.setTimeout(() => bubble.remove(), duration);
}

function submitMemory(event) {
  event.preventDefault();

  const typedValue = elements.memoryInput.value.trim();
  if (!typedValue) {
    return;
  }

  const currentWord = getCurrentWord();
  const isCorrect = normalizeWord(typedValue) === normalizeWord(currentWord.word);

  createMemoryBubble(typedValue, isCorrect);
  elements.memoryInput.value = "";
  elements.memoryInput.focus();
}

function loadVoices() {
  availableVoices = window.speechSynthesis?.getVoices() || [];
}

function pickVoice() {
  if (!availableVoices.length) {
    return null;
  }

  return (
    availableVoices.find((voice) => voice.lang === "en-US") ||
    availableVoices.find((voice) => voice.lang.startsWith("en-")) ||
    availableVoices[0]
  );
}

function pronounceCurrentWord() {
  if (!("speechSynthesis" in window)) {
    return;
  }

  const currentWord = getCurrentWord();
  const utterance = new SpeechSynthesisUtterance(currentWord.word);
  const voice = pickVoice();

  utterance.lang = voice?.lang || "en-US";
  utterance.voice = voice;
  utterance.rate = 0.86;
  utterance.pitch = 0.98;

  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

function scheduleAutoPronunciation() {
  window.clearTimeout(autoPronounceTimer);
  autoPronounceTimer = window.setTimeout(() => {
    pronounceCurrentWord();
  }, 120);
}

elements.memoryForm.addEventListener("submit", submitMemory);
elements.prevButton.addEventListener("click", () => nextWord(-1));
elements.nextButton.addEventListener("click", () => nextWord(1));
elements.wordText.addEventListener("click", pronounceCurrentWord);

window.addEventListener("keydown", (event) => {
  if (document.activeElement === elements.memoryInput) {
    return;
  }

  if (event.key === "ArrowLeft") {
    nextWord(-1);
  }

  if (event.key === "ArrowRight") {
    nextWord(1);
  }

  if (event.key === " " || event.key === "Enter") {
    event.preventDefault();
    pronounceCurrentWord();
  }
});

if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = loadVoices;
}

loadVoices();
render();
