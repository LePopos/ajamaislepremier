import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── CONFIG ────────────────────────────────────────────────────────────────

SITEMAP_URL = "https://www.cofidis.fr/sitemap.xml"
OUTPUT = "cofidis_maillage_mapping.xlsx"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SEO-audit/1.0)"}
TIMEOUT = 10

EXCLUDE_PREFIXES = [
    "/fr/espace-client/", "/fr/aide-et-contact/", "/fr/decouvrir-cofidis/",
    "/fr/infos_legales", "/fr/gestion-donnees", "/fr/accessibilite/", "/fr/index.html",
]
EXCLUDE_PATTERNS = [".cgi", ".aspx", "#"]

QA_KEYWORDS = [
    "comment", "pourquoi", "quand", "quel", "quelle", "quels", "peut-on",
    "faut-il", "combien", "est-ce", "quoi", "qui", "obtenir", "demander", "savoir",
]
TOOL_KEYWORDS = ["simulation", "simulateur", "calculette", "calculatrice"]

SILO_TO_ID = [
    ("pret-renovation-energetique", "id_renovation_energetique"),
    ("pret-personnel/pret-travaux", "id_travaux"),
    ("pret-personnel/credit-cuisine", "id_credit_cuisine"),
    ("pret-personnel/credit-auto", "id_credit_auto"),
    ("pret-personnel/credit-moto-scooter", "id_credit_moto"),
    ("pret-personnel/credit-salle-de-bain", "id_credit_sdb"),
    ("pret-personnel/credit-decoration", "id_credit_deco"),
    ("pret-personnel/credit-piscine", "id_credit_piscine"),
    ("pret-personnel/credit-veranda", "id_credit_veranda"),
    ("pret-personnel/credit-mariage", "id_credit_mariage"),
    ("pret-personnel/credit-voyage", "id_credit_voyage"),
    ("pret-personnel/credit-camping-car", "id_credit_campingcar"),
    ("pret-personnel/credit-demenagement", "id_credit_demenagement"),
    ("pret-personnel", "id_pret_personnel"),
    ("credit-velo", "id_credit_velo"),
    ("credit-auto", "id_credit_auto"),
    ("rachat-de-credit", "id_rachat_credit"),
    ("assurance", "id_assurance"),
    ("credit", "id_credit_general"),
    ("paiement-a-credit", "id_credit_general"),
    ("guide-credit", "id_credit_general"),
    ("guide-projets", "id_projets_general"),
    ("lexique-credit", "id_lexique"),
    ("tous-vos-projets", "id_projets_general"),
]

ID_PROCHES = {
    "id_renovation_energetique": ["id_travaux", "id_credit_general"],
    "id_travaux": ["id_renovation_energetique", "id_credit_cuisine", "id_credit_sdb"],
    "id_credit_cuisine": ["id_travaux", "id_credit_deco"],
    "id_credit_auto": ["id_credit_moto", "id_credit_velo"],
    "id_credit_moto": ["id_credit_auto", "id_credit_velo"],
    "id_pret_personnel": ["id_credit_general"],
    "id_credit_general": ["id_pret_personnel", "id_rachat_credit"],
    "id_rachat_credit": ["id_credit_general"],
    "id_assurance": ["id_credit_general"],
}

INCONTOURNABLES = [
    "https://www.cofidis.fr/fr/credit/simulation-credit.html",
    "https://www.cofidis.fr/fr/credit.html",
    "https://www.cofidis.fr/fr/pret-personnel/pret-sur-mesure.html",
    "https://www.cofidis.fr/fr/pret-personnel/simulation-pret.html",
    "https://www.cofidis.fr/fr/credit/credit-renouvelable.html",
    "https://www.cofidis.fr/fr/credit/credit-consommation.html",
]

DEFAULT_OUTIL = "https://www.cofidis.fr/fr/pret-personnel/simulation-pret.html"


# ── SITEMAP ───────────────────────────────────────────────────────────────

def fetch_urls(sitemap_url):
    urls = []
    try:
        r = requests.get(sitemap_url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"Erreur sitemap {sitemap_url}: {e}")
        fallback = sitemap_url.replace("sitemap.xml", "fr/sitemap.xml")
        try:
            r = requests.get(fallback, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
        except Exception as e2:
            print(f"Erreur fallback: {e2}")
            return []

    root = ET.fromstring(r.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # sitemap index
    sitemaps = root.findall("sm:sitemap/sm:loc", ns)
    if sitemaps:
        for s in sitemaps:
            urls.extend(fetch_urls(s.text.strip()))
        return urls

    # urlset
    for loc in root.findall("sm:url/sm:loc", ns):
        urls.append(loc.text.strip())
    return urls


# ── CLASSIFICATION ────────────────────────────────────────────────────────

def should_exclude(url):
    path = urlparse(url).path
    for p in EXCLUDE_PREFIXES:
        if path.startswith(p):
            return True
    for p in EXCLUDE_PATTERNS:
        if p in url:
            return True
    return False


def classify(url):
    path = urlparse(url).path
    # remove /fr/ prefix
    rel = path.lstrip("/")
    if rel.startswith("fr/"):
        rel = rel[3:]

    slug = rel.rstrip("/").split("/")[-1].replace(".html", "")
    depth = len([s for s in rel.rstrip("/").split("/") if s])

    if any(k in slug for k in TOOL_KEYWORDS) or any(k in rel for k in TOOL_KEYWORDS):
        return "OUTIL"
    if "lexique" in rel:
        return "LEXIQUE"
    if depth == 1 or rel.startswith("guide-"):
        return "HUB"
    if any(k in slug for k in QA_KEYWORDS):
        return "Q&A"
    if depth >= 3:
        return "GUIDE"
    if depth == 2:
        # if slug looks like a content page (long slug with hyphens), treat as Q&A or GUIDE
        if len(slug.split("-")) >= 3:
            return "Q&A"
        return "PRODUIT"
    return "AUTRE"


def get_id(url):
    path = urlparse(url).path
    rel = path.lstrip("/")
    if rel.startswith("fr/"):
        rel = rel[3:]
    rel = rel.rstrip("/").rstrip(".html")

    for silo, id_ in SILO_TO_ID:
        if rel.startswith(silo):
            return id_
    return "id_autre"


# ── MAPPING ───────────────────────────────────────────────────────────────

def build_mapping(pages):
    # pages: list of dicts {url, type, id}
    by_type_id = {}
    for p in pages:
        key = (p["type"], p["id"])
        by_type_id.setdefault(key, []).append(p["url"])

    results = []
    for p in pages:
        if p["type"] not in ("Q&A", "GUIDE", "PRODUIT", "HUB"):
            continue

        url = p["url"]
        tid = p["id"]

        # BLOC Q&A
        qa_pool = [u for u in by_type_id.get(("Q&A", tid), []) if u != url]
        bloc_qa = qa_pool[:5]

        # BLOC GUIDE
        guide_pool = [u for u in by_type_id.get(("GUIDE", tid), []) if u != url]
        if len(guide_pool) < 4:
            for proche in ID_PROCHES.get(tid, []):
                extra = [u for u in by_type_id.get(("GUIDE", proche), []) if u not in guide_pool and u != url]
                guide_pool.extend(extra)
        bloc_guide = guide_pool[:6]

        # BLOC OUTIL
        outil_pool = [u for u in by_type_id.get(("OUTIL", tid), [])]
        if not outil_pool:
            outil_pool = [DEFAULT_OUTIL]
        bloc_outil = outil_pool[:2]

        nb_qa = len(by_type_id.get(("Q&A", tid), []))
        nb_guide = len(by_type_id.get(("GUIDE", tid), []))

        results.append({
            "url": url,
            "type": p["type"],
            "id": tid,
            "bloc_qa": bloc_qa,
            "bloc_guide": bloc_guide,
            "bloc_incontournables": INCONTOURNABLES,
            "bloc_outil": bloc_outil,
            "nb_qa_dispo": nb_qa,
            "nb_guide_dispo": nb_guide,
        })
    return results


# ── EXCEL ─────────────────────────────────────────────────────────────────

DARK = "1A1A2E"
MID  = "E8E8F0"
WHITE = "FFFFFF"
LIGHT = "F5F5F5"

def hdr_style(cell, bg=DARK, fg=WHITE):
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.font = Font(bold=True, color=fg, size=9)
    cell.alignment = Alignment(wrap_text=True, vertical="center")

def cell_style(cell, bg=WHITE):
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.font = Font(size=9)
    cell.alignment = Alignment(wrap_text=False, vertical="center")

thin = Side(style="thin", color="CCCCCC")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

def apply_border(cell):
    cell.border = border


def write_excel(mapping, all_pages):
    wb = Workbook()

    # ── ONGLET MAPPING ────────────────────────────────────────────────────
    ws = wb.active
    ws.title = "Mapping"

    headers = (
        ["url_page", "type_page", "id_thematique"]
        + [f"bloc_qa_{i}" for i in range(1, 6)]
        + [f"bloc_guide_{i}" for i in range(1, 7)]
        + [f"bloc_inco_{i}" for i in range(1, 7)]
        + ["bloc_outil_1", "bloc_outil_2"]
        + ["nb_qa_dispo", "nb_guide_dispo"]
    )

    ws.append(headers)
    for i, h in enumerate(headers, 1):
        hdr_style(ws.cell(1, i))
        apply_border(ws.cell(1, i))
    ws.row_dimensions[1].height = 28

    for r_idx, m in enumerate(mapping, 2):
        bg = LIGHT if r_idx % 2 == 0 else WHITE
        row = (
            [m["url"], m["type"], m["id"]]
            + (m["bloc_qa"] + [""] * 5)[:5]
            + (m["bloc_guide"] + [""] * 6)[:6]
            + m["bloc_incontournables"]
            + (m["bloc_outil"] + [""] * 2)[:2]
            + [m["nb_qa_dispo"], m["nb_guide_dispo"]]
        )
        ws.append(row)
        for c_idx, _ in enumerate(row, 1):
            cell_style(ws.cell(r_idx, c_idx), bg)
            apply_border(ws.cell(r_idx, c_idx))

    ws.column_dimensions["A"].width = 60
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 28
    for col in range(4, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 55
    ws.freeze_panes = "D2"

    # ── ONGLET INVENTAIRE ─────────────────────────────────────────────────
    ws2 = wb.create_sheet("Inventaire")
    mapping_urls = {m["url"] for m in mapping}
    inv_headers = ["url", "type_page", "id_thematique", "inclus_mapping"]
    ws2.append(inv_headers)
    for i, h in enumerate(inv_headers, 1):
        hdr_style(ws2.cell(1, i))
        apply_border(ws2.cell(1, i))
    ws2.row_dimensions[1].height = 24

    for r_idx, p in enumerate(all_pages, 2):
        bg = LIGHT if r_idx % 2 == 0 else WHITE
        row = [p["url"], p["type"], p["id"], "OUI" if p["url"] in mapping_urls else "NON"]
        ws2.append(row)
        for c_idx, _ in enumerate(row, 1):
            cell_style(ws2.cell(r_idx, c_idx), bg)
            apply_border(ws2.cell(r_idx, c_idx))

    ws2.column_dimensions["A"].width = 70
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 28
    ws2.column_dimensions["D"].width = 16
    ws2.freeze_panes = "B2"

    wb.save(OUTPUT)


# ── MAIN ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Récupération du sitemap...")
    raw_urls = fetch_urls(SITEMAP_URL)
    print(f"  → {len(raw_urls)} URLs brutes")

    pages = []
    for url in raw_urls:
        if should_exclude(url):
            continue
        t = classify(url)
        if t == "AUTRE":
            continue
        pages.append({"url": url, "type": t, "id": get_id(url)})

    # stats
    from collections import Counter
    counts = Counter(p["type"] for p in pages)
    print(f"\nURLs conservées : {len(pages)}")
    for t, n in sorted(counts.items()):
        print(f"  {t:10} : {n}")

    print("\nConstruction du mapping...")
    mapping = build_mapping(pages)
    print(f"  → {len(mapping)} pages dans l'onglet Mapping")

    print("\nGénération Excel...")
    write_excel(mapping, pages)
    print(f"  → {OUTPUT} généré.")
