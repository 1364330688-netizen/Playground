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

function detectEnvironment() {
  const userAgent = navigator.userAgent || "";
  const platform = navigator.userAgentData?.platform || navigator.platform || "";
  const touchPoints = navigator.maxTouchPoints || 0;
  const isWindows = /win/i.test(platform) || /\bwindows\b/i.test(userAgent);
  const isAndroid = /\bandroid\b/i.test(userAgent);
  const isIOS = /iPad|iPhone|iPod/.test(userAgent) || (platform === "MacIntel" && touchPoints > 1);
  const isMac = /mac/i.test(platform) || /\bmac os x\b/i.test(userAgent);

  return {
    isWindows,
    isAndroid,
    isIOS,
    isMac,
    shouldUseLiteEffects: isWindows,
  };
}

const environment = detectEnvironment();
document.documentElement.classList.toggle("platform-windows", environment.isWindows);
document.documentElement.classList.toggle("platform-android", environment.isAndroid);
document.documentElement.classList.toggle("performance-lite", environment.shouldUseLiteEffects);

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
let hasUserActivatedAudio = false;
let pendingAutoPronunciation = false;
let lastWordActivationAt = 0;
let pronunciationAudio = null;
let lastPronunciationRequestId = 0;

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

function canUseSpeechSynthesis() {
  return "speechSynthesis" in window && typeof window.SpeechSynthesisUtterance === "function";
}

function ensurePronunciationAudio() {
  if (pronunciationAudio) {
    return pronunciationAudio;
  }

  pronunciationAudio = new Audio();
  pronunciationAudio.preload = "none";
  pronunciationAudio.playsInline = true;
  return pronunciationAudio;
}

function stopRemotePronunciation() {
  if (!pronunciationAudio) {
    return;
  }

  pronunciationAudio.pause();
  pronunciationAudio.currentTime = 0;
}

function stopAllPronunciation() {
  window.clearTimeout(autoPronounceTimer);

  if (canUseSpeechSynthesis()) {
    window.speechSynthesis.cancel();
  }

  stopRemotePronunciation();
}

function buildRemotePronunciationUrls(word) {
  const query = encodeURIComponent(word);
  return [
    `https://dict.youdao.com/dictvoice?audio=${query}&type=2`,
    `https://dict.youdao.com/dictvoice?audio=${query}&type=1`,
  ];
}

function animateBubbleLetters(letters, duration) {
  const centerIndex = (letters.length - 1) / 2;

  letters.forEach((letter, index) => {
    if (letter.dataset.space === "true" || typeof letter.animate !== "function") {
      return;
    }

    const distanceFromCenter = index - centerIndex;
    const spreadBias = distanceFromCenter * randomBetween(1.8, 3.6);
    const wiggle = randomBetween(4.8, 10.8);
    const liftBias = randomBetween(-4.5, 4.5) - Math.abs(distanceFromCenter) * 0.45;
    const sideBurst = randomBetween(-wiggle * 1.2, wiggle * 1.2);
    const sideBurstLate = randomBetween(-wiggle * 1.75, wiggle * 1.75);
    const sideReturn = randomBetween(-wiggle * 0.7, wiggle * 0.7);
    const verticalBurst = randomBetween(-wiggle * 1.4, wiggle * 0.35);
    const verticalBurstLate = randomBetween(-wiggle * 2.4, wiggle * 0.55);
    const hoverLift = randomBetween(-wiggle * 2.9, -wiggle * 1.3);
    const startRotate = randomBetween(-3.8, 3.8);
    const midRotate = startRotate + randomBetween(-5.6, 5.6);
    const endRotate = midRotate + randomBetween(-6.4, 6.4);
    const returnRotate = endRotate + randomBetween(-3.5, 3.5);
    const delay = Math.max(0, randomBetween(0, 180) + Math.abs(distanceFromCenter) * 14);
    const driftDuration = duration + randomBetween(-220, 420);

    letter.animate(
      [
        {
          opacity: 0,
          transform: `translate3d(0px, 0px, 0) rotate(${startRotate}deg) scale(0.94)`,
        },
        {
          offset: 0.16,
          opacity: 1,
          transform: `translate3d(${Math.round(spreadBias * 0.18 + sideBurst * 0.24)}px, ${Math.round(randomBetween(-wiggle * 0.48, wiggle * 0.2) + liftBias * 0.24)}px, 0) rotate(${Math.round(startRotate * 0.55)}deg) scale(1)`,
        },
        {
          offset: 0.48,
          opacity: 1,
          transform: `translate3d(${Math.round(spreadBias * 0.46 + sideBurst * 0.7)}px, ${Math.round(verticalBurst + liftBias)}px, 0) rotate(${midRotate}deg) scale(1.03)`,
        },
        {
          offset: 0.68,
          opacity: 0.9,
          transform: `translate3d(${Math.round(spreadBias * 0.82 + sideBurstLate * 0.82)}px, ${Math.round(verticalBurstLate + liftBias * 1.52)}px, 0) rotate(${endRotate}deg) scale(1.02)`,
        },
        {
          offset: 0.84,
          opacity: 0.82,
          transform: `translate3d(${Math.round(spreadBias * 0.72 + sideReturn)}px, ${Math.round(hoverLift + liftBias * 1.8)}px, 0) rotate(${returnRotate}deg) scale(1.01)`,
        },
        {
          offset: 0.93,
          opacity: 0.58,
          transform: `translate3d(${Math.round(spreadBias * 0.9 + sideBurstLate * 0.46)}px, ${Math.round(hoverLift + randomBetween(-wiggle * 0.7, wiggle * 0.16) + liftBias * 1.95)}px, 0) rotate(${Math.round(returnRotate + randomBetween(-2.4, 2.4))}deg) scale(0.995)`,
        },
        {
          opacity: 0.46,
          transform: `translate3d(${Math.round(spreadBias * 1.08 + sideBurstLate)}px, ${Math.round(verticalBurstLate + randomBetween(-wiggle * 0.8, wiggle * 0.24) + liftBias * 1.95)}px, 0) rotate(${Math.round(endRotate + randomBetween(-4.5, 4.5))}deg) scale(0.99)`,
        },
      ],
      {
        duration: driftDuration,
        delay,
        easing: "cubic-bezier(0.22, 0.72, 0.2, 1)",
        fill: "both",
      }
    );
  });
}

function createMemoryBubble(value, isCorrect) {
  const bubble = document.createElement("div");
  const laneWidth = elements.bubbleLane.clientWidth || elements.wordCard.clientWidth || 600;
  const laneHeight = elements.bubbleLane.clientHeight || elements.wordCard.clientHeight || 420;
  const mainWordSize = parseFloat(window.getComputedStyle(elements.wordText).fontSize) || 96;
  const widthBasedSize = (laneWidth * 0.76) / Math.max(value.length * 0.52, 1);
  const fontSize = Math.max(36, Math.min(mainWordSize * 0.5, widthBasedSize, 96));
  const wordShell = document.createElement("div");
  const letters = [];
  const startTilt = randomBetween(-1.8, 1.8);
  const midTilt = startTilt + randomBetween(-2.4, 2.4);
  const endTilt = midTilt + randomBetween(-2.8, 2.8);
  const returnTilt = endTilt + randomBetween(-1.8, 1.8);
  const duration = environment.shouldUseLiteEffects
    ? randomBetween(2860, 3720)
    : randomBetween(3480, 4580);

  bubble.className = `memory-bubble ${isCorrect ? "memory-bubble-success" : "memory-bubble-error"}`;
  wordShell.className = "memory-bubble-word";
  bubble.style.fontSize = `${fontSize}px`;
  [...value].forEach((character) => {
    const letter = document.createElement("span");
    const isSpace = character === " ";
    letter.className = `memory-bubble-letter${isSpace ? " memory-bubble-letter-space" : ""}`;
    letter.dataset.space = isSpace ? "true" : "false";
    letter.textContent = isSpace ? "\u00A0" : character;
    wordShell.appendChild(letter);
    letters.push(letter);
  });
  bubble.appendChild(wordShell);
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
    Math.max(-110, maxLeftDrift),
    Math.min(110, maxRightDrift)
  );
  const curveTwoX = curveOneX + randomBetween(-68, 68);
  const endX = curveTwoX + randomBetween(-52, 52);
  const returnX = endX + randomBetween(-34, 34);
  const finalX = endX + randomBetween(-34, 34);
  const rise = -randomBetween(laneHeight * 0.58, laneHeight - bubbleHeight - 8);

  bubble.style.left = `${startLeft}px`;
  bubble.style.bottom = `${startBottom}px`;

  const keyframes = environment.shouldUseLiteEffects
    ? [
        {
          opacity: 0,
          transform: `translate3d(0px, 0px, 0) scale(0.94) rotate(${startTilt}deg)`,
        },
        {
          offset: 0.18,
          opacity: 1,
          transform: `translate3d(${Math.round(curveOneX)}px, -14px, 0) scale(1.01) rotate(${Math.round(startTilt * 0.45)}deg)`,
        },
        {
          offset: 0.5,
          opacity: 0.94,
          transform: `translate3d(${Math.round(curveTwoX)}px, ${Math.round(rise * 0.44)}px, 0) scale(1.03) rotate(${midTilt}deg)`,
        },
        {
          offset: 0.82,
          opacity: 0.48,
          transform: `translate3d(${Math.round(returnX)}px, ${Math.round(rise * 0.86)}px, 0) scale(1.03) rotate(${returnTilt}deg)`,
        },
        {
          opacity: 0,
          transform: `translate3d(${Math.round(finalX)}px, ${Math.round(rise)}px, 0) scale(1.04) rotate(${Math.round(endTilt + randomBetween(-2, 2))}deg)`,
        },
      ]
    : [
        {
          opacity: 0,
          filter: "blur(0.7px)",
          transform: `translate3d(0px, 0px, 0) scale(0.92) rotate(${startTilt}deg)`,
        },
        {
          offset: 0.16,
          opacity: 1,
          filter: "blur(0px)",
          transform: `translate3d(${Math.round(curveOneX)}px, -16px, 0) scale(1.01) rotate(${Math.round(startTilt * 0.35)}deg)`,
        },
        {
          offset: 0.46,
          opacity: 0.98,
          filter: "blur(0px)",
          transform: `translate3d(${Math.round(curveTwoX)}px, ${Math.round(rise * 0.42)}px, 0) scale(1.03) rotate(${midTilt}deg)`,
        },
        {
          offset: 0.72,
          opacity: 0.72,
          filter: "blur(0.12px)",
          transform: `translate3d(${Math.round(endX)}px, ${Math.round(rise * 0.76)}px, 0) scale(1.04) rotate(${endTilt}deg)`,
        },
        {
          offset: 0.88,
          opacity: 0.52,
          filter: "blur(0.2px)",
          transform: `translate3d(${Math.round(returnX)}px, ${Math.round(rise * 0.88)}px, 0) scale(1.025) rotate(${returnTilt}deg)`,
        },
        {
          opacity: 0,
          filter: "blur(0.95px)",
          transform: `translate3d(${Math.round(finalX)}px, ${Math.round(rise)}px, 0) scale(1.05) rotate(${Math.round(endTilt + randomBetween(-2, 2))}deg)`,
        },
      ];

  if (!environment.shouldUseLiteEffects) {
    animateBubbleLetters(letters, duration);
  }

  if (typeof bubble.animate === "function") {
    const animation = bubble.animate(keyframes, {
      duration,
      easing: "cubic-bezier(0.18, 0.7, 0.2, 1)",
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

function speakWithSpeechSynthesis(word) {
  if (!canUseSpeechSynthesis()) {
    return false;
  }

  const utterance = new SpeechSynthesisUtterance(word);
  const voice = pickVoice();

  utterance.lang = voice?.lang || "en-US";
  utterance.voice = voice;
  utterance.rate = 0.86;
  utterance.pitch = 0.98;

  window.speechSynthesis.cancel();
  window.speechSynthesis.resume();
  window.speechSynthesis.speak(utterance);
  return true;
}

async function playRemotePronunciation(word, requestId) {
  const audio = ensurePronunciationAudio();
  const sources = buildRemotePronunciationUrls(word);

  for (const source of sources) {
    if (requestId !== lastPronunciationRequestId) {
      return false;
    }

    try {
      audio.pause();
      audio.currentTime = 0;
      audio.src = source;
      audio.load();

      const playPromise = audio.play();
      if (playPromise && typeof playPromise.then === "function") {
        await playPromise;
      }

      return true;
    } catch (error) {
      audio.pause();
      audio.removeAttribute("src");
    }
  }

  return false;
}

async function pronounceCurrentWord(options = {}) {
  const { force = false } = options;
  const canSpeakNow = force || hasUserActivatedAudio || navigator.userActivation?.hasBeenActive;
  if (!canSpeakNow) {
    pendingAutoPronunciation = true;
    return false;
  }

  const currentWord = getCurrentWord();
  const requestId = ++lastPronunciationRequestId;

  stopAllPronunciation();

  let didPlay = false;

  if (environment.isAndroid) {
    didPlay = await playRemotePronunciation(currentWord.word, requestId);
    if (!didPlay) {
      didPlay = speakWithSpeechSynthesis(currentWord.word);
    }
  } else {
    didPlay = speakWithSpeechSynthesis(currentWord.word);
    if (!didPlay) {
      didPlay = await playRemotePronunciation(currentWord.word, requestId);
    }
  }

  if (!didPlay && !force) {
    pendingAutoPronunciation = true;
    return false;
  }

  pendingAutoPronunciation = false;
  return didPlay;
}

function scheduleAutoPronunciation(delay = 120) {
  window.clearTimeout(autoPronounceTimer);
  autoPronounceTimer = window.setTimeout(() => {
    pronounceCurrentWord().catch(() => {
      pendingAutoPronunciation = true;
    });
  }, delay);
}

function unlockAudioAndReplayPending() {
  if (hasUserActivatedAudio) {
    return;
  }

  hasUserActivatedAudio = true;
  window.speechSynthesis?.resume?.();

  if (pendingAutoPronunciation) {
    pendingAutoPronunciation = false;
    scheduleAutoPronunciation(120);
  }
}

function activateWordPronunciation(event) {
  if (event.type === "keydown" && event.key !== "Enter" && event.key !== " ") {
    return;
  }

  if (event.cancelable) {
    event.preventDefault();
  }
  event.stopPropagation();

  const now = Date.now();
  if (event.type === "click" && now - lastWordActivationAt < 320) {
    return;
  }

  lastWordActivationAt = now;
  unlockAudioAndReplayPending();
  pronounceCurrentWord({ force: true }).catch(() => {});
}

elements.memoryForm.addEventListener("submit", submitMemory);
elements.prevButton.addEventListener("click", () => nextWord(-1));
elements.nextButton.addEventListener("click", () => nextWord(1));
elements.wordText.addEventListener("pointerdown", (event) => {
  if (event.pointerType !== "mouse" && event.cancelable) {
    event.preventDefault();
  }
});
elements.wordText.addEventListener("pointerup", activateWordPronunciation);
elements.wordText.addEventListener("click", activateWordPronunciation);
elements.wordText.addEventListener("keydown", activateWordPronunciation);

document.addEventListener("pointerdown", unlockAudioAndReplayPending, {
  capture: true,
  once: true,
  passive: true,
});
document.addEventListener("keydown", unlockAudioAndReplayPending, {
  capture: true,
  once: true,
});

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
    pronounceCurrentWord({ force: true }).catch(() => {});
  }
});

if (canUseSpeechSynthesis()) {
  window.speechSynthesis.onvoiceschanged = loadVoices;
}

loadVoices();
render();
