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

    # --- Publishers previously only reached via Google News ---
    "https://morgenbladet.no/rss",          # Morgenbladet (weekly quality newspaper)
    "https://hallingdolen.no/rss",          # Hallingdølen (Hallingdal regional)

    # --- NRK thematic channels ---
    "https://www.nrk.no/sport/toppsaker.rss",   # NRK Sport
    "https://www.nrk.no/urix/toppsaker.rss",    # NRK Urix (foreign affairs)
    "https://www.nrk.no/kultur/toppsaker.rss",  # NRK Kultur

    # --- NRK regional ---
    "https://www.nrk.no/rogaland/toppsaker.rss",
    "https://www.nrk.no/vestland/toppsaker.rss",
    "https://www.nrk.no/trondelag/toppsaker.rss",
    "https://www.nrk.no/innlandet/toppsaker.rss",
    "https://www.nrk.no/nordland/toppsaker.rss",
    "https://www.nrk.no/mr/toppsaker.rss",          # Møre og Romsdal
    "https://www.nrk.no/osloogviken/toppsaker.rss",
    "https://www.nrk.no/agder/toppsaker.rss",
    "https://www.nrk.no/tromsogfinnmark/toppsaker.rss",

    # --- Trade / niche ---
    "https://www.kampanje.com/rss/",        # Kampanje (marketing & media industry)
    "https://rett24.no/rss/",               # Rett24 (legal news)
    "https://www.energiogklima.no/feed/",   # Energi og Klima (climate/energy policy)

    # --- Polaris Media regionals with RSS ---
    "https://www.vol.no/rss",              # Vesterålen Online (Polaris regional)
    "https://www.driva.no/rss.xml",        # Driva (Sunndalsøra)
    "https://www.fosna-folket.no/rss",     # Fosna-Folket / Bladet Fosen (Fosen peninsula)
]

# Domains with no RSS and no sitemap — paywall/subscriber-only
RSS_UNAVAILABLE = ["klassekampen.no"]

# News sitemaps — give direct article URLs, updated continuously.
# Replaces Google News for publishers that have them.
NORWEGIAN_NEWS_SITEMAPS = [
    # sitemap URL                                      publisher name
    ("https://www.dagbladet.no/sitemap.xml",          "Dagbladet"),
    ("https://www.dn.no/sitemap/news.xml",            "Dagens Næringsliv"),
    ("https://www.vl.no/sitemap.xml",                 "Vårt Land"),
    ("https://www.dagen.no/sitemap.xml",              "Dagen"),
    ("https://www.shifter.no/sitemap.xml",            "Shifter"),
    # Paginated sitemap — first page always has the newest articles
    ("https://www.abcnyheter.no/sitemap?start=0&pageType=article", "ABC Nyheter"),
    ("https://www.khrono.no/sitemap.xml",             "Khrono"),
    ("https://www.forskning.no/sitemap.xml",          "Forskning.no"),
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

    # --- High-traffic national / major regionals (also Amedia) ---
    ("https://www.nettavisen.no",         "Nettavisen"),

    # --- Polaris Media regionals on Amedia platform ---
    ("https://www.nordlys.no",            "Nordlys"),         # Tromsø/Nord-Norge
    ("https://www.t-a.no",               "Trønder-Avisa"),   # Steinkjer/Trøndelag
    ("https://www.h-a.no",               "Hamar Arbeiderblad"),
    ("https://www.ranablad.no",           "Rana Blad"),       # Mo i Rana

    # --- Other Amedia regionals ---
    ("https://www.nationen.no",           "Nationen"),        # Agriculture/rural
    ("https://www.glomdalen.no",          "Glåmdalen"),       # Kongsvinger/Hedmark
    ("https://www.ostlendingen.no",       "Østlendingen"),    # Elverum/Hedmark
    ("https://www.nidaros.no",            "Nidaros"),         # Trondheim online
    ("https://www.steinkjer-avisa.no",    "Steinkjer-Avisa"), # Nord-Trøndelag

    # --- Amedia Østfold ---
    ("https://www.sa.no",                 "Sarpsborg Arbeiderblad"),
    ("https://www.smaalenene.no",         "Smaalenenes Avis"),# Askim/Mysen

    # --- Amedia Vestfold ---
    ("https://www.sb.no",                 "Sandefjords Blad"),

    # --- Amedia Telemark / Numedal ---
    ("https://www.laagendalsposten.no",   "Laagendalsposten"),# Kongsberg
    ("https://www.telen.no",              "Telen"),           # Notodden
    ("https://www.pd.no",                 "Porsgrunns Dagblad"),
    ("https://www.vtb.no",                "Vest-Telemark Blad"),

    # --- Amedia Agder ---
    ("https://www.firda.no",              "Firda"),           # Nordfjordeid
    ("https://www.sognavis.no",           "Sogn Avis"),       # Sogndal

    # --- Amedia Nordland ---
    ("https://www.helgelendingen.no",     "Helgelendingen"),  # Sandnessjøen

    # --- Amedia Troms og Finnmark ---
    ("https://www.finnmarken.no",         "Finnmarken"),      # Vadsø

    # --- Amedia Akershus ---
    ("https://www.rha.no",                "Akershus Amtstidende"),

    # --- Amedia Vestfold ---
    ("https://www.op.no",                 "Østlandsposten"),      # Larvik
    ("https://www.gjengangeren.no",       "Gjengangeren"),        # Horten
    ("https://www.oyene.no",              "Øyene"),               # Nøtterøy/Tjøme

    # --- Amedia Rogaland (small) ---
    ("https://www.ryfylke.no",            "Ryfylke"),             # Sauda/Suldal

    # --- Amedia Vestland (small) ---
    ("https://www.hardanger-folkeblad.no","Hardanger Folkeblad"), # Odda

    # --- Amedia Møre og Romsdal (via RSS-less Amedia CMS) ---
    ("https://www.ba.no",                 "Bergensavisen"),        # Bergen (Amedia)
    ("https://www.tk.no",                 "Tidens Krav"),          # Kristiansund (Amedia)
    ("https://www.bygdebladet.no",        "Bygdebladet"),          # Averøy

    # --- Amedia Trøndelag (small) ---
    ("https://www.inderoyningen.no",      "Inderøyningen"),       # Inderøy
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
    "morgenbladet.no":     "Morgenbladet",
    "hallingdolen.no":     "Hallingdølen",
    "hegnar.no":           "Hegnar Online",
    "khrono.no":           "Khrono",
    "forskning.no":        "Forskning.no",
    "finansavisen.no":     "Finansavisen",
    "vl.no":               "Vårt Land",
    "dagen.no":            "Dagen",
    "shifter.no":          "Shifter",
    "abcnyheter.no":       "ABC Nyheter",
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
    # Newly added Amedia papers
    "nettavisen.no":       "Nettavisen",
    "nordlys.no":          "Nordlys",
    "t-a.no":              "Trønder-Avisa",
    "h-a.no":              "Hamar Arbeiderblad",
    "ranablad.no":         "Rana Blad",
    "nationen.no":         "Nationen",
    "glomdalen.no":        "Glåmdalen",
    "ostlendingen.no":     "Østlendingen",
    "nidaros.no":          "Nidaros",
    "steinkjer-avisa.no":  "Steinkjer-Avisa",
    # Polaris regionals (RSS)
    "ba.no":               "Bergensavisen",
    "tk.no":               "Tidens Krav",
    "driva.no":            "Driva",
    "vol.no":              "Vesterålen Online",
    "fosna-folket.no":     "Bladet Fosen",
    # Amedia Vestland
    "firda.no":            "Firda",
    "sognavis.no":         "Sogn Avis",
    # Amedia Nordland
    "helgelendingen.no":   "Helgelendingen",
    # Amedia Troms og Finnmark
    "finnmarken.no":       "Finnmarken",
    # Amedia Akershus
    "rha.no":              "Akershus Amtstidende",
    # Amedia Vestfold
    "op.no":               "Østlandsposten",
    "gjengangeren.no":     "Gjengangeren",
    "oyene.no":            "Øyene",
    # Amedia Rogaland (small)
    "ryfylke.no":          "Ryfylke",
    # Amedia Vestland (small)
    "hardanger-folkeblad.no": "Hardanger Folkeblad",
    # Amedia Møre og Romsdal
    "bygdebladet.no":      "Bygdebladet",
    # Amedia Trøndelag (small)
    "inderoyningen.no":    "Inderøyningen",
    # Trade / niche
    "kampanje.com":        "Kampanje",
    "rett24.no":           "Rett24",
    "energiogklima.no":    "Energi og Klima",
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
    "news.google.com",   # Google News redirect stubs — body is just the title (66-76 chars)
    "google.com/search", # Google Search fallback URLs — not articles
    "google.com/sorry",  # Google rate-limit page
    "/sok/?q=",          # Publisher search pages (fvn, adressa, etc.) — not articles
    "/search?q=",        # Generic publisher search pages
    "vgtv",              # VG video teasers ("Se X på 25 minutter - VGTV")
    "/v/5-",             # Amedia video article type
]

SPACY_MODEL = "nb_core_news_lg"
SBERT_MODEL = "NbAiLab/nb-sbert-base"
SENTIMENT_MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

# nb_core_news_lg uses GPE_LOC/GPE_ORG (not GPE) and EVT (not EVENT)
NER_LABELS = {"PER", "ORG", "GPE_LOC", "GPE_ORG", "LOC", "EVT"}
NLP_TEXT_LIMIT = 5000
EMBEDDING_TEXT_LIMIT = 500
