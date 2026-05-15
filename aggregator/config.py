import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "30"))

DEDUP_THRESHOLD = 0.92

NORWEGIAN_RSS_FEEDS = [
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
    "https://www.agderposten.no/rss.xml",   # Agderposten (Arendal)
    "https://www.varden.no/rss.xml",        # Varden (Skien)

    # --- Independent regionals with RSS ---
    "https://www.sunnhordland.no/rss.xml",  # Sunnhordland
    "https://www.innherred.no/rss.xml",     # Innherred (Levanger/Verdal)
    "https://www.tronderbladet.no/rss.xml", # Trønderbladet
    "https://www.avisa-st.no/rss.xml",      # Avisa Sør-Trøndelag
    "https://www.altaposten.no/rss.xml",    # Altaposten
    "https://www.folkebladet.no/rss.xml",   # Folkebladet (Finnsnes)
    "https://www.framtidinord.no/rss.xml",  # Framtid i Nord

    # --- Tech & investigative (direct RSS) ---
    "https://www.tu.no/rss",                # Teknisk Ukeblad (engineering/tech)
    "https://www.filternyheter.no/feed",    # Filter Nyheter (investigative)
]

# Domains with no RSS and no sitemap — covered by Google News only
RSS_UNAVAILABLE = ["nettavisen.no", "klassekampen.no"]

# News sitemaps — give direct article URLs, updated continuously.
# Replaces Google News for publishers that have them.
NORWEGIAN_NEWS_SITEMAPS = [
    # sitemap URL                                      publisher name
    ("https://www.dagbladet.no/sitemap.xml",          "Dagbladet"),
    ("https://www.dn.no/sitemap/news.xml",            "Dagens Næringsliv"),
]

# Amedia papers that have no RSS/sitemap — crawl their homepage for article links.
# Article URLs follow the pattern: /{slug}/{type}/5-{pub_id}-{article_id}
AMEDIA_PAPERS = [
    # homepage URL                        publisher name
    ("https://www.rb.no",                 "Romerikes Blad"),
    ("https://www.budstikka.no",          "Budstikka"),
    ("https://www.dt.no",                 "Drammens Tidende"),
    ("https://www.moss-avis.no",          "Moss Avis"),
    ("https://www.tb.no",                 "Tønsbergs Blad"),
    ("https://www.f-b.no",               "Fredriksstad Blad"),
    ("https://www.ha-halden.no",          "Halden Arbeiderblad"),
    ("https://www.h-avis.no",            "Haugesunds Avis"),
    ("https://www.ta.no",                 "Telemarksavisa"),
    ("https://www.an.no",                 "Avisa Nordland"),
    ("https://www.blv.no",               "Bladet Vesterålen"),
    ("https://www.lofotposten.no",        "Lofotposten"),
    ("https://www.fremover.no",           "Fremover"),
    ("https://www.namdalsavisa.no",       "Namdalsavisa"),
    ("https://www.oa.no",                 "Oppland Arbeiderblad"),
    ("https://www.gd.no",                 "Gudbrandsdølen Dagningen"),
]

# Canonical publisher names for each domain we ingest directly
DOMAIN_TO_NAME = {
    "nrk.no":              "NRK",
    "vg.no":               "VG",
    "tv2.no":              "TV2",
    "aftenposten.no":      "Aftenposten",
    "vink.aftenposten.no": "Aftenposten",
    "dagsavisen.no":       "Dagsavisen",
    "e24.no":              "E24",
    "digi.no":             "Digi.no",
    "aftenbladet.no":      "Stavanger Aftenblad",
    "fvn.no":              "Fædrelandsvennen",
    "bt.no":               "Bergens Tidende",
    "adressa.no":          "Adresseavisen",
    "smp.no":              "Sunnmørsposten",
    "rbnett.no":           "Romsdals Budstikke",
    "itromso.no":          "iTromsø",
    "ht.no":               "Harstad Tidende",
    "sunnhordland.no":     "Sunnhordland",
    "tu.no":               "Teknisk Ukeblad",
    "filternyheter.no":    "Filter Nyheter",
    "dagbladet.no":        "Dagbladet",
    "dn.no":               "Dagens Næringsliv",
    # Polaris regionals (newly added RSS)
    "agderposten.no":      "Agderposten",
    "varden.no":           "Varden",
    # Independent regionals (newly added RSS)
    "innherred.no":        "Innherred",
    "tronderbladet.no":    "Trønderbladet",
    "avisa-st.no":         "Avisa Sør-Trøndelag",
    "altaposten.no":       "Altaposten",
    "folkebladet.no":      "Folkebladet",
    "framtidinord.no":     "Framtid i Nord",
    # Amedia papers (homepage crawler)
    "rb.no":               "Romerikes Blad",
    "budstikka.no":        "Budstikka",
    "dt.no":               "Drammens Tidende",
    "moss-avis.no":        "Moss Avis",
    "tb.no":               "Tønsbergs Blad",
    "f-b.no":              "Fredriksstad Blad",
    "ha-halden.no":        "Halden Arbeiderblad",
    "h-avis.no":           "Haugesunds Avis",
    "ta.no":               "Telemarksavisa",
    "an.no":               "Avisa Nordland",
    "blv.no":              "Bladet Vesterålen",
    "lofotposten.no":      "Lofotposten",
    "fremover.no":         "Fremover",
    "namdalsavisa.no":     "Namdalsavisa",
    "oa.no":               "Oppland Arbeiderblad",
    "gd.no":               "Gudbrandsdølen Dagningen",
}

# Search URL templates for Google News articles.
# We can't decode CBMi tokens server-side (GDPR consent gate blocks redirect following),
# so for Google News articles we link to the publisher's own search page instead.
# {title} is replaced with the URL-encoded article title.
# Domains not listed here fall back to a Google Search scoped to the publisher's domain.
DOMAIN_TO_SEARCH = {
    "nrk.no":           "https://www.nrk.no/sok/?q={title}",
    "vg.no":            "https://www.vg.no/sok/?q={title}",
    "tv2.no":           "https://www.tv2.no/sok/?q={title}",
    "aftenposten.no":   "https://www.aftenposten.no/sok/?q={title}",
    "dagbladet.no":     "https://www.dagbladet.no/sok/?q={title}",
    "dagsavisen.no":    "https://www.dagsavisen.no/sok/?q={title}",
    "nettavisen.no":    "https://www.nettavisen.no/sok/?q={title}",
    "e24.no":           "https://e24.no/sok/?q={title}",
    "digi.no":          "https://www.digi.no/sok?q={title}",
    "aftenbladet.no":   "https://www.aftenbladet.no/sok/?q={title}",
    "fvn.no":           "https://www.fvn.no/sok/?q={title}",
    "bt.no":            "https://www.bt.no/sok/?q={title}",
    "adressa.no":       "https://www.adressa.no/sok/?q={title}",
    "smp.no":           "https://www.smp.no/sok/?q={title}",
    "rbnett.no":        "https://www.rbnett.no/sok/?q={title}",
    "itromso.no":       "https://www.itromso.no/sok/?q={title}",
    "ht.no":            "https://www.ht.no/sok/?q={title}",
    "sunnhordland.no":  "https://www.sunnhordland.no/sok/?q={title}",
    "tu.no":            "https://www.tu.no/sok?q={title}",
    "filternyheter.no": "https://www.filternyheter.no/?s={title}",
    "dn.no":            "https://www.dn.no/sok/?q={title}",
    "klassekampen.no":  "https://www.klassekampen.no/sok/?q={title}",
    "agderposten.no":   "https://www.agderposten.no/sok/?q={title}",
    "varden.no":        "https://www.varden.no/sok/?q={title}",
    "rb.no":            "https://www.rb.no/sok/?q={title}",
    "budstikka.no":     "https://www.budstikka.no/sok/?q={title}",
    "dt.no":            "https://www.dt.no/sok/?q={title}",
    "moss-avis.no":     "https://www.moss-avis.no/sok/?q={title}",
    "tb.no":            "https://www.tb.no/sok/?q={title}",
    "f-b.no":           "https://www.f-b.no/sok/?q={title}",
    "ha-halden.no":     "https://www.ha-halden.no/sok/?q={title}",
    "h-avis.no":        "https://www.h-avis.no/sok/?q={title}",
    "ta.no":            "https://www.ta.no/sok/?q={title}",
    "an.no":            "https://www.an.no/sok/?q={title}",
    "blv.no":           "https://www.blv.no/sok/?q={title}",
    "lofotposten.no":   "https://www.lofotposten.no/sok/?q={title}",
    "fremover.no":      "https://www.fremover.no/sok/?q={title}",
    "namdalsavisa.no":  "https://www.namdalsavisa.no/sok/?q={title}",
    "oa.no":            "https://www.oa.no/sok/?q={title}",
    "gd.no":            "https://www.gd.no/sok/?q={title}",
}

# Domains known to require a full browser (JS-rendered or Cloudflare JS challenge)
PLAYWRIGHT_DOMAINS = {
    "digi.no",
    "tek.no",
    "itavisen.no",
}

# URL substrings to skip during extraction (video pages, RSS-only paths, etc.)
SKIP_URL_PATTERNS = [
    "tv.itromso.no",     # iTromsø video subdomain — no article text
    "tv.adressa.no",     # Adresseavisen video subdomain
    "/tv/n/",            # Polaris Media video path pattern
    "/video/",           # Generic video path
    "playlistId=",       # Schibsted video/audio story pages (aftenbladet, bt, fvn, etc.)
]

SPACY_MODEL = "nb_core_news_lg"
SBERT_MODEL = "NbAiLab/nb-sbert-base"

NER_LABELS = {"PER", "ORG", "GPE", "LOC", "EVENT"}
NLP_TEXT_LIMIT = 5000
EMBEDDING_TEXT_LIMIT = 500
