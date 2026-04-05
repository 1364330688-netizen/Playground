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
TARGET_TOTAL = 1500

hyphenator = pyphen.Pyphen(lang="en_US")

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
    "anybody": ["any", "body"],
    "afternoon": ["after", "noon"],
    "anyway": ["any", "way"],
    "advice": ["ad", "vice"],
    "aspect": ["as", "pect"],
    "answer": ["answer"],
    "attend": ["at", "tend"],
    "bother": ["bother"],
    "brother": ["brother"],
    "center": ["center"],
    "common": ["common"],
    "computer": ["com", "pu", "ter"],
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
    "family": ["fa", "mi", "ly"],
    "freedom": ["free", "dom"],
    "income": ["in", "come"],
    "insist": ["in", "sist"],
    "intend": ["in", "tend"],
    "invite": ["in", "vite"],
    "critic": ["cri", "tic"],
    "mistake": ["mis", "take"],
    "necessary": ["neces", "sary"],
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
    "somehow": ["some", "how"],
    "situation": ["situ", "ation"],
    "survive": ["sur", "vive"],
    "unless": ["un", "less"],
    "weekend": ["week", "end"],
    "welcome": ["wel", "come"],
    "political": ["po", "li", "ti", "cal"],
    "contribute": ["con", "tri", "bute"],
    "economic": ["eco", "no", "mic"],
    "academic": ["aca", "de", "mic"],
    "democratic": ["demo", "cra", "tic"],
    "dramatic": ["dra", "ma", "tic"],
    "specific": ["spe", "ci", "fic"],
    "scientific": ["sci", "en", "ti", "fic"],
    "automatic": ["au", "to", "ma", "tic"],
    "education": ["edu", "ca", "tion"],
    "evidence": ["evi", "dence"],
    "medical": ["medi", "cal"],
    "individual": ["indi", "vid", "ual"],
    "technology": ["tech", "nol", "ogy"],
    "operation": ["op", "er", "ation"],
    "authority": ["au", "thor", "ity"],
    "executive": ["ex", "ec", "utive"],
    "popular": ["pop", "ular"],
    "particular": ["par", "tic", "ular"],
    "reality": ["re", "al", "ity"],
    "violence": ["vio", "lence"],
    "responsibility": ["re", "spon", "si", "bil", "ity"],
    "favorite": ["fa", "vo", "rite"],
    "failure": ["fail", "ure"],
    "matter": ["matter"],
    "member": ["member"],
    "memory": ["memory"],
    "medicine": ["medi", "cine"],
    "moment": ["moment"],
    "parent": ["parent"],
    "politician": ["po", "li", "ti", "cian"],
    "progress": ["pro", "gress"],
    "growing": ["grow", "ing"],
    "living": ["liv", "ing"],
    "meaning": ["mean", "ing"],
    "mother": ["mother"],
    "reading": ["read", "ing"],
    "summer": ["summer"],
    "writing": ["writ", "ing"],
    "catholic": ["ca", "tho", "lic"],
    "democracy": ["demo", "cra", "cy"],
    "democrat": ["demo", "crat"],
    "weather": ["weather"],
}

RIGHT_JOIN_SUFFIXES = {
    "al",
    "cal",
    "cy",
    "dence",
    "ence",
    "gy",
    "ial",
    "lar",
    "lence",
    "ly",
    "ment",
    "ness",
    "ous",
    "ship",
    "sion",
    "tion",
    "ty",
    "ual",
}

LEFT_PULL_ENDINGS = {
    "ic": 1,
    "ute": 1,
}

MAX_CHUNK_COUNT = 3


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


def squash_single_letter_chunks(chunks: list[str]) -> list[str]:
    merged = [chunk for chunk in chunks if chunk]
    i = 0

    while i < len(merged):
        if len(merged[i]) != 1:
            i += 1
            continue

        if len(merged) == 1:
            return merged

        if i == 0:
            merged[1] = merged[0] + merged[1]
            del merged[0]
            continue

        if i == len(merged) - 1:
            merged[i - 1] += merged[i]
            del merged[i]
            i -= 1
            continue

        next_chunk = merged[i + 1]
        is_final_pair = i + 1 == len(merged) - 1

        if next_chunk in RIGHT_JOIN_SUFFIXES or (len(next_chunk) <= 2 and is_final_pair):
            merged[i + 1] = merged[i] + merged[i + 1]
            del merged[i]
            continue

        merged[i - 1] += merged[i]
        del merged[i]
        i -= 1

    return merged


def rebalance_terminal_chunks(chunks: list[str]) -> list[str]:
    rebalanced = chunks[:]

    for ending, take_count in LEFT_PULL_ENDINGS.items():
        if len(rebalanced) < 2 or rebalanced[-1] != ending:
            continue

        previous = rebalanced[-2]
        if len(previous) <= take_count + 1:
            continue

        rebalanced[-2] = previous[:-take_count]
        rebalanced[-1] = previous[-take_count:] + ending

    return [chunk for chunk in rebalanced if chunk]


def needs_terminal_rebalance(chunks: list[str]) -> bool:
    if len(chunks) < 2:
        return False

    ending = chunks[-1]
    take_count = LEFT_PULL_ENDINGS.get(ending)
    if take_count is None:
        return False

    return len(chunks[-2]) > take_count + 1


def normalize_terminal_suffix(word: str, chunks: list[str]) -> list[str]:
    normalized = [chunk for chunk in chunks if chunk]

    if (
        word.endswith("ly")
        and len(normalized) >= 2
        and normalized[-1] != "ly"
        and normalized[-1].endswith("ly")
        and len(normalized[-1]) > 2
    ):
        prefix = normalized[-1][:-2]
        normalized[-2] += prefix
        normalized[-1] = "ly"

    return normalized


def group_chunks_by_count(chunks: list[str], groups: int) -> list[str]:
    if len(chunks) <= groups:
        return chunks[:]

    base_size = len(chunks) // groups
    extra = len(chunks) % groups
    group_sizes = [base_size + (1 if index < extra else 0) for index in range(groups)]

    grouped = []
    start = 0
    for size in group_sizes:
        grouped.append("".join(chunks[start:start + size]))
        start += size

    return [chunk for chunk in grouped if chunk]


def limit_chunk_count(word: str, chunks: list[str]) -> list[str]:
    limited = normalize_terminal_suffix(word, chunks)
    if len(limited) <= MAX_CHUNK_COUNT:
        return limited
    return group_chunks_by_count(limited, MAX_CHUNK_COUNT)


def build_memory_chunks(word: str) -> list[str]:
    inserted = hyphenator.inserted(word)
    if not inserted or inserted == word:
        return [word]

    chunks = squash_single_letter_chunks(inserted.split("-"))
    chunks = rebalance_terminal_chunks(chunks)
    chunks = limit_chunk_count(word, chunks)
    return chunks or [word]


def normalize_chunks(word: str, current_chunks: Optional[list[str]] = None) -> list[str]:
    if word in CHUNK_OVERRIDES:
        return limit_chunk_count(word, CHUNK_OVERRIDES[word])

    current_chunks = [chunk for chunk in (current_chunks or []) if chunk]

    if len(word) <= 5:
        return [word]

    candidate = build_memory_chunks(word)

    if not current_chunks:
        return candidate

    if len(current_chunks) > MAX_CHUNK_COUNT:
        return candidate

    if needs_terminal_rebalance(current_chunks):
        return candidate

    if normalize_terminal_suffix(word, current_chunks) != current_chunks:
        return candidate

    if len(current_chunks) > 1 and not any(len(chunk) == 1 for chunk in current_chunks):
        return current_chunks

    if len(current_chunks) == 1 and len(word) <= 7:
        return [word]

    if len(word) <= 7 and len(candidate) > 3:
        return [word]

    return candidate


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
