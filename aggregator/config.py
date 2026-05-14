import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "30"))

DEDUP_THRESHOLD = 0.92

NORWEGIAN_RSS_FEEDS = [
    # --- Google News topic feeds (100 entries each, covers 30+ outlets
    #     including all ~70 Amedia papers that have no RSS of their own) ---
    "https://news.google.com/rss?hl=no&gl=NO&ceid=NO:no",                                          # Top stories
    "https://news.google.com/rss/search?q=norsk+politikk&hl=no&gl=NO&ceid=NO:no",                 # Politikk
    "https://news.google.com/rss/search?q=norsk+økonomi&hl=no&gl=NO&ceid=NO:no",                  # Økonomi
    "https://news.google.com/rss/search?q=norsk+sport&hl=no&gl=NO&ceid=NO:no",                    # Sport
    "https://news.google.com/rss/search?q=kriminalitet+norge&hl=no&gl=NO&ceid=NO:no",             # Kriminalitet
    "https://news.google.com/rss/search?q=helse+norge&hl=no&gl=NO&ceid=NO:no",                    # Helse
    "https://news.google.com/rss/search?q=teknologi+norge&hl=no&gl=NO&ceid=NO:no",                # Teknologi
    "https://news.google.com/rss/search?q=klima+norge&hl=no&gl=NO&ceid=NO:no",                    # Klima
    "https://news.google.com/rss/search?q=utenriks+norge&hl=no&gl=NO&ceid=NO:no",                 # Utenriks

    # --- National broadcasters & tabloids ---
    "https://www.nrk.no/toppsaker.rss",
    "https://www.vg.no/rss/feed/",
    "https://www.tv2.no/rss/nyheter/",

    # --- National newspapers ---
    "https://www.aftenposten.no/rss/",
    "https://www.dagsavisen.no/rss/",

    # --- Business / finance / tech ---
    "https://e24.no/rss",
    "https://www.digi.no/rss",

    # --- Schibsted regionals ---
    "https://www.aftenbladet.no/rss.xml",   # Stavanger Aftenblad
    "https://www.fvn.no/rss.xml",           # Fædrelandsvennen (Kristiansand)
    "https://www.bt.no/rss.xml",            # Bergens Tidende

    # --- Polaris Media regionals ---
    "https://www.adressa.no/rss.xml",       # Adresseavisen (Trondheim)
    "https://www.smp.no/rss.xml",           # Sunnmørsposten (Ålesund)
    "https://www.rbnett.no/rss.xml",        # Romsdals Budstikke (Molde)
    "https://www.itromso.no/rss.xml",       # iTromsø
    "https://www.ht.no/rss.xml",            # Harstad Tidende

    # --- Independent regionals ---
    "https://www.sunnhordland.no/rss.xml",  # Sunnhordland
]

# Amedia (~70 papers) have removed RSS — covered via Google News above
RSS_UNAVAILABLE = ["dagbladet.no", "nettavisen.no", "klassekampen.no"]

# Domains known to require a full browser (JS-rendered or Cloudflare JS challenge)
PLAYWRIGHT_DOMAINS = {
    "digi.no",
    "tek.no",
    "itavisen.no",
}

SPACY_MODEL = "nb_core_news_lg"
SBERT_MODEL = "NbAiLab/nb-sbert-base"

NER_LABELS = {"PER", "ORG", "GPE", "LOC", "EVENT"}
NLP_TEXT_LIMIT = 5000
EMBEDDING_TEXT_LIMIT = 500
