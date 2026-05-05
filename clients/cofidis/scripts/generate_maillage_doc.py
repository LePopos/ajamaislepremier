from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUTPUT = "/workspaces/ajamaislepremier/clients/cofidis/livrables/cahier_des_charges_maillage_cofidis.docx"

doc = Document()

for section in doc.sections:
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

doc.styles['Normal'].font.name = 'Arial'
doc.styles['Normal'].font.size = Pt(10)


def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), hex_color)
    shd.set(qn('w:val'), 'clear')
    tcPr.append(shd)


def h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)


def rule_block(page_type, rules):
    """One block per page type: bold label + bullet rules."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(page_type)
    r.bold = True
    r.font.size = Pt(10)
    for rule in rules:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_after = Pt(1)
        bp.paragraph_format.left_indent = Cm(0.5)
        bp.add_run(rule).font.size = Pt(10)


def fixed_links_table(urls):
    table = doc.add_table(rows=len(urls), cols=1)
    table.style = 'Table Grid'
    for i, url in enumerate(urls):
        cell = table.rows[i].cells[0]
        cell.text = url
        set_cell_bg(cell, 'F5F5F5' if i % 2 == 0 else 'FFFFFF')
        cell.paragraphs[0].runs[0].font.size = Pt(9)
        cell.paragraphs[0].paragraph_format.space_before = Pt(2)
        cell.paragraphs[0].paragraph_format.space_after = Pt(2)
    doc.add_paragraph()


# ── TITRE ─────────────────────────────────────────────────────────────────
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(4)
r = p.add_run('Règles de maillage interne — Cofidis')
r.bold = True
r.font.size = Pt(16)
r.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)

p2 = doc.add_paragraph('Principe : sur chaque page de contenu, ajouter des liens vers d\'autres pages du même sujet, organisés en 4 blocs.')
p2.paragraph_format.space_after = Pt(2)
p2.runs[0].font.size = Pt(10)

doc.add_paragraph()

# ── RÈGLES PAR TYPE DE PAGE ───────────────────────────────────────────────
h1('Règles par type de page')

rule_block('Page Q&A', [
    '5 liens vers d\'autres Q&A du même sujet (ex : "crédit cuisine")',
    '6 liens vers des guides du même sujet',
    '2 liens vers le ou les simulateurs du même sujet',
    '6 liens fixes (voir ci-dessous)',
])

rule_block('Page Guide', [
    '5 liens vers des Q&A du même sujet',
    '6 liens vers d\'autres guides du même sujet',
    '2 liens vers le ou les simulateurs du même sujet',
    '6 liens fixes (voir ci-dessous)',
])

rule_block('Page Produit', [
    '5 liens vers des Q&A du même sujet',
    '6 liens vers des guides du même sujet',
    '2 liens vers le ou les simulateurs du même sujet',
    '6 liens fixes (voir ci-dessous)',
])

rule_block('Page Hub', [
    '6 liens vers des guides du même sujet',
    '2 liens vers le ou les simulateurs du même sujet',
    '6 liens fixes (voir ci-dessous)',
])

rule_block('Simulateur / Lexique', [
    '6 liens fixes uniquement (voir ci-dessous)',
])

doc.add_paragraph()

# ── LIENS FIXES ───────────────────────────────────────────────────────────
h1('Les 6 liens fixes (présents sur toutes les pages)')

fixed_links_table([
    '/fr/credit/simulation-credit.html',
    '/fr/credit.html',
    '/fr/pret-personnel/pret-sur-mesure.html',
    '/fr/pret-personnel/simulation-pret.html',
    '/fr/credit/credit-renouvelable.html',
    '/fr/credit/credit-consommation.html',
])

# ── COMMENT TROUVER LE SUJET ──────────────────────────────────────────────
h1('Comment identifier le sujet d\'une page')

p = doc.add_paragraph('Le sujet est déterminé par l\'URL. Exemples :')
p.runs[0].font.size = Pt(10)
p.paragraph_format.space_after = Pt(4)

examples = [
    ('/fr/pret-personnel/credit-cuisine/...', 'sujet = Crédit cuisine'),
    ('/fr/pret-renovation-energetique/...', 'sujet = Rénovation énergétique'),
    ('/fr/pret-personnel/pret-travaux/...', 'sujet = Travaux'),
    ('/fr/credit/...', 'sujet = Crédit général'),
]
table = doc.add_table(rows=1 + len(examples), cols=2)
table.style = 'Table Grid'
for i, h in enumerate(['URL (début)', 'Sujet']):
    cell = table.rows[0].cells[i]
    cell.text = h
    set_cell_bg(cell, '1A1A2E')
    r = cell.paragraphs[0].runs[0]
    r.bold = True
    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    r.font.size = Pt(9)
    cell.paragraphs[0].paragraph_format.space_before = Pt(2)
    cell.paragraphs[0].paragraph_format.space_after = Pt(2)

for r_idx, (url, sujet) in enumerate(examples, 1):
    bg = 'F5F5F5' if r_idx % 2 != 0 else 'FFFFFF'
    for c_idx, val in enumerate([url, sujet]):
        cell = table.rows[r_idx].cells[c_idx]
        cell.text = val
        set_cell_bg(cell, bg)
        cell.paragraphs[0].runs[0].font.size = Pt(9)
        cell.paragraphs[0].paragraph_format.space_before = Pt(2)
        cell.paragraphs[0].paragraph_format.space_after = Pt(2)

table.columns[0].width = Cm(10)
table.columns[1].width = Cm(5)

doc.add_paragraph()

# ── NOTE ──────────────────────────────────────────────────────────────────
p = doc.add_paragraph('Note : si un sujet n\'a pas assez de guides (moins de 4), compléter avec des guides de sujets proches. Ex : Crédit cuisine → compléter avec des guides Travaux ou Crédit déco.')
p.runs[0].font.size = Pt(9)
p.runs[0].font.color.rgb = RGBColor(0x88, 0x88, 0x88)
p.paragraph_format.space_before = Pt(6)

doc.save(OUTPUT)
print('Done.')
