#!/usr/bin/env python3

import csv
import json
import re
from pathlib import Path

import pyphen

SOURCE_PATH = Path("/tmp/wordgen/ecdict.csv")
VOCAB_PATH = Path("vocabulary.js")
TARGET_COUNT = 1500

MEANING_OVERRIDES = {
    "a": "一个；一",
    "an": "一个；一",
    "and": "和",
    "any": "任何",
    "answer": "回答；答案",
    "as": "像；作为",
    "be": "是",
    "because": "因为",
    "benefit": "利益；好处",
    "best": "最好的",
    "better": "更好的；更好地",
    "body": "身体",
    "book": "书",
    "business": "商业；生意",
    "by": "通过；在……旁",
    "can": "能；可以",
    "child": "孩子",
    "children": "孩子们",
    "common": "常见的",
    "computer": "计算机",
    "cost": "成本；花费",
    "customer": "顾客",
    "day": "天；日子",
    "develop": "发展",
    "different": "不同的",
    "discover": "发现",
    "down": "向下",
    "easy": "容易的",
    "family": "家庭",
    "fact": "事实",
    "figure": "数字；人物",
    "forest": "森林",
    "for": "为了",
    "from": "从；来自",
    "general": "普遍的；一般的",
    "get": "得到",
    "go": "去",
    "good": "好的",
    "great": "极好的；巨大的",
    "have": "有",
    "he": "他",
    "hospital": "医院",
    "include": "包括",
    "industry": "工业",
    "in": "在……里",
    "international": "国际的",
    "it": "它",
    "know": "知道；了解",
    "life": "生活；生命",
    "look": "看",
    "major": "主要的",
    "make": "制造；使得",
    "manage": "管理",
    "may": "可以；也许",
    "medical": "医学的；医疗的",
    "month": "月",
    "more": "更多；更",
    "my": "我的",
    "natural": "自然的",
    "next": "下一个；下一次",
    "not": "不",
    "now": "现在",
    "of": "的",
    "on": "在……上",
    "one": "一；一个",
    "people": "人们",
    "place": "地方",
    "possible": "可能的",
    "public": "公众的；公共的",
    "resource": "资源",
    "respond": "回应",
    "school": "学校",
    "save": "保存；挽救",
    "say": "说",
    "simple": "简单的",
    "some": "一些",
    "state": "状态；州",
    "support": "支持",
    "situation": "情况",
    "take": "拿；带走",
    "that": "那；那个",
    "the": "这；那（定冠词）",
    "their": "他们的",
    "there": "那里",
    "this": "这",
    "time": "时间",
    "to": "到；向",
    "tough": "艰难的；强硬的",
    "university": "大学",
    "us": "我们",
    "very": "非常",
    "way": "方式；道路",
    "we": "我们",
    "what": "什么",
    "when": "何时；当……时候",
    "where": "在哪里",
    "who": "谁",
    "will": "将；愿意",
    "with": "和……一起",
    "work": "工作",
    "world": "世界",
    "would": "将会；愿意",
    "year": "年",
    "you": "你",
    "your": "你的",
}

PHONETIC_OVERRIDES = {
    "a": "/ə/",
    "an": "/ən/",
    "and": "/ænd/",
    "any": "/ˈeni/",
    "be": "/bi/",
    "because": "/bɪˈkɔz/",
    "benefit": "/ˈbɛnəfɪt/",
    "best": "/bɛst/",
    "better": "/ˈbɛtər/",
    "book": "/bʊk/",
    "business": "/ˈbɪznəs/",
    "by": "/baɪ/",
    "can": "/kæn/",
    "child": "/ʧaɪld/",
    "children": "/ˈʧɪldrən/",
    "computer": "/kəmˈpjuːtər/",
    "customer": "/ˈkʌstəmər/",
    "day": "/deɪ/",
    "develop": "/dɪˈvɛləp/",
    "different": "/ˈdɪfərənt/",
    "discover": "/dɪˈskʌvər/",
    "easy": "/ˈizi/",
    "family": "/ˈfæməli/",
    "figure": "/ˈfɪgjər/",
    "forest": "/ˈfɔrɪst/",
    "for": "/fɔr/",
    "from": "/frəm/",
    "general": "/ˈʤɛnərəl/",
    "get": "/gɛt/",
    "go": "/goʊ/",
    "good": "/gʊd/",
    "great": "/greɪt/",
    "have": "/hæv/",
    "he": "/hi/",
    "hospital": "/ˈhɑspɪtəl/",
    "include": "/ɪnˈklud/",
    "industry": "/ˈɪndəstri/",
    "in": "/ɪn/",
    "international": "/ˌɪntərˈnæʃənəl/",
    "it": "/ɪt/",
    "know": "/noʊ/",
    "life": "/laɪf/",
    "look": "/lʊk/",
    "major": "/ˈmeɪʤər/",
    "make": "/meɪk/",
    "manage": "/ˈmænəʤ/",
    "may": "/meɪ/",
    "medical": "/ˈmɛdɪkəl/",
    "month": "/mʌnθ/",
    "more": "/mɔr/",
    "my": "/maɪ/",
    "natural": "/ˈnæʧərəl/",
    "next": "/nɛkst/",
    "not": "/nɑt/",
    "now": "/naʊ/",
    "of": "/əv/",
    "on": "/ɔn/",
    "one": "/wʌn/",
    "people": "/ˈpipəl/",
    "place": "/pleɪs/",
    "possible": "/ˈpɑsəbəl/",
    "public": "/ˈpʌblɪk/",
    "resource": "/ˈrisɔrs/",
    "respond": "/rɪˈspɑnd/",
    "school": "/skul/",
    "save": "/seɪv/",
    "say": "/seɪ/",
    "simple": "/ˈsɪmpəl/",
    "some": "/sʌm/",
    "state": "/steɪt/",
    "support": "/səˈpɔrt/",
    "situation": "/ˌsɪʧuˈeɪʃən/",
    "take": "/teɪk/",
    "that": "/ðæt/",
    "the": "/ðə/",
    "their": "/ðer/",
    "there": "/ðer/",
    "this": "/ðɪs/",
    "time": "/taɪm/",
    "to": "/tu/",
    "tough": "/tʌf/",
    "university": "/ˌjunəˈvɜrsəti/",
    "us": "/ʌs/",
    "very": "/ˈvɛri/",
    "way": "/weɪ/",
    "we": "/wi/",
    "what": "/wʌt/",
    "when": "/wɛn/",
    "where": "/wɛr/",
    "who": "/hu/",
    "will": "/wɪl/",
    "with": "/wɪθ/",
    "work": "/wɜrk/",
    "world": "/wɜrld/",
    "would": "/wʊd/",
    "year": "/jɪr/",
    "you": "/ju/",
    "your": "/jʊr/",
}

CHUNK_OVERRIDES = {
    "because": ["be", "cause"],
    "business": ["busi", "ness"],
    "computer": ["com", "pu", "ter"],
    "family": ["fam", "i", "ly"],
    "people": ["peo", "ple"],
    "situation": ["sit", "u", "ation"],
    "university": ["uni", "ver", "si", "ty"],
}


def rank(value: str) -> int:
    try:
        number = int(value)
    except Exception:
        return 10**9
    return number if number > 0 else 10**9


def contains_chinese(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def clean_text(value: str) -> str:
    value = value.replace("\\n", "\n").strip().replace('"', "")
    value = re.sub(r"^\[[^\]]+\]\s*", "", value)
    value = re.sub(r"^(n|v|vi|vt|adj|adv|prep|conj|pron|aux|art|num|int)\.(?:\s*|$)", "", value, flags=re.I)
    value = re.sub(r"\[[^\]]+\]", "", value)
    value = re.sub(r"\([^)]*\)", "", value)
    return value.strip(" ;,，；、")


def pick_meaning(word: str, raw: str) -> str:
    if word in MEANING_OVERRIDES:
        return MEANING_OVERRIDES[word]

    candidates = []
    for line in raw.replace("\\n", "\n").splitlines():
        line = line.strip()
        if not line or line.startswith("[网络]"):
            continue
        for piece in re.split(r"[；;]", line):
            piece = clean_text(piece)
            if not contains_chinese(piece):
                continue
            for part in re.split(r"[，,、/]", piece):
                part = clean_text(part)
                if contains_chinese(part):
                    candidates.append(part)

    for candidate in candidates:
        if candidate:
            return candidate
    return ""


def pick_phonetic(word: str, raw: str) -> str:
    if word in PHONETIC_OVERRIDES:
        return PHONETIC_OVERRIDES[word]

    raw = raw.strip()
    if not raw:
        return ""

    raw = raw.replace("ɚ", "ər").replace("ʤ", "dʒ").replace("*", "")
    raw = raw.strip("/ ")
    return f"/{raw}/"


def pick_chunks(word: str) -> list[str]:
    if word in CHUNK_OVERRIDES:
        return CHUNK_OVERRIDES[word]
    if len(word) <= 5:
        return [word]
    return [word]


def main() -> None:
    existing_text = VOCAB_PATH.read_text(encoding="utf-8")
    existing_items = json.loads(existing_text[existing_text.index("[") : existing_text.rindex("]") + 1])
    existing_words = {item["word"] for item in existing_items}

    chosen = []
    seen_new = set()

    with SOURCE_PATH.open(encoding="utf-8", errors="ignore") as source:
        reader = csv.DictReader(source)
        ranked = []

        for row in reader:
            word = row["word"].strip().lower()
            if not re.fullmatch(r"[a-z]+", word):
                continue
            if word in existing_words or word in seen_new:
                continue
            if len(word) > 16:
                continue

            meaning = pick_meaning(word, row["translation"])
            phonetic = pick_phonetic(word, row["phonetic"])
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
                        "chunks": pick_chunks(word),
                        "phonetic": phonetic,
                        "meaning": meaning,
                    },
                )
            )
            seen_new.add(word)

    ranked.sort(key=lambda item: item[0])
    chosen = [item[1] for item in ranked[:500]]

    combined = existing_items + chosen
    VOCAB_PATH.write_text(
        "window.VOCABULARY = " + json.dumps(combined, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )

    print(f"updated {VOCAB_PATH} with {len(chosen)} new entries")
    print("first new words:", ", ".join(item["word"] for item in chosen[:10]))
    print("last new words:", ", ".join(item["word"] for item in chosen[-10:]))


if __name__ == "__main__":
    main()
