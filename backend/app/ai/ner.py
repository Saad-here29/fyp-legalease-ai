"""Legal Named Entity Recognition for Document Analysis.

Model: distilbert-base-multilingual-cased fine-tuned on LHC + SCP court
judgments (ai-services/ner_training/, results in docs/ner_training_results.md).
Weights live at settings.NER_MODEL_PATH and are gitignored — when they are
absent, `extract_entities()` reports the model as unavailable and callers
carry on without NER.

Loading takes ~13 s on CPU, so `start_background_load()` is kicked off from
the app lifespan; a request that arrives first waits on the same lock.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

from app.ai.model_loading import MODEL_LOAD_LOCK
from app.core.config import settings
from app.core.logging import logger

MAX_CHARS = 30_000       # same cap the LLM summary applies
CHUNK_TOKENS = 200       # model was trained at max_length=256
MIN_SCORE = 0.5

# LHC and SCP annotators spelled three labels differently; one concept each.
_MERGE = {"caseNo.": "caseno", "refCase": "refcase", "refCourt": "refcourt"}
# Near-zero F1 on validation/test — showing their output would mislead.
_DROP = {"Misc.name", "FIRno", "mutationNo.", "witnessName"}

_LOCK = threading.Lock()
_TAGGER = None
_STATE = "not_loaded"    # not_loaded | loaded | unavailable


class _Tagger:
    """Tags words split the way the training data was (see `word_spans`):
    each word gets the label of its FIRST subword, as in training and
    evaluation, then B-/I- tags are joined into entity spans.

    (The HF pipeline's aggregation re-splits words at punctuation, so a date
    like "30.7.1983" reached the model as "30 . 7 . 1983" and came back as
    two entities; training data kept it as one word.)"""

    def __init__(self, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model
        self.id2label = model.config.id2label

    def __call__(self, chunks: list[str], batch_size: int = 8) -> list[list[dict]]:
        import torch

        out: list[list[dict]] = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            spans = [word_spans(c) for c in batch]
            enc = self.tokenizer(
                [[c[s:e] for s, e in sp] for c, sp in zip(batch, spans)],
                is_split_into_words=True, truncation=True, max_length=512,
                padding=True, return_tensors="pt",
            )
            with torch.no_grad():
                probs = self.model(
                    input_ids=enc["input_ids"], attention_mask=enc["attention_mask"]
                ).logits.softmax(-1)
            for b, sp in enumerate(spans):
                word_tags: dict[int, tuple[str, float]] = {}
                for j, w in enumerate(enc.word_ids(batch_index=b)):
                    if w is not None and w not in word_tags:
                        p, idx = probs[b, j].max(-1)
                        word_tags[w] = (self.id2label[int(idx)], float(p))
                out.append(_decode_bio(sp, [word_tags.get(w, ("O", 1.0)) for w in range(len(sp))]))
        return out


_LEAD = set("([{\"'")
_TRAIL = set(".,;:)]}\"'")


def word_spans(text: str) -> list[tuple[int, int]]:
    """Word boundaries in the training data's style: whitespace-separated,
    with punctuation at a word's edges split off as its own token
    ("W.P.No." -> "W.P.No" "." ; "(Against" -> "(" "Against") while internal
    punctuation stays ("30.7.1983", "NO.1074", "11983/2005")."""
    spans: list[tuple[int, int]] = []
    for m in re.finditer(r"\S+", text):
        s, e = m.start(), m.end()
        lead, trail = [], []
        while s < e and text[s] in _LEAD:
            lead.append((s, s + 1)); s += 1
        while e > s and text[e - 1] in _TRAIL:
            trail.append((e - 1, e)); e -= 1
        spans.extend(lead)
        if s < e:
            spans.append((s, e))
        spans.extend(reversed(trail))
    return spans


def _decode_bio(spans: list[tuple[int, int]], tags: list[tuple[str, float]]) -> list[dict]:
    """Join per-word B-/I- tags into entities. An I- tag that doesn't continue
    an entity of the same type starts a new one (seqeval's default reading).
    Score = mean word probability."""
    ents: list[dict] = []
    cur = None
    for (s, e), (tag, p) in zip(spans, tags):
        kind, _, typ = tag.partition("-")
        if tag == "O":
            cur = None
            continue
        if kind == "I" and cur is not None and cur["entity_group"] == typ:
            cur["end"] = e
            cur["_p"].append(p)
            continue
        cur = {"entity_group": typ, "start": s, "end": e, "_p": [p]}
        ents.append(cur)
    for ent in ents:
        ps = ent.pop("_p")
        ent["score"] = sum(ps) / len(ps)
    return ents


# ---- Loading ---------------------------------------------------------------

def _load():
    global _TAGGER, _STATE
    with _LOCK:
        if _STATE != "not_loaded":
            return _TAGGER
        path = Path(settings.NER_MODEL_PATH)
        if not settings.NER_ENABLED:
            logger.info("NER disabled (NER_ENABLED=false)")
            _STATE = "unavailable"
            return None
        if not (path / "model.safetensors").exists():
            logger.warning(f"NER model not found at {path} — Document Analysis will skip NER")
            _STATE = "unavailable"
            return None
        try:
            # Shared with the embedding loader: concurrent `transformers`
            # imports race (see app/ai/model_loading.py).
            with MODEL_LOAD_LOCK:
                from transformers import AutoModelForTokenClassification, AutoTokenizer
                logger.info(f"Loading NER model from {path}")
                tok = AutoTokenizer.from_pretrained(str(path))
                # Saved by transformers 5.x as a plain BertTokenizer, which
                # emits token_type_ids — DistilBERT's forward() rejects them.
                tok.model_input_names = ["input_ids", "attention_mask"]
                model = AutoModelForTokenClassification.from_pretrained(str(path)).eval()
            _TAGGER = _Tagger(tok, model)
            _STATE = "loaded"
            logger.info("NER model ready")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"NER model failed to load: {type(e).__name__}: {e}")
            _STATE = "unavailable"
        return _TAGGER


def start_background_load() -> None:
    threading.Thread(target=_load, name="ner-load", daemon=True).start()


def reset() -> None:
    """Forget the loaded model (tests)."""
    global _TAGGER, _STATE
    with _LOCK:
        _TAGGER, _STATE = None, "not_loaded"


# ---- Chunking --------------------------------------------------------------

_SENTENCE_END = re.compile(r"(?<=[.!?۔])\s+|\n+")


def chunk_text(text: str, count_tokens, max_tokens: int = CHUNK_TOKENS) -> list[tuple[int, str]]:
    """Split `text` into (start_offset, chunk) pieces of at most `max_tokens`
    subword tokens, breaking at sentence ends where possible and at word
    boundaries otherwise. Offsets index into `text`, so entity positions
    inside a chunk map straight back to the original document."""
    spans: list[tuple[int, int]] = []           # sentence spans
    pos = 0
    for m in _SENTENCE_END.finditer(text):
        if m.start() > pos:
            spans.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        spans.append((pos, len(text)))

    # Oversized sentences -> word-boundary pieces
    pieces: list[tuple[int, int]] = []
    for s, e in spans:
        if count_tokens(text[s:e]) <= max_tokens:
            pieces.append((s, e))
            continue
        start, prev_end = s, None
        for w in re.finditer(r"\S+", text[s:e]):
            ws, we = s + w.start(), s + w.end()
            if prev_end is not None and count_tokens(text[start:we]) > max_tokens:
                pieces.append((start, prev_end))
                start = ws
            prev_end = we
        pieces.append((start, prev_end or e))

    # A single "word" longer than the budget (e.g. a run of symbols with no
    # spaces) would overflow the model's 512 positions: cut it by characters.
    safe: list[tuple[int, int]] = []
    for s, e in pieces:
        while count_tokens(text[s:e]) > max_tokens and e - s > 1:
            cut = s + max(1, (e - s) // 2)
            while count_tokens(text[s:cut]) > max_tokens and cut - s > 1:
                cut = s + (cut - s) // 2
            safe.append((s, cut))
            s = cut
        safe.append((s, e))
    pieces = safe

    # Greedily pack consecutive pieces into chunks
    chunks: list[tuple[int, int]] = []
    for s, e in pieces:
        if chunks and count_tokens(text[chunks[-1][0]:e]) <= max_tokens:
            chunks[-1] = (chunks[-1][0], e)
        else:
            chunks.append((s, e))
    return [(s, text[s:e]) for s, e in chunks if text[s:e].strip()]


# ---- Post-processing -------------------------------------------------------

# Corrections for two failure modes found on a real 2026 Supreme Court order
# (docs/demo_examples.md). Both are narrow, deterministic rules applied to
# the model's output — the model itself is unchanged.

_PERSON_TYPES = {"per", "resp"}
_ABBREVIATION = re.compile(r"[A-Z]{2,3}\.?")   # not 1 letter: keeps initials ("S.")


def trim_line_break_abbreviation(text: str, ent: dict) -> dict:
    """Line breaks reach the model as plain spaces, so in a counsel block like
        "Mr. Altaf Khan, AAG KP\\nTahir Khan, SI"
    the province code "KP" ended one line and the model tagged "KP Tahir
    Khan" as one person. When a person/respondent entity crosses a line
    break and the part on one side is only a short all-caps abbreviation
    (KP, AAG, SI, ...), drop that part. Limited to person types so
    citations that legitimately start "PLD\\n2015 ..." are never touched."""
    if ent["entity_group"] not in _PERSON_TYPES:
        return ent
    start, end = ent["start"], ent["end"]
    span = text[start:end]
    first_break = span.find("\n")
    if first_break != -1 and _ABBREVIATION.fullmatch(span[:first_break].strip()):
        start += first_break + 1
    span = text[start:end]
    last_break = span.rfind("\n")
    if last_break != -1 and _ABBREVIATION.fullmatch(span[last_break + 1:].strip()):
        end = start + last_break
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return {**ent, "start": start, "end": end} if (start, end) != (ent["start"], ent["end"]) else ent


# Where a judgment's heading ends: the "[Against the judgment ..." line that
# introduces the lower-court decision, or the ORDER / JUDGMENT title.
_HEADING_END = re.compile(r"\bAgainst\b|^\s*(?:ORDER|JUDGMENT|JUDGEMENT)\s*$", re.MULTILINE)
_CASE_NUMBER = re.compile(r"\bNo\b|\bNos?\.", re.IGNORECASE)
# A heading is the top of the document. If no marker appears this early,
# assume there is no judgment-style heading and change nothing — a
# capitalised "Against" deep in the body must not relabel cited cases.
_HEADING_MAX_CHARS = 2_000


def relabel_own_case_number(text: str, raw: list[dict]) -> list[dict]:
    """In SCP training data a judgment's own number is written in capitals
    ("CIVIL APPEAL NO.1074 OF 2009") and labelled caseno; mixed-case
    "Criminal Petition No." only ever appears as a cited or appealed-from
    case. So on a mixed-case heading the model labels the document's own
    number `appealcaseno`. A case number that sits in the heading — before
    the "Against the judgment ..." line or the ORDER/JUDGMENT title, where
    the appealed-from case is named — is the document's own case."""
    m = _HEADING_END.search(text, 0, _HEADING_MAX_CHARS)
    if m is None:
        return raw
    heading_end = m.start()
    out = []
    for ent in raw:
        if (ent["entity_group"] in ("appealcaseno", "refcase")
                and ent["end"] <= heading_end
                and _CASE_NUMBER.search(text[ent["start"]:ent["end"]])
                and re.search(r"\d", text[ent["start"]:ent["end"]])):
            ent = {**ent, "entity_group": "caseno"}
        out.append(ent)
    return out

@dataclass
class Entity:
    type: str
    text: str
    count: int
    score: float
    first_offset: int


@dataclass
class NerResult:
    available: bool
    entities: list[Entity] = field(default_factory=list)

    def by_type(self, *types: str) -> list[Entity]:
        return [e for e in self.entities if e.type in types]

    def as_json(self) -> dict:
        grouped: dict[str, list[dict]] = {}
        for e in self.entities:
            grouped.setdefault(e.type, []).append(
                {"text": e.text, "count": e.count, "score": round(e.score, 3)}
            )
        return grouped


def _norm_key(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" ,;:.").lower()


def merge_predictions(text: str, raw: list[dict]) -> list[Entity]:
    """`raw` entries: {entity_group, score, start, end} with offsets into
    `text`. Applies label merging, drops unreliable types and low-confidence
    spans, and de-duplicates by (type, normalised text) keeping document
    order, a mention count and the best score."""
    out: dict[tuple[str, str], Entity] = {}
    for r in raw:
        label = _MERGE.get(r["entity_group"], r["entity_group"])
        if label in _DROP or float(r["score"]) < MIN_SCORE:
            continue
        surface = re.sub(r"\s+", " ", text[r["start"]:r["end"]]).strip(" ,;:")
        if len(surface) < 2:
            continue
        key = (label, _norm_key(surface))
        if key in out:
            out[key].count += 1
            out[key].score = max(out[key].score, float(r["score"]))
        else:
            out[key] = Entity(label, surface, 1, float(r["score"]), r["start"])
    return sorted(out.values(), key=lambda e: e.first_offset)


# ---- Public API ------------------------------------------------------------

def extract_entities(text: str) -> NerResult:
    ner = _load()
    if ner is None:
        return NerResult(available=False)
    text = (text or "")[:MAX_CHARS]
    if not text.strip():
        return NerResult(available=True)

    tok = ner.tokenizer

    def count_tokens(s: str) -> int:
        return len(tok(s, add_special_tokens=False)["input_ids"])

    chunks = chunk_text(text, count_tokens)
    outputs = ner([c for _, c in chunks], batch_size=8)
    raw = []
    for (offset, _), preds in zip(chunks, outputs):
        for p in preds:
            raw.append({
                "entity_group": p["entity_group"],
                "score": p["score"],
                "start": offset + p["start"],
                "end": offset + p["end"],
            })
    raw = relabel_own_case_number(text, [trim_line_break_abbreviation(text, r) for r in raw])
    return NerResult(available=True, entities=merge_predictions(text, raw))
