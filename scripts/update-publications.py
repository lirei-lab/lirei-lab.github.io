#!/usr/bin/env python3
"""Finds Professor Agbossou's new publications and adds them to the catalogue.

Three sources, each used for what it does well:

- Crossref holds the publisher's own record — title, authors, venue, DOI, date.
  It is the only source whose metadata is written into the catalogue.
- OpenAlex has already resolved Agbossou's name to a single author, so it
  catches papers that Crossref's fuzzy name search ranks too low. Only its DOIs
  are used; each one is then looked up in Crossref.
- Google Scholar is the profile the laboratory keeps by hand, and the most
  complete, but it has no API and turns away servers. It is read only on
  request, from a workstation, as a cross-check: a title it lists that neither
  other source found is looked up in Crossref by title, and whatever still has
  no DOI (a patent, a thesis) is reported for a person to decide.

Existing entries are never modified. A work already in the catalogue — by DOI
or by title — is skipped, so hand corrections survive every run.

    python3 scripts/update-publications.py               # report only, writes nothing
    python3 scripts/update-publications.py --write       # add new entries, rebuild the topic map
    python3 scripts/update-publications.py --scholar     # also cross-check Google Scholar
    python3 scripts/update-publications.py --scholar-file page.html   # … from a saved page
    python3 scripts/update-publications.py --since 2019  # look further back (default: last year)
    python3 scripts/update-publications.py --summary out.md  # Markdown summary, for a pull request
"""

import argparse
import datetime
import difflib
import glob
import html
import json
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBS = ROOT / 'src/content/publications'

ORCID = '0000-0003-1441-424X'
OPENALEX_AUTHOR = 'A5008090389'
SCHOLAR_USER = 'KRJCGE8AAAAJ'
# The laboratory's public address: Crossref and OpenAlex serve identified
# callers from a faster, more reliable pool.
CONTACT = 'lirei.info@uqtr.ca'
USER_AGENT = f'lireiweb-publications/1.0 (https://lirei-lab.github.io; mailto:{CONTACT})'

# A preprint is left out: the published version follows, and would otherwise
# appear twice under two DOIs.
KEPT_TYPES = {'journal-article', 'proceedings-article', 'book-chapter'}
# Errata, a journal's yearly author index, a thesis chapter Scholar lists apart.
NOT_A_PAPER = re.compile(r'^(correction|corrigendum|erratum|retraction)\b|\bindex\b.*\bvol\b'
                         r'|^\d+(\.\d+)*\s+article\s+\d+\s*:', re.I)
PROCEEDINGS = re.compile(r'proceedings|conference|symposium|congress|lecture notes', re.I)

# Surname particles, which say nothing about who a co-author is.
PARTICLES = {'de', 'del', 'der', 'des', 'da', 'di', 'do', 'dos', 'du', 'la', 'le', 'los', 'van', 'von', 'y'}


# — Text ————————————————————————————————————————————————————————————————————

def fold(text: str) -> str:
    """Lowercase, strip accents."""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower()


def words(text: str) -> list[str]:
    return [w for w in re.split(r'[^a-z0-9]+', fold(text)) if w]


def title_key(title: str) -> str:
    """What two spellings of one title have in common: letters and digits."""
    return ''.join(words(title))


def clean(text: str) -> str:
    """Crossref titles carry JATS markup and HTML entities."""
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', text))).strip()


def slug(year: int, title: str) -> str:
    """The catalogue's file names: the year and the title's first six words."""
    return f"{year}-" + '-'.join(words(title)[:6])


# — HTTP ————————————————————————————————————————————————————————————————————

def fetch(url: str, *, accept='application/json', user_agent=USER_AGENT) -> bytes | None:
    """GET with a few patient retries. A 404 is an answer, not a failure."""
    request = urllib.request.Request(url, headers={'User-Agent': user_agent, 'Accept': accept})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            if err.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
        except urllib.error.URLError:
            if attempt == 3:
                raise
        time.sleep(2 ** attempt * 2)
    return None


def get_json(url: str, **params) -> dict | None:
    body = fetch(f"{url}?{urllib.parse.urlencode(params)}" if params else url)
    return json.loads(body) if body else None


# — Who is Kodjo Agbossou ———————————————————————————————————————————————————

def colleague_surnames() -> set[str]:
    """Surnames of everyone on the team or among its graduates."""
    names = set()
    for path in glob.glob(str(ROOT / 'src/content/team/*.json')) + \
            glob.glob(str(ROOT / 'src/content/alumni/*.json')):
        name = json.load(open(path, encoding='utf-8'))['name']
        names.update(w for w in words(name)[1:] if len(w) > 2 and w not in PARTICLES)
    names.discard('agbossou')
    return names


def by_agbossou(work: dict, colleagues: set[str]) -> bool:
    """Is Kodjo Agbossou among this work's authors?

    Other Agbossous publish too — Igor in urban planning, Kokou in photonics —
    so the surname alone is not enough. An ORCID settles it, and so does the
    given name. A bare initial is accepted only alongside a known co-author.
    """
    authors = work.get('author', [])
    for author in authors:
        family, given = fold(author.get('family', '')), fold(author.get('given', ''))
        if not given and ' ' in family:  # "AGBOSSOU K", with nothing in `given`
            family, _, given = family.partition(' ')
        if family.strip() != 'agbossou':
            continue
        if author.get('ORCID', '').endswith(ORCID) or given.startswith('kodjo'):
            return True
        if words(given) == ['k']:
            others = {w for a in authors if a is not author for w in words(a.get('family', ''))}
            if others & colleagues:
                return True
    return False


# — Crossref records to catalogue entries ——————————————————————————————————

def initials(given: str) -> str:
    """"Juan Carlos" → "J. C.", "Jean-Philippe" → "J.-P."."""
    return ' '.join('-'.join(part[0].upper() + '.' for part in chunk.split('-') if part)
                    for chunk in given.replace('.', ' ').split())


def author_name(author: dict) -> str:
    if 'family' not in author:
        return clean(author.get('name', ''))
    given = initials(author.get('given', ''))
    return f"{given} {clean(author['family'])}".strip()


def entry(work: dict, spellings: dict[str, str]) -> dict:
    title = clean((work.get('title') or [''])[0])
    subtitle = clean((work.get('subtitle') or [''])[0])
    if subtitle and title_key(subtitle) not in title_key(title):
        title = f"{title}: {subtitle}"
    # A chapter's containers run from the book series down to the volume
    # ("Environmental Science and Engineering", "Proceedings of the 5th …"):
    # the proceedings, when there are some, say more than the series does.
    containers = [clean(c) for c in work.get('container-title') or []] or ['']
    venue = next((c for c in containers if PROCEEDINGS.search(c)), containers[0])
    kind = {'journal-article': 'journal', 'proceedings-article': 'conference'}.get(work['type'])
    if kind is None:
        kind = 'conference' if PROCEEDINGS.search(venue) else 'other'

    record = {
        'title': title,
        'authors': [spellings.get(fold(name), name)
                    for name in map(author_name, work.get('author', []))],
        'venue': venue,
        # `issued` is the earliest of print and online: an article belongs to
        # the year it became readable, not to the issue that later collected it.
        'year': work['issued']['date-parts'][0][0],
        'type': kind,
        'doi': work['DOI'].lower() if work['DOI'].startswith('10.') else work['DOI'],
    }
    if not venue:
        del record['venue']
    return record


def keepable(work: dict) -> bool:
    title = (work.get('title') or [''])[0]
    return (work.get('type') in KEPT_TYPES and bool(title) and not NOT_A_PAPER.search(title)
            and bool((work.get('issued') or {}).get('date-parts', [[None]])[0][0]))


# — Sources —————————————————————————————————————————————————————————————————

def crossref_search(since: int) -> list[dict]:
    """Every Crossref work since `since` crediting someone named Agbossou."""
    works, cursor = [], '*'
    while True:
        page = get_json('https://api.crossref.org/works',
                        **{'query.author': 'Kodjo Agbossou',
                           'filter': f'from-pub-date:{since}-01-01,' + ','.join(f'type:{t}' for t in sorted(KEPT_TYPES)),
                           'rows': 200, 'cursor': cursor, 'mailto': CONTACT})['message']
        if not page['items']:
            return works
        works += [w for w in page['items']
                  if any(fold(a.get('family', '')).startswith('agbossou') for a in w.get('author', []))]
        cursor = page['next-cursor']


def openalex_dois(since: int) -> set[str]:
    dois, cursor = set(), '*'
    while cursor:
        page = get_json('https://api.openalex.org/works',
                        filter=f'authorships.author.id:{OPENALEX_AUTHOR},from_publication_date:{since}-01-01',
                        select='doi', per_page=200, cursor=cursor, mailto=CONTACT)
        dois.update(w['doi'].removeprefix('https://doi.org/').lower() for w in page['results'] if w['doi'])
        cursor = page['meta'].get('next_cursor')
    return dois


def crossref_work(doi: str) -> dict | None:
    page = get_json(f'https://api.crossref.org/works/{urllib.parse.quote(doi)}', mailto=CONTACT)
    return page['message'] if page else None


def crossref_by_title(title: str) -> dict | None:
    page = get_json('https://api.crossref.org/works',
                    **{'query.bibliographic': title, 'query.author': 'Agbossou',
                       'rows': 3, 'mailto': CONTACT})
    for work in page['message']['items']:
        found = (work.get('title') or [''])[0]
        if difflib.SequenceMatcher(None, title_key(found), title_key(title)).ratio() > 0.92:
            return work
    return None


def scholar_rows(saved_page: str | None, since: int) -> list[dict]:
    """The profile's most recent hundred works, newest first.

    One page, no pagination: Scholar's robots.txt allows /citations?user= but
    not the cstart= that pages further.
    """
    if saved_page:
        text = Path(saved_page).read_text(encoding='utf-8')
    else:
        url = ('https://scholar.google.com/citations?user=' + SCHOLAR_USER +
               '&view_op=list_works&sortby=pubdate&pagesize=100&hl=en')
        text = fetch(url, accept='text/html',
                     user_agent='Mozilla/5.0 (X11; Linux x86_64) lireiweb-publications/1.0').decode('utf-8')
    rows = []
    for row in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', text, re.S):
        title = re.search(r'class="gsc_a_at"[^>]*>(.*?)</a>', row, re.S)
        year = re.search(r'gsc_a_h gsc_a_hc gs_ibl[^>]*>(\d{4})<', row)
        if not (title and year):
            continue
        gray = [clean(g) for g in re.findall(r'<div class="gs_gray">(.*?)</div>', row, re.S)]
        rows.append({'title': clean(title.group(1)), 'year': int(year.group(1)),
                     'authors': gray[0] if gray else '', 'venue': gray[1] if len(gray) > 1 else ''})
    if not rows and 'gsc_a_tr' not in text:
        sys.exit("Google Scholar n'a pas renvoyé la liste (captcha ?). Enregistrez la page "
                 "depuis un navigateur et relancez avec --scholar-file.")
    return [r for r in rows if r['year'] >= since and not NOT_A_PAPER.search(r['title'])]


# — Catalogue ———————————————————————————————————————————————————————————————

def load_catalogue():
    """DOIs and titles already listed, and how each author's name is spelled.

    Crossref often drops accents ("Caballero-Pena"); a name the catalogue
    already carries keeps the spelling it has there.
    """
    dois, titles, spellings = set(), [], {}
    for path in sorted(glob.glob(str(PUBS / '*.json'))):
        data = json.load(open(path, encoding='utf-8'))
        if data.get('doi'):
            dois.add(data['doi'].lower())
        titles.append(title_key(data['title']))
        for name in data['authors']:
            if name != fold(name) or fold(name) not in spellings:
                spellings[fold(name)] = name
    return dois, titles, spellings


def known(key: str, titles: list[str]) -> bool:
    """Titles differ in punctuation, casing and the odd dropped space."""
    return key in titles or bool(difflib.get_close_matches(key, titles, n=1, cutoff=0.95))


def main():
    this_year = datetime.date.today().year
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--since', type=int, default=this_year - 1,
                        help='première année examinée (défaut : année précédente)')
    parser.add_argument('--write', action='store_true',
                        help='écrit les nouvelles fiches et régénère la carte des sujets')
    parser.add_argument('--scholar', action='store_true', help='recoupe avec Google Scholar')
    parser.add_argument('--scholar-file', help='page Google Scholar enregistrée (HTML)')
    parser.add_argument('--summary', help='écrit un résumé Markdown dans ce fichier')
    args = parser.parse_args()

    colleagues = colleague_surnames()
    cat_dois, cat_titles, spellings = load_catalogue()

    works = {w['DOI'].lower(): w for w in crossref_search(args.since)}
    print(f"Crossref : {len(works)} travaux signés Agbossou depuis {args.since}")

    extra = openalex_dois(args.since) - works.keys() - cat_dois
    print(f"OpenAlex : {len(extra)} DOI supplémentaires à vérifier dans Crossref")
    for doi in sorted(extra):
        if (work := crossref_work(doi)) is not None:
            works[doi] = work

    unresolved = []
    if args.scholar or args.scholar_file:
        rows = scholar_rows(args.scholar_file, args.since)
        found_titles = [title_key((w.get('title') or [''])[0]) for w in works.values()]
        missing = [r for r in rows if not known(title_key(r['title']), cat_titles + found_titles)]
        print(f"Google Scholar : {len(rows)} travaux depuis {args.since}, "
              f"{len(missing)} absents du catalogue et des autres sources")
        for row in missing:
            work = crossref_by_title(row['title'])
            if work is None:
                unresolved.append(row)
            else:
                works[work['DOI'].lower()] = work

    new, doubtful = {}, []
    for doi, work in sorted(works.items()):
        if doi in cat_dois or not keepable(work):
            continue
        if not by_agbossou(work, colleagues):
            if doi in extra:  # OpenAlex attributed it to him; Crossref cannot confirm
                doubtful.append(work)
            continue
        record = entry(work, spellings)
        key = title_key(record['title'])
        if known(key, cat_titles) or any(title_key(r['title']) == key for r in new.values()):
            continue
        name = slug(record['year'], record['title'])
        while name in new or (PUBS / f'{name}.json').exists():
            name = re.sub(r'(-\d+)?$', lambda m: f'-{int((m.group(1) or "-1")[1:]) + 1}', name, count=1)
        new[name] = record

    report(new, doubtful, unresolved, args)

    if args.write and new:
        for name, record in new.items():
            (PUBS / f'{name}.json').write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f"\n{len(new)} fiches écrites dans {PUBS.relative_to(ROOT)}/")
        subprocess.run([sys.executable, str(ROOT / 'scripts/build-topics.py')], check=True)
    elif new:
        print('\nRien n’a été écrit. Relancez avec --write pour ajouter ces publications.')


def report(new, doubtful, unresolved, args):
    lines = []
    if new:
        lines.append(f"## {len(new)} nouvelle(s) publication(s)\n")
        for name, r in sorted(new.items(), reverse=True):
            lines.append(f"- **{r['year']}** · {r['type']} · [{r['title']}](https://doi.org/{r['doi']})  \n"
                         f"  {', '.join(r['authors'])} — *{r.get('venue', '—')}*")
    else:
        lines.append('Aucune nouvelle publication.')
    if doubtful:
        lines.append(f"\n## {len(doubtful)} attribuée(s) par OpenAlex, sans « Kodjo Agbossou » dans Crossref\n")
        lines.append('Non ajoutées. À vérifier à la main.\n')
        for w in doubtful:
            lines.append(f"- {clean((w.get('title') or [''])[0])} — https://doi.org/{w['DOI']}")
    if unresolved:
        lines.append(f"\n## {len(unresolved)} sur Google Scholar sans DOI trouvé\n")
        lines.append('Brevets, thèses, chapitres : non ajoutés. Créez la fiche à la main si elle a sa place.\n')
        for r in unresolved:
            lines.append(f"- **{r['year']}** · {r['title']} — {r['authors']} — *{r['venue']}*")
    text = '\n'.join(lines) + '\n'
    print('\n' + text)
    if args.summary:
        Path(args.summary).write_text(text, encoding='utf-8')


if __name__ == '__main__':
    main()
