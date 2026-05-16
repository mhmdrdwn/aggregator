import logging
import numpy as np
from functools import lru_cache
from urllib.parse import urlparse

from .config import (
    SPACY_MODEL,
    SBERT_MODEL,
    SENTIMENT_MODEL,
    NER_LABELS,
    NLP_TEXT_LIMIT,
    EMBEDDING_TEXT_LIMIT,
    DEDUP_THRESHOLD,
    DOMAIN_TO_NAME,
)

logger = logging.getLogger(__name__)


def _hostname(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.removeprefix("www.")
    except Exception:
        return ""


@lru_cache(maxsize=1)
def _spacy_model():
    import spacy
    return spacy.load(SPACY_MODEL)


@lru_cache(maxsize=1)
def _sbert_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(SBERT_MODEL)


@lru_cache(maxsize=1)
def _sentiment_pipeline():
    from transformers import pipeline
    return pipeline("sentiment-analysis", model=SENTIMENT_MODEL, top_k=1, truncation=True, max_length=512)


def _canonical_source(article: dict) -> str:
    host = _hostname(article.get("url", ""))
    if host in DOMAIN_TO_NAME:
        return DOMAIN_TO_NAME[host]
    # Subdomain fallback: trdby.adressa.no → adressa.no
    parts = host.split(".")
    if len(parts) > 2:
        parent = ".".join(parts[-2:])
        if parent in DOMAIN_TO_NAME:
            return DOMAIN_TO_NAME[parent]
    return article.get("publisher") or article.get("sitename") or host or "Ukjent"


# Keyword sets per topic — scored against lowercased title + body snippet
_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "sport":         ["fotball","håndball","ski","langrenn","idrett","kamp","turnering",
                      "liga","vm","em","ol","trener","spiller","seier","tap","mål",
                      "champions league","premier league","nhl","nba","sykkel","tennis",
                      "golf","friidrett","svømming","haaland","løping","runde","poeng"],
    "kriminalitet":  ["politi","siktet","tiltalt","drap","ran","vold","dom","fengslet",
                      "pågripet","etterforsker","overfall","narkotika","bedrageri",
                      "svindel","kniv","skudd","arrestert","ofre","retten","straff"],
    "politikk":      ["stortinget","regjering","statsminister","minister","parti","valg",
                      "ap","høyre","frp","sv","senterpartiet","vedtak","debatt",
                      "politikk","støre","storting","budsjettet","flertall","opposisjon"],
    "økonomi":       ["økonomi","næringsliv","aksjer","børs","renter","inflasjon",
                      "bedrift","selskap","kvartal","omsetning","overskudd","underskudd",
                      "norges bank","oljeprisen","kronekurs","arbeidsledighet","vekst"],
    "helse":         ["helse","sykdom","sykehus","pasient","lege","behandling","medisin",
                      "kreft","hjerte","psykisk","folkehelse","vaksine","studie","forskning",
                      "helseminister","legemiddel","operasjon","diagnose","symptomer"],
    "teknologi":     ["teknologi","data","ai","kunstig intelligens","digitalisering",
                      "programvare","app","robot","cyber","kryptovaluta","bitcoin",
                      "elektrisitet","batteri","halvleder","it","startup","innovasjon"],
    "klima":         ["klima","miljø","utslipp","co2","natur","fornybar","vindkraft",
                      "solenergi","havnivå","flom","tørke","ekstremvær","artsmangfold",
                      "naturkatastrofe","klimaendring","grønn","bærekraft"],
    "kultur":        ["kultur","musikk","film","kunst","litteratur","teater","konsert",
                      "festival","utstilling","prisvinner","bok","serie","strømming",
                      "kino","skuespiller","forfatter","regissør","nobelprisen"],
    "utenriks":      ["ukraina","russland","usa","kina","eu","nato","krig","konflikt",
                      "trump","putin","israel","gaza","palestina","midtøsten","fn",
                      "sanksjoner","diplomat","bilateral","internasjonal","verdensbank"],
    "forsvar":       ["forsvaret","militær","nato","soldat","fregatt","kampfly","hær",
                      "marine","heimevernet","beredskap","rustning","ubåt","missil",
                      "forsvarsbudsjet","sikkerhetspolitikk","etterretning"],
    "utdanning":     ["skole","elev","lærer","student","universitet","høyskole",
                      "utdanning","forskning","karakter","eksamen","barnehage",
                      "rektor","studiepoeng","frafall","lærested"],
    "samfunn":       ["samfunn","velferd","innvandring","integrering","bolig",
                      "fattigdom","barnevern","nav","trygd","pensjon","likestilling",
                      "diskriminering","rasisme","frivillighet","kirke","religion"],
}

# SBERT anchor embeddings for each topic (computed once, used as fallback)
@lru_cache(maxsize=1)
def _topic_anchors() -> tuple[list[str], np.ndarray]:
    descriptions = {k: " ".join(v[:12]) for k, v in _TOPIC_KEYWORDS.items()}
    names = list(descriptions.keys())
    embs = _sbert_model().encode(list(descriptions.values()))
    return names, embs


def classify_topic(title: str, text: str, embedding: list[float]) -> str:
    """Keyword scoring with SBERT cosine-similarity fallback."""
    haystack = f"{title} {text[:600]}".lower()

    scores: dict[str, int] = {}
    for topic, keywords in _TOPIC_KEYWORDS.items():
        scores[topic] = sum(1 for kw in keywords if kw in haystack)

    best_score = max(scores.values())
    if best_score >= 2:
        return max(scores, key=lambda t: scores[t])

    # Fallback: cosine similarity against topic anchors
    names, anchors = _topic_anchors()
    from sklearn.metrics.pairwise import cosine_similarity as cos_sim
    sims = cos_sim([embedding], anchors)[0]
    return names[int(sims.argmax())]


_LABEL_NORM = {"GPE_LOC": "GPE", "GPE_ORG": "GPE", "EVT": "EVENT"}

# (text.lower(), label) → canonical display name
_ENTITY_ALIASES: dict[tuple[str, str], str] = {
    # --- International political figures ---
    ("trump", "PER"):              "Donald Trump",
    ("trumps", "PER"):             "Donald Trump",
    ("donald trumps", "PER"):      "Donald Trump",
    ("xi", "PER"):                 "Xi Jinping",
    ("xis", "PER"):                "Xi Jinping",
    ("putin", "PER"):              "Vladimir Putin",
    ("putins", "PER"):             "Vladimir Putin",
    ("vladimir putins", "PER"):    "Vladimir Putin",
    ("netanyahu", "PER"):          "Benjamin Netanyahu",
    ("netanyahus", "PER"):         "Benjamin Netanyahu",
    ("macron", "PER"):             "Emmanuel Macron",
    ("macrons", "PER"):            "Emmanuel Macron",
    ("orban", "PER"):              "Viktor Orbán",
    ("orbán", "PER"):              "Viktor Orbán",
    ("orbans", "PER"):             "Viktor Orbán",
    ("orbáns", "PER"):             "Viktor Orbán",
    ("zelenskyj", "PER"):          "Volodymyr Zelenskyj",
    ("zelenskyjs", "PER"):         "Volodymyr Zelenskyj",
    ("zelensky", "PER"):           "Volodymyr Zelenskyj",
    ("zelenskij", "PER"):          "Volodymyr Zelenskyj",
    ("biden", "PER"):              "Joe Biden",
    ("bidens", "PER"):             "Joe Biden",
    ("rubio", "PER"):              "Marco Rubio",
    ("rubios", "PER"):             "Marco Rubio",
    ("hegseth", "PER"):            "Pete Hegseth",
    ("hegseths", "PER"):           "Pete Hegseth",
    ("powell", "PER"):             "Jerome Powell",
    ("powells", "PER"):            "Jerome Powell",

    # --- Norwegian political figures ---
    ("støre", "PER"):                    "Jonas Gahr Støre",
    ("støres", "PER"):                   "Jonas Gahr Støre",
    ("jonas gahr støres", "PER"):        "Jonas Gahr Støre",
    ("stoltenberg", "PER"):              "Jens Stoltenberg",
    ("stoltenbergs", "PER"):             "Jens Stoltenberg",
    ("jens stoltenbergs", "PER"):        "Jens Stoltenberg",
    ("listhaug", "PER"):                 "Sylvi Listhaug",
    ("listhaugs", "PER"):                "Sylvi Listhaug",
    ("sylvi listhaugs", "PER"):          "Sylvi Listhaug",
    ("vedum", "PER"):                    "Trygve Slagsvold Vedum",
    ("vedums", "PER"):                   "Trygve Slagsvold Vedum",
    ("skjæran", "PER"):                  "Bjørnar Skjæran",
    ("skjærans", "PER"):                 "Bjørnar Skjæran",
    ("erna solbergs", "PER"):            "Erna Solberg",
    ("solbergs", "PER"):                 "Erna Solberg",
    ("høiby", "PER"):                    "Marius Borg Høiby",
    ("høibys", "PER"):                   "Marius Borg Høiby",
    ("marius borg høibys", "PER"):       "Marius Borg Høiby",

    # --- Sports figures ---
    ("warholm", "PER"):                  "Karsten Warholm",
    ("warholms", "PER"):                 "Karsten Warholm",
    ("karsten warholms", "PER"):         "Karsten Warholm",
    ("mbappé", "PER"):                   "Kylian Mbappé",
    ("mbappés", "PER"):                  "Kylian Mbappé",
    ("mbappe", "PER"):                   "Kylian Mbappé",
    ("erling haalands", "PER"):          "Erling Haaland",
    ("erling braut haalands", "PER"):    "Erling Haaland",
    ("erling braut haaland", "PER"):     "Erling Haaland",

    # --- GPE genitives (Norwegian possessive -s suffix) ---
    ("norges", "GPE"):       "Norge",
    ("usas", "GPE"):         "USA",
    ("kinas", "GPE"):        "Kina",
    ("israels", "GPE"):      "Israel",
    ("russlands", "GPE"):    "Russland",
    ("ukrainas", "GPE"):     "Ukraina",
    ("irans", "GPE"):        "Iran",
    ("europas", "GPE"):      "Europa",
    ("natos", "GPE"):        "NATO",
    ("natos", "ORG"):        "NATO",
    ("nato", "ORG"):         "NATO",
    ("nato", "GPE"):         "NATO",
    ("eus", "GPE"):          "EU",
    ("eus", "ORG"):          "EU",
    ("fns", "GPE"):          "FN",
    ("fns", "ORG"):          "FN",
    ("oslos", "GPE"):        "Oslo",
    ("polens", "GPE"):       "Polen",
    ("frankrikes", "GPE"):   "Frankrike",
    ("tysklands", "GPE"):    "Tyskland",
    ("storbritannias", "GPE"): "Storbritannia",
    ("japans", "GPE"):       "Japan",
    ("indias", "GPE"):       "India",
    ("bergens", "GPE"):      "Bergen",
    ("trondheims", "GPE"):   "Trondheim",
    ("stavangers", "GPE"):   "Stavanger",
    ("tromsøs", "GPE"):      "Tromsø",
    ("kinas", "GPE"):        "Kina",
    ("sverigas", "GPE"):     "Sverige",
    ("Sveriges", "GPE"):     "Sverige",
    ("danmarks", "GPE"):     "Danmark",
    ("finlands", "GPE"):     "Finland",
}


def _normalize_entity(text: str, label: str) -> str:
    key = (text.lower(), label)
    canon = _ENTITY_ALIASES.get(key)
    if canon:
        return canon
    # Strip Norwegian genitive 's' and retry (e.g. "Kylian Mbappés" → "Kylian Mbappé")
    if text.endswith("s") and len(text) > 3:
        key2 = (text[:-1].lower(), label)
        canon2 = _ENTITY_ALIASES.get(key2)
        if canon2:
            return canon2
    return text


def normalize_entities(entities: list[dict]) -> list[dict]:
    """Normalize surface forms and deduplicate within a single article."""
    seen: set[tuple[str, str]] = set()
    result: list[dict] = []
    for ent in entities:
        normalized = _normalize_entity(ent["text"], ent["label"])
        key = (normalized, ent["label"])
        if key not in seen:
            seen.add(key)
            result.append({"text": normalized, "label": ent["label"]})
    return result


def _ner(text: str) -> list[dict]:
    doc = _spacy_model()(text[:NLP_TEXT_LIMIT])
    raw = [
        {"text": ent.text, "label": _LABEL_NORM.get(ent.label_, ent.label_)}
        for ent in doc.ents
        if ent.label_ in NER_LABELS
    ]
    return normalize_entities(raw)


def process_articles(raw_articles: list[dict]) -> list[dict]:
    """Process a batch of raw trafilatura dicts — NER + embeddings in one shot."""
    # Require at least a title or some body — title alone is enough for sentiment
    valid = [a for a in raw_articles if (a.get("title") or len(a.get("text") or "") >= 20)]
    if not valid:
        return []

    # NER per article (spaCy has no batch API worth using here)
    entities_list = [_ner(a["text"]) for a in valid]

    # Encode all texts in a single SBERT batch
    texts = [
        f"{a.get('title', '')}. {a['text'][:EMBEDDING_TEXT_LIMIT]}"
        for a in valid
    ]
    embeddings = _sbert_model().encode(texts, batch_size=32, show_progress_bar=True)

    # Sentiment on title + first 300 chars of body (fast, sufficient signal)
    sentiment_inputs = [
        f"{a.get('title', '')}. {a['text'][:300]}"
        for a in valid
    ]
    sentiment_results = _sentiment_pipeline()(sentiment_inputs, batch_size=32)

    results = []
    for a, entities, embedding, sent in zip(valid, entities_list, embeddings, sentiment_results):
        top = sent[0] if sent else {}
        emb_list = embedding.tolist()
        results.append({
            "title": a.get("title", ""),
            "text": a["text"],
            "url": a.get("url", ""),
            "author": a.get("author", ""),
            "date": a.get("date") or a.get("published", ""),
            "source": _canonical_source(a),
            "entities": entities,
            "embedding": emb_list,
            "link_url": a.get("link_url"),
            "sentiment": top.get("label") or "neutral",
            "sentiment_score": round(top.get("score", 0.5), 3),
            "topic": classify_topic(a.get("title", ""), a["text"], emb_list),
        })

    return results


def deduplicate(articles: list[dict], threshold: float = DEDUP_THRESHOLD) -> list[dict]:
    if not articles:
        return []

    from sklearn.metrics.pairwise import cosine_similarity

    embeddings = np.array([a["embedding"] for a in articles])
    sim = cosine_similarity(embeddings)

    keep: list[dict] = []
    seen: set[int] = set()

    for i, article in enumerate(articles):
        if i in seen:
            continue
        keep.append(article)
        for j in range(i + 1, len(articles)):
            if sim[i][j] > threshold:
                seen.add(j)

    return keep
