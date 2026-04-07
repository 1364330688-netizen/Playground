#!/usr/bin/env python3

import argparse
import csv
import heapq
import io
import json
import re
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

import eng_to_ipa as ipa
import pyphen

ROOT = Path(__file__).resolve().parent.parent
VOCABULARY_PATH = ROOT / "vocabulary.js"
CACHE_DIR = ROOT / ".cache"
ECDICT_PATH = CACHE_DIR / "ecdict.csv"
ECDICT_URL = "https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv"
TARGET_TOTAL = 2000

us_hyphenator = pyphen.Pyphen(lang="en_US")
gb_hyphenator = pyphen.Pyphen(lang="en_GB")

MEANING_OVERRIDES = {
    "a": "一个；一（不定冠词）",
    "i": "我",
    "the": "这，那（定冠词）",
    "be": "是",
    "and": "和",
    "of": "的",
    "in": "在……里",
    "to": "到，向",
    "it": "它",
    "for": "为了",
    "you": "你",
    "he": "他",
    "on": "在……上",
    "do": "做",
    "say": "说",
    "this": "这",
    "they": "他们",
    "at": "在",
    "but": "但是",
    "we": "我们",
    "his": "他的",
    "from": "从；来自",
    "not": "不",
    "by": "通过；在……旁",
    "she": "她",
    "or": "或者",
    "as": "像；作为",
    "what": "什么",
    "go": "去",
    "their": "他们的",
    "can": "能；可以",
    "who": "谁",
    "get": "得到",
    "if": "如果",
    "would": "将会；愿意",
    "her": "她的；她",
    "all": "全部",
    "my": "我的",
    "make": "制造；使得",
    "when": "何时；当……时候",
    "more": "更多；更",
    "back": "后面；返回",
    "any": "任何",
    "us": "我们",
    "down": "向下",
    "may": "可以；也许",
    "own": "自己的",
    "why": "为什么",
    "begin": "开始",
    "where": "在哪里",
    "american": "美国的；美国人",
    "mr": "先生",
    "next": "下一个；下一次",
    "before": "在……之前",
    "month": "月",
    "different": "不同的",
    "both": "两者都",
    "yes": "是的",
    "bad": "坏的",
    "best": "最好的",
    "boy": "男孩",
    "death": "死亡",
    "behind": "在……后面",
    "development": "发展",
    "better": "更好的；更好地",
    "military": "军事的；军队",
    "international": "国际的",
    "baby": "婴儿",
    "daughter": "女儿",
    "hospital": "医院",
    "thousand": "一千",
    "natural": "自然的",
    "animal": "动物",
    "tv": "电视",
    "save": "挽救；保存",
    "media": "媒体",
    "television": "电视",
    "analysis": "分析",
    "benefit": "益处；好处",
    "lawyer": "律师",
    "gun": "枪",
    "blue": "蓝色的",
    "democratic": "民主的",
    "respond": "回应",
    "manage": "管理",
    "conference": "会议",
    "deep": "深的",
    "tough": "艰难的；强硬的",
    "investment": "投资",
    "consumer": "消费者",
    "budget": "预算",
    "scientist": "科学家",
    "born": "出生的",
    "professional": "专业的；职业的",
    "customer": "顾客",
    "computer": "计算机",
    "people": "人们",
    "business": "商业；生意",
    "family": "家庭",
    "because": "因为",
    "situation": "情况",
    "easy": "容易的",
    "cost": "成本；花费",
    "industry": "工业",
    "figure": "数字；人物",
    "resource": "资源",
    "identify": "识别；认出",
    "participant": "参与者",
    "university": "大学",
    "forest": "森林",
    "answer": "回答；答案",
    "evidence": "证据",
    "medical": "医学的；医疗的",
    "individual": "个人；个体",
    "executive": "行政的；高管",
    "popular": "受欢迎的；流行的",
    "particular": "特定的；特别的",
    "reality": "现实",
    "violence": "暴力",
    "coach": "教练；长途客车",
    "yard": "院子；码",
    "beat": "击打；打败",
    "tradition": "传统",
    "independent": "独立的",
    "apartment": "公寓",
    "potential": "潜力；潜在的",
    "committee": "委员会",
    "leadership": "领导力",
    "favorite": "最喜欢的",
}

PHONETIC_OVERRIDES = {
    "a": "/ə/",
    "i": "/aɪ/",
    "the": "/ðə/",
    "be": "/bi/",
    "and": "/ænd/",
    "of": "/əv/",
    "to": "/tu/",
    "for": "/fɔr/",
    "you": "/ju/",
    "he": "/hi/",
    "we": "/wi/",
    "my": "/maɪ/",
    "by": "/baɪ/",
    "or": "/ɔr/",
    "what": "/wʌt/",
    "can": "/kæn/",
    "one": "/wʌn/",
    "when": "/wen/",
    "where": "/wer/",
    "why": "/waɪ/",
    "there": "/ðer/",
    "their": "/ðer/",
    "your": "/jʊr/",
    "our": "/aʊr/",
    "who": "/hu/",
    "would": "/wʊd/",
    "could": "/kʊd/",
    "should": "/ʃʊd/",
    "computer": "/kəmˈpjuːtər/",
    "tough": "/tʌf/",
}

CHUNK_OVERRIDES = {
    "about": ["a", "bout"],
    "abstain": ["ab", "stain"],
    "abuse": ["ab", "use"],
    "afternoon": ["after", "noon"],
    "again": ["a", "gain"],
    "alive": ["a", "live"],
    "around": ["a", "round"],
    "beautiful": ["beau", "ti", "ful"],
    "comprise": ["com", "prise"],
    "computer": ["com", "pu", "ter"],
    "congratulation": ["con", "gra", "tu", "la", "tion"],
    "event": ["e", "vent"],
    "exist": ["exist"],
    "family": ["fam", "i", "ly"],
    "fire": ["fire"],
    "market": ["mar", "ket"],
    "maybe": ["may", "be"],
    "mistake": ["mis", "take"],
    "morning": ["mor", "ning"],
    "nation": ["na", "tion"],
    "ocean": ["o", "cean"],
    "open": ["o", "pen"],
    "radio": ["ra", "di", "o"],
    "silver": ["sil", "ver"],
    "somehow": ["some", "how"],
    "student": ["stu", "dent"],
    "video": ["vid", "e", "o"],
    "aftermath": ["after", "math"],
    "afternoon": ["after", "noon"],
    "anyway": ["any", "way"],
    "anybody": ["any", "body"],
    "advice": ["ad", "vice"],
    "aspect": ["as", "pect"],
    "attend": ["at", "tend"],
    "active": ["ac", "tive"],
    "because": ["be", "cause"],
    "belong": ["be", "long"],
    "business": ["busi", "ness"],
    "collect": ["col", "lect"],
    "combine": ["com", "bine"],
    "comment": ["com", "ment"],
    "commit": ["com", "mit"],
    "concept": ["con", "cept"],
    "conduct": ["con", "duct"],
    "connect": ["con", "nect"],
    "context": ["con", "text"],
    "contact": ["con", "tact"],
    "define": ["de", "fine"],
    "demand": ["de", "mand"],
    "depend": ["de", "pend"],
    "desire": ["de", "sire"],
    "destroy": ["de", "stroy"],
    "direct": ["di", "rect"],
    "engage": ["en", "gage"],
    "expand": ["ex", "pand"],
    "explore": ["ex", "plore"],
    "express": ["ex", "press"],
    "extend": ["ex", "tend"],
    "people": ["peo", "ple"],
    "freedom": ["free", "dom"],
    "income": ["in", "come"],
    "insist": ["in", "sist"],
    "intend": ["in", "tend"],
    "invite": ["in", "vite"],
    "critic": ["cri", "tic"],
    "nobody": ["no", "body"],
    "observe": ["ob", "serve"],
    "obtain": ["ob", "tain"],
    "plastic": ["plas", "tic"],
    "predict": ["pre", "dict"],
    "recall": ["re", "call"],
    "reform": ["re", "form"],
    "release": ["re", "lease"],
    "remind": ["re", "mind"],
    "repeat": ["re", "peat"],
    "replace": ["re", "place"],
    "respect": ["re", "spect"],
    "review": ["re", "view"],
    "situation": ["sit", "u", "a", "tion"],
    "survive": ["sur", "vive"],
    "unless": ["un", "less"],
    "weekend": ["week", "end"],
    "welcome": ["wel", "come"],
    "political": ["po", "lit", "i", "cal"],
    "contribute": ["con", "tri", "bute"],
    "economic": ["eco", "nom", "ic"],
    "academic": ["ac", "a", "dem", "ic"],
    "democratic": ["de", "mo", "crat", "ic"],
    "dramatic": ["dra", "ma", "tic"],
    "specific": ["spe", "cif", "ic"],
    "scientific": ["sci", "en", "tif", "ic"],
    "automatic": ["au", "to", "mat", "ic"],
    "education": ["ed", "u", "ca", "tion"],
    "evidence": ["ev", "i", "dence"],
    "medical": ["med", "i", "cal"],
    "individual": ["in", "di", "vid", "u", "al"],
    "technology": ["tech", "nol", "o", "gy"],
    "operation": ["op", "er", "a", "tion"],
    "authority": ["au", "thor", "i", "ty"],
    "executive": ["exe", "cu", "tive"],
    "popular": ["pop", "u", "lar"],
    "particular": ["par", "tic", "u", "lar"],
    "reality": ["re", "al", "i", "ty"],
    "violence": ["vi", "o", "lence"],
    "responsibility": ["re", "spon", "si", "bil", "i", "ty"],
    "favorite": ["fa", "vo", "rite"],
    "failure": ["fail", "ure"],
    "memory": ["mem", "o", "ry"],
    "medicine": ["med", "i", "cine"],
    "politician": ["po", "li", "ti", "cian"],
    "progress": ["pro", "gress"],
    "probably": ["pro", "ba", "bly"],
    "growing": ["grow", "ing"],
    "living": ["liv", "ing"],
    "meaning": ["mean", "ing"],
    "reading": ["read", "ing"],
    "writing": ["writ", "ing"],
    "catholic": ["cath", "o", "lic"],
    "democracy": ["de", "moc", "ra", "cy"],
    "democrat": ["dem", "o", "crat"],
    "international": ["in", "ter", "na", "tion", "al"],
    "community": ["com", "mu", "ni", "ty"],
    "organization": ["or", "ga", "ni", "za", "tion"],
    "opportunity": ["op", "por", "tu", "ni", "ty"],
    "administration": ["ad", "min", "is", "tra", "tion"],
    "material": ["ma", "te", "ri", "al"],
    "population": ["pop", "u", "la", "tion"],
    "security": ["se", "cu", "ri", "ty"],
    "natural": ["nat", "u", "ral"],
    "animal": ["an", "i", "mal"],
    "analysis": ["a", "nal", "y", "sis"],
    "benefit": ["ben", "e", "fit"],
    "environmental": ["en", "vi", "ron", "men", "tal"],
    "environment": ["en", "vi", "ron", "ment"],
    "especially": ["es", "pe", "cial", "ly"],
    "development": ["de", "vel", "op", "ment"],
    "relationship": ["re", "la", "tion", "ship"],
    "recommend": ["re", "com", "mend"],
    "activity": ["ac", "tiv", "i", "ty"],
    "actually": ["ac", "tu", "al", "ly"],
    "experience": ["ex", "pe", "ri", "ence"],
    "available": ["a", "vail", "a", "ble"],
    "particularly": ["par", "tic", "u", "lar", "ly"],
    "physical": ["phys", "i", "cal"],
    "strategy": ["strat", "e", "gy"],
    "various": ["var", "i", "ous"],
    "traditional": ["tra", "di", "tion", "al"],
    "popular": ["pop", "u", "lar"],
    "quality": ["qual", "i", "ty"],
    "operation": ["op", "er", "a", "tion"],
    "medical": ["med", "i", "cal"],
    "economic": ["eco", "nom", "ic"],
    "military": ["mil", "i", "tar", "y"],
    "media": ["me", "di", "a"],
}

IPA_SYLLABLE_RE = re.compile(
    r"aɪ|aʊ|eɪ|oʊ|ɔɪ|ju|ɪr|er|ɛr|ʊr|ɔr|ɑr|ɚ|ɝ|[iyɪʊueəɛæʌɑɔɒɜɐo]"
)

COMMON_VOWEL_TEAMS = {
    "ai",
    "ay",
    "ea",
    "ee",
    "ei",
    "eu",
    "ew",
    "ie",
    "oa",
    "oe",
    "oi",
    "oo",
    "ou",
    "ow",
    "oy",
    "au",
    "aw",
    "ui",
    "ue",
    "igh",
}


def ensure_ecdict() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not ECDICT_PATH.exists():
        ECDICT_PATH.write_bytes(urlopen(ECDICT_URL, timeout=120).read())
    return ECDICT_PATH


def rank(value: str) -> int:
    try:
        number = int(value)
    except Exception:
        return 10**9
    return number if number > 0 else 10**9


def load_items() -> list[dict]:
    text = VOCABULARY_PATH.read_text(encoding="utf-8")
    return json.loads(text[text.index("["): text.rindex("]") + 1])


def write_items(items: list[dict]) -> None:
    VOCABULARY_PATH.write_text(
        "window.VOCABULARY = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def contains_chinese(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def clean_segment(value: str) -> str:
    value = value.strip().replace('"', "")
    value = re.sub(r"^\[[^\]]+\]\s*", "", value)
    value = re.sub(
        r"^(n|v|vi|vt|aux|a|adj|adv|prep|conj|pron|art|num|int|abbr|phr|modal)\.(?:\s*|$)",
        "",
        value,
        flags=re.I,
    )
    value = re.sub(r"\[[^\]]+\]", "", value)
    value = re.sub(r"\([^)]*\)", "", value)
    return value.strip(" ;,，；、")


def normalize_meaning(word: str, raw: str) -> str:
    if word in MEANING_OVERRIDES:
        return MEANING_OVERRIDES[word]

    raw = raw.replace("\\n", "\n")
    candidates = []

    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("[网络]"):
            continue

        for piece in re.split(r"[；;]", line):
            piece = clean_segment(piece)
            if not contains_chinese(piece):
                continue

            for segment in re.split(r"[，,、/]", piece):
                segment = clean_segment(segment)
                if contains_chinese(segment):
                    candidates.append(segment)

    seen = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.append(candidate)

    if seen:
        return seen[0]

    return raw.strip()


def normalize_phonetic(word: str, current: str = "") -> str:
    if word in PHONETIC_OVERRIDES:
        return PHONETIC_OVERRIDES[word]

    converted = ipa.convert(word).strip().replace("*", "")
    converted = converted.replace("ʤ", "dʒ").replace("ɚ", "ər")

    if converted:
        return f"/{converted}/"

    return current


def estimate_syllable_count(word: str) -> int:
    phonetic = normalize_phonetic(word, "").strip("/")
    count = len(IPA_SYLLABLE_RE.findall(phonetic))
    return max(1, count)


def split_vowel_run(sequence: str, target_groups: int) -> list[str]:
    if target_groups <= 1 or len(sequence) <= 1:
        return [sequence]

    if sequence.lower() in COMMON_VOWEL_TEAMS:
        return [sequence]

    if target_groups == 2:
        if len(sequence) == 2:
            return [sequence[0], sequence[1]]
        return [sequence[:-1], sequence[-1:]]

    parts = []
    remaining = sequence
    while len(parts) < target_groups - 1 and remaining:
        parts.append(remaining[:1])
        remaining = remaining[1:]

    if remaining:
        parts.append(remaining)

    return [part for part in parts if part]


def split_chunk_once(chunk: str) -> list[str]:
    lower = chunk.lower()
    length = len(lower)

    if length <= 3:
        return [chunk]

    if lower.endswith("le") and length > 3 and lower[-3] not in "aeiouy":
        return [chunk[:-2], chunk[-2:]]

    spans = []
    index = 0
    while index < length:
        char = lower[index]
        is_vowel = char in "aeiou" or (char == "y" and index != 0)
        if not is_vowel:
            index += 1
            continue

        end = index + 1
        while end < length and (lower[end] in "aeiou" or (lower[end] == "y" and end != 0)):
            end += 1

        spans.append((index, end))
        index = end

    if len(spans) <= 1:
        return [chunk]

    first_start, first_end = spans[0]
    second_start, second_end = spans[1]
    middle = lower[first_end:second_start]

    if not middle:
        sequence = chunk[first_start:second_end]
        pieces = split_vowel_run(sequence, 2)
        if len(pieces) == 2:
            return [chunk[:first_start] + pieces[0], pieces[1] + chunk[second_end:]]
        return [chunk]

    cut = first_end if len(middle) == 1 else first_end + 1
    return [chunk[:cut], chunk[cut:]]


def refine_unsplit_candidate(chunks: list[str], target_count: int) -> list[str]:
    current = list(chunks)
    seen = {tuple(current)}

    while len(current) < target_count:
        index = max(range(len(current)), key=lambda idx: len(current[idx]))
        pieces = split_chunk_once(current[index])
        proposal = tuple(current[:index] + pieces + current[index + 1:])
        if len(pieces) == 1 or proposal in seen:
            break

        seen.add(proposal)
        current = list(proposal)

    return current


def choose_natural_chunks(word: str) -> list[str]:
    if word in CHUNK_OVERRIDES:
        return CHUNK_OVERRIDES[word]

    target_count = estimate_syllable_count(word)
    us_chunks = us_hyphenator.inserted(word).split("-") if "-" in us_hyphenator.inserted(word) else [word]
    gb_chunks = gb_hyphenator.inserted(word).split("-") if "-" in gb_hyphenator.inserted(word) else [word]

    candidates = [("us", us_chunks)]
    if gb_chunks != us_chunks:
        candidates.append(("gb", gb_chunks))

    _, best_chunks = min(
        candidates,
        key=lambda item: (abs(len(item[1]) - target_count), 0 if item[0] == "us" else 1),
    )

    if len(best_chunks) == 1 and target_count > 1:
        refined = refine_unsplit_candidate(best_chunks, target_count)
        if refined != best_chunks:
            return refined

    return [chunk for chunk in best_chunks if chunk] or [word]


def normalize_chunks(word: str, current_chunks: Optional[list[str]] = None) -> list[str]:
    _ = current_chunks
    return choose_natural_chunks(word)


def clean_existing(items: list[dict]) -> list[dict]:
    cleaned = []
    for item in items:
        word = item["word"].strip().lower()
        cleaned.append(
            {
                "word": word,
                "chunks": normalize_chunks(word, item.get("chunks") or [word]),
                "phonetic": normalize_phonetic(word, item.get("phonetic", "")),
                "meaning": normalize_meaning(word, item.get("meaning", "")),
            }
        )
    return cleaned


def build_new_entries(existing_words: set[str], count: int) -> list[dict]:
    reader = csv.DictReader(io.StringIO(ensure_ecdict().read_text(encoding="utf-8", errors="ignore")))
    ranked = []

    for row in reader:
        word = row["word"].strip().lower()
        if word in existing_words:
            continue
        if not re.fullmatch(r"[a-z]+", word):
            continue
        if len(word) < 2 or len(word) > 16:
            continue

        meaning = normalize_meaning(word, row["translation"])
        phonetic = normalize_phonetic(word, row["phonetic"])
        if not meaning or not phonetic:
            continue

        ranked.append(
            (
                (
                    rank(row["frq"]),
                    rank(row["bnc"]),
                    -int(row["oxford"] or 0),
                    -int(row["collins"] or 0),
                    len(word),
                    word,
                ),
                {
                    "word": word,
                    "chunks": normalize_chunks(word),
                    "phonetic": phonetic,
                    "meaning": meaning,
                },
            )
        )

    best = heapq.nsmallest(count, ranked, key=lambda item: item[0])
    best.sort(key=lambda item: item[0])
    return [entry for _, entry in best]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-total", type=int, default=TARGET_TOTAL)
    args = parser.parse_args()

    items = clean_existing(load_items())
    existing_words = {item["word"] for item in items}
    needed = max(0, args.target_total - len(items))

    if needed:
        items.extend(build_new_entries(existing_words, needed))

    if len(items) != args.target_total:
        raise RuntimeError(f"Expected {args.target_total} entries, got {len(items)}")

    write_items(items)
    print(f"wrote {len(items)} entries")
    print("new segment:", ", ".join(entry["word"] for entry in items[-10:]))


if __name__ == "__main__":
    main()
