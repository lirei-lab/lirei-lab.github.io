#!/usr/bin/env python3
"""Builds the topic co-occurrence graph drawn on the publications page.

The catalogue gives us titles and nothing else — no abstracts, no keywords — so
the topics cannot be mined statistically: raw n-grams return "proton exchange
membrane", "exchange membrane fuel" and "pem fuel cell" as three different
things. They are instead a curated vocabulary, each entry a pair of labels
(the site is bilingual, and English n-grams do not translate themselves) and a
set of patterns matched against the title.

Two publications share an edge when they carry both topics. Positions come from
a seeded force-directed layout computed here, once, so the page ships a finished
picture rather than a simulation the browser has to run.

    python3 scripts/build-topics.py        # writes src/data/topics.json
    python3 scripts/build-topics.py --audit # coverage report, writes nothing
"""

import glob
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Five thematic domains carry a hue; the sixth is deliberately neutral. Methods
# are tools used across every domain, and a grey that reads as "not a domain"
# says so better than a sixth colour would — six hues cannot be kept apart
# under protanopia anyway. Hues validated with the dataviz palette checker
# (all pairs, light surface): lightness band, chroma floor, CVD separation,
# normal-vision floor and contrast all pass.
DOMAINS = {
    'hydrogen':   {'color': '#15599e', 'fr': 'Hydrogène et piles à combustible',        'en': 'Hydrogen and fuel cells'},
    'grids':      {'color': '#2f9a5b', 'fr': 'Réseaux et énergies renouvelables',       'en': 'Grids and renewable energy'},
    'residential':{'color': '#9e4a08', 'fr': 'Bâtiment et efficacité résidentielle',    'en': 'Buildings and residential efficiency'},
    'flexibility':{'color': '#b5246b', 'fr': 'Flexibilité, marchés et communautés',     'en': 'Flexibility, markets and communities'},
    'mobility':   {'color': '#7a45d8', 'fr': 'Mobilité électrique et véhicules',        'en': 'Electric mobility and vehicles'},
    'methods':    {'color': '#5a6b7d', 'fr': 'Méthodes transversales',                  'en': 'Cross-cutting methods'},
}

# (id, domain, fr, en, include-pattern, exclude-pattern or None)
TOPICS = [
    # — Hydrogène et piles à combustible ————————————————————————————————
    ('fuelcell', 'hydrogen', 'Piles à combustible', 'Fuel cells',
     r'fuel[ -]?cells?\b|pemfc|pem[ -]fc\b', None),
    ('pem', 'hydrogen', 'Membrane échangeuse de protons', 'Proton exchange membrane',
     r'proton exchange membrane|pemfc|pem fuel cell|pem-fc|polymer membrane|membrane fuel cell', None),
    ('multistack', 'hydrogen', 'Systèmes multi-piles', 'Multi-stack systems',
     r'multi[- ]?stack|modular fuel cell|multi-source|multisources?', None),
    ('hydrogen', 'hydrogen', 'Hydrogène', 'Hydrogen',
     r'hydrogen', None),
    ('electrolysis', 'hydrogen', 'Électrolyse', 'Electrolysis',
     r'electroly', None),
    ('genset', 'hydrogen', 'Génératrice à hydrogène', 'Hydrogen genset',
     r'genset|range extend|range extension|gasoline generator|bi-fuel|hydrogen.gasoline', None),
    ('coldstart', 'hydrogen', 'Démarrage à froid', 'Cold start',
     r'cold start|startup|start-?up|freezing|low temperature start', None),
    ('degradation', 'hydrogen', 'Dégradation et durée de vie', 'Degradation and lifetime',
     r'degradation|degrading|age?ing\b|lifetime|remaining useful life|durabilit|life ?cycle|life preservation|loss of life|replacement', None),
    ('watergas', 'hydrogen', "Gestion de l'eau et des gaz", 'Water and gas management',
     r'water phenomena|water model|water distribution|water issues|diphasic|flooding|drying\)|air cooling|air supply|gas supply|feeding gas|oxygen', None),

    # — Réseaux et énergies renouvelables ——————————————————————————————
    ('wind', 'grids', 'Énergie éolienne', 'Wind energy',
     r'\bwind\b', None),
    ('dfig', 'grids', 'Génératrice asynchrone à double alimentation', 'Doubly-fed induction generator',
     r'doubly[- ]fed|\bdfig\b|induction (wind )?generator|synchronous generator|asynchronous machine', None),
    ('pv', 'grids', 'Photovoltaïque', 'Photovoltaic',
     r'photovoltaic|\bpv\b|solar', None),
    ('mppt', 'grids', 'Poursuite du point de puissance maximale', 'Maximum power point tracking',
     r'\bmppt\b|maximum power point|power maximization|power extraction maximization|maximum efficiency', None),
    ('standalone', 'grids', 'Systèmes autonomes', 'Stand-alone systems',
     r'stand[- ]?alone|standalone|autonomous operation|off[- ]grid|remote applications|isolated ac|autonomous (ac )?microgrid', None),
    ('microgrid', 'grids', 'Micro-réseaux', 'Microgrids',
     r'micro[- ]?grids?\b', None),
    ('dg', 'grids', 'Production décentralisée', 'Distributed generation',
     r'distributed (generat|energy resources|network protocol)|\bder\b|distribution (network|grid|transformer|level)|utility[- ]interconnect|grid[- ]connected|grid interactive|interconnected|transmission network', None),
    ('islanding', 'grids', "Détection d'îlotage", 'Islanding detection',
     r'islanding', None),
    ('inverter', 'grids', 'Onduleurs et convertisseurs', 'Inverters and converters',
     r'inverters?\b|converters?\b|\bvsi\b|multilevel|h-bridge|igbt|mosfet|buck|boost|amplifier|electric springs|power interface|power electronics', None),
    ('powerquality', 'grids', "Qualité de l'onde et synchronisation", 'Power quality and synchronisation',
     r'power quality|voltage (unbalance|variation|degradation|positive feedback|source)|unbalanced|synchroni[sz]|frequency locked loop|\bfll\b|adaline|transient (event|air|behavior)|power analysis|reactive power|power transfer|load commutation|load transients', None),
    ('realtime', 'grids', 'Temps réel et FPGA', 'Real-time and FPGA',
     r'\bfpga\b|real[- ]?time|hardware (implementation|solution)|emulation|\bvhdl\b|test bench', None),

    # — Bâtiment et efficacité résidentielle ————————————————————————————
    ('hems', 'residential', 'Résidentiel et maisons intelligentes', 'Residential and smart homes',
     r'home energy management|smart home|\bhems\b|household|residential', None),
    ('building', 'residential', 'Bâtiments', 'Buildings',
     r'building', None),
    ('heating', 'residential', 'Chauffage et charges thermiques', 'Heating and thermal loads',
     r'heating|heaters?\b|baseboard|thermostatic|\bhvac\b|space heat|heat load|thermal (model|parameters|behavior)', None),
    ('ets', 'residential', 'Stockage thermique électrique', 'Electric thermal storage',
     r'thermal storage', None),
    ('occupancy', 'residential', 'Occupation des lieux', 'Occupancy',
     r'occupanc|occupant', None),
    ('nilm', 'residential', 'Suivi non intrusif des charges', 'Non-intrusive load monitoring',
     r'non[- ]?intrusive|\bnilm\b|load monitoring|disaggregation|appliance|refrigerator|anomaly detection', None),
    ('forecasting', 'residential', 'Prévision de la demande', 'Load forecasting',
     r'forecast|anticipat|\bprevision\b|predict', None),
    ('loadmodel', 'residential', 'Modélisation des charges', 'Load modelling',
     r'load model|zip model|residual (load|components)|admittance|two-state loads|active power load|electricity demand|energy consumption|consumer', None),
    ('metering', 'residential', 'Mesure et jeux de données', 'Metering and datasets',
     r'dataset|sub-?metering|data management|energy monitoring|measurement|ambient display', None),

    # — Flexibilité, marchés et communautés ————————————————————————————
    ('transactive', 'flexibility', 'Énergie transactive', 'Transactive energy',
     r'transactive', None),
    ('markets', 'flexibility', 'Marchés de flexibilité', 'Flexibility markets',
     r'flexibility (spot )?market|spot market|local (forward|flexibility) market|market[- ]clearing|forward market|retail market|\bbids?\b|bid execution|energy allocation', None),
    ('dr', 'flexibility', 'Réponse à la demande', 'Demand response',
     r'demand response|demand aggregation|load aggregator|peak shaving|peak-to-average|off-peak|flexible load|energy reduction|flexibility potential', None),
    ('pricing', 'flexibility', 'Tarification et mécanismes incitatifs', 'Pricing and incentives',
     r'pricing|price-based|time-of-use|cost-sharing|cost mapping|penalty mechanism|incentive|discount|economic|fuel cost|low-cost', None),
    ('community', 'flexibility', 'Communautés énergétiques', 'Energy communities',
     r'energy communit|neighbo|communit', None),
    ('coordination', 'flexibility', 'Coordination distribuée', 'Distributed coordination',
     r'coordinat|consensus|\badmm\b|multi[- ]agent|aggregator|sharing[- ]based|load sharing|bi-level|hierarchical', None),
    ('greenhouse', 'flexibility', 'Serres et agriculture', 'Greenhouses and agriculture',
     r'greenhouse|agricultur|cultivation|maize|water pumping', None),

    # — Mobilité électrique et véhicules ————————————————————————————————
    ('ev', 'mobility', 'Véhicules électriques', 'Electric vehicles',
     r'electric vehicle|\bevs?\b|electric mobility|plug-?in|\bphev\b|electric.*vehicle', None),
    ('hev', 'mobility', 'Véhicules hybrides', 'Hybrid electric vehicles',
     r'hybrid electric vehicle|\bhev\b|\bphev\b|hybrid vehicle|fc-phev|hybrid source|hybrid power system', None),
    ('battery', 'mobility', 'Batteries', 'Batteries',
     r'batter|lead acid|\bsoc\b|\bsoh\b|state of charge', None),
    ('charging', 'mobility', 'Recharge des véhicules', 'Vehicle charging',
     r'charging|charge scheduling|charge-sustaining', None),
    ('autonomous', 'mobility', 'Véhicules autonomes et guidés', 'Autonomous and self-guided vehicles',
     r'self[- ]guided|autonomous driving|self driving|automated guided|\bagv\b|navigation|trajectory|path planning|obstacle|perception|lane departure|intelligent (vehicle|ground|vision)|ground vehicle|material handling|order picking|localization|sensor fusion|object detection|image fusion|manufacturing environment|industry 4', None),
    ('winter', 'mobility', 'Conditions hivernales', 'Winter conditions',
     r'winter|cold (weather|climate)|nordic', None),
    ('dynamics', 'mobility', 'Dynamique et rendement du véhicule', 'Vehicle dynamics and efficiency',
     r'rolling resistance|aerodynamic|regenerative braking|driving (style|speed)|mass estimation|grade estimation|road trip|speed control|long-trip|energy efficient (path|routing|order)|autonomy extension', None),

    # — Méthodes transversales ————————————————————————————————————————
    # Reinforcement learning was its own topic at four publications — a dot on
    # the edge of the map. It is machine learning, and the merged node carries
    # the lab's recent multi-agent work rather than hiding it in the margin.
    ('ml', 'methods', 'Apprentissage automatique', 'Machine learning',
     r'machine learning|deep learning|reinforcement learning|learning[- ]based|markovian|based (architectures|learning)', None),
    ('nn', 'methods', 'Réseaux de neurones', 'Neural networks',
     r'neur(al|onal) network|\bann\b|neuro-fuzzy|attention transfer|backpropagation', None),
    ('fuzzy', 'methods', 'Logique floue', 'Fuzzy logic',
     r'fuzzy', None),
    ('optimization', 'methods', 'Optimisation', 'Optimisation',
     r'optimi[sz]|optimal\b|meta-?heuristic|genetic algorithm|\bgwo\b|convex|linear quadratic|dynamic programming|sizing|shrinked-space|shapley', None),
    ('uncertainty', 'methods', 'Incertitude et approches stochastiques', 'Uncertainty and stochastic methods',
     r'stochastic|uncertaint|probabilistic|chance constrained|\brisk\b|gaussian process|non-parametric|sensitivity analysis|density estimation', None),
    ('identification', 'methods', 'Identification et estimation', 'Identification and estimation',
     r'(parameters?|system|online|nonlinear model) identification|parameters? (estimation|identification)|estimation of|kalman|estimation method|characteri[sz]ation|characteristics|state model|semi-empirical', None),
    ('control', 'methods', 'Commande et contrôle', 'Control',
     r'\bcontrol\b|controller|droop|\bpid\b|super-twisting|field orientation|hysteresis current', None),
    # Deliberately narrower than "any title containing the word model": that
    # matched 60 publications and made a hub that said nothing. This is the
    # simulation work proper.
    ('simulation', 'methods', 'Modélisation et simulation', 'Modelling and simulation',
     r'co-?simulation|simulink|matlab|\bsimulation|simulator|petri net|numerical investigation|macroscopic (model|representation)|analytical model|multi-physics|physics model|3d stack|pseudo.2d|pseudo-two-dimensional', None),
    ('clustering', 'methods', 'Classification et regroupement', 'Clustering and classification',
     r'clustering|k-means|classification|recommender system|principal component|wavelet', None),
    ('review', 'methods', 'Revues et synthèses', 'Reviews and surveys',
     r'\breview\b|survey|state of the art|literature review|comprehensive (review|cost mapping)|overview', None),
    ('platforms', 'methods', 'Plateformes et architectures logicielles', 'Software platforms and architectures',
     r'software (architecture|development)|open platform|kubernetes|architecture|framework|platform|\bdnp3\b|ethernet|connectivity|interface design|deploying', None),
    ('instrumentation', 'methods', 'Instrumentation et capteurs', 'Instrumentation and sensing',
     r'sensors?\b|piezoelectric|ultrasonic|transducer|permittivity|electromagnetic field|\bprobe\b|cavitation|e-field|toxic|applicator', None),
]

# Map labels. The full names above are what the tooltip and the legend say; on
# the map itself a shorter form fits beside the disc. Only topics needing one
# are listed — the rest use their full name unchanged.
SHORT = {
    'pem':             ('Membrane PEM', 'PEM membrane'),
    'multistack':      ('Multi-piles', 'Multi-stack'),
    'genset':          ('Génératrice H₂', 'H₂ genset'),
    'degradation':     ('Dégradation', 'Degradation'),
    'watergas':        ('Eau et gaz', 'Water and gas'),
    'wind':            ('Éolien', 'Wind'),
    'dfig':            ('DFIG', 'DFIG'),
    'mppt':            ('MPPT', 'MPPT'),
    'standalone':      ('Systèmes autonomes', 'Stand-alone'),
    'dg':              ('Production décentralisée', 'Distributed generation'),
    'islanding':       ('Îlotage', 'Islanding'),
    'inverter':        ('Onduleurs', 'Inverters'),
    'powerquality':    ("Qualité de l'onde", 'Power quality'),
    'realtime':        ('Temps réel / FPGA', 'Real-time / FPGA'),
    'hems':            ('Résidentiel', 'Residential'),
    'heating':         ('Chauffage', 'Heating'),
    'ets':             ('Stockage thermique', 'Thermal storage'),
    'occupancy':       ('Occupation', 'Occupancy'),
    'nilm':            ('NILM', 'NILM'),
    'forecasting':     ('Prévision', 'Forecasting'),
    'loadmodel':       ('Modélisation des charges', 'Load modelling'),
    'metering':        ('Mesure et données', 'Metering and data'),
    'markets':         ('Marchés de flexibilité', 'Flexibility markets'),
    'pricing':         ('Tarification', 'Pricing'),
    'community':       ('Communautés', 'Communities'),
    'greenhouse':      ('Serres', 'Greenhouses'),
    'hev':             ('Véhicules hybrides', 'Hybrid vehicles'),
    'charging':        ('Recharge', 'Charging'),
    'autonomous':      ('Véhicules autonomes', 'Autonomous vehicles'),
    'dynamics':        ('Dynamique du véhicule', 'Vehicle dynamics'),
    'nn':              ('Réseaux de neurones', 'Neural networks'),
    'uncertainty':     ('Incertitude', 'Uncertainty'),
    'identification':  ('Identification', 'Identification'),
    'control':         ('Commande', 'Control'),
    'simulation':      ('Simulation', 'Simulation'),
    'clustering':      ('Classification', 'Clustering'),
    'review':          ('Revues', 'Reviews'),
    'platforms':       ('Plateformes logicielles', 'Software platforms'),
}

MIN_PUBS = 4      # a topic below this is noise on the map
MIN_EDGE = 3      # two topics meeting twice is coincidence, not a relationship
TOP_LINKS = 4     # strongest links kept per topic, so the map is not a hairball

WIDTH, HEIGHT = 1000, 660
R_MIN, R_MAX = 5.0, 23.0


def norm(text: str) -> str:
    """Lowercase, strip accents — the patterns are written against this form."""
    stripped = ''.join(c for c in unicodedata.normalize('NFD', text)
                       if unicodedata.category(c) != 'Mn')
    return stripped.lower()


def load_publications():
    pubs = []
    for path in sorted(glob.glob(str(ROOT / 'src/content/publications/*.json'))):
        data = json.load(open(path, encoding='utf-8'))
        pubs.append({
            'id': Path(path).stem,
            'title': data['title'],
            'year': data['year'],
            'type': data['type'],
            'norm': norm(data['title']),
        })
    return sorted(pubs, key=lambda p: (-p['year'], p['title']))


def assign(pubs):
    """Tag every publication with the topics whose patterns its title matches."""
    compiled = [(tid, dom, fr, en, re.compile(inc),
                 re.compile(exc) if exc else None)
                for tid, dom, fr, en, inc, exc in TOPICS]
    for pub in pubs:
        pub['topics'] = [
            tid for tid, _, _, _, inc, exc in compiled
            if inc.search(pub['norm']) and not (exc and exc.search(pub['norm']))
        ]
    return pubs


def audit(pubs):
    counts = {}
    for pub in pubs:
        for tid in pub['topics']:
            counts[tid] = counts.get(tid, 0) + 1

    by_domain = {}
    for tid, dom, fr, _, _, _ in TOPICS:
        by_domain.setdefault(dom, []).append((counts.get(tid, 0), tid, fr))

    print(f"{len(pubs)} publications · {len(TOPICS)} sujets définis\n")
    for dom, rows in by_domain.items():
        print(f"— {DOMAINS[dom]['fr']}")
        for n, tid, fr in sorted(rows, reverse=True):
            mark = '  ' if n >= MIN_PUBS else '✗ '
            print(f"  {mark}{n:>3}  {tid:<16} {fr}")
        print()

    orphans = [p for p in pubs if not p['topics']]
    print(f"Publications sans aucun sujet : {len(orphans)}")
    for pub in orphans:
        print(f"   {pub['year']}  {pub['title'][:92]}")

    spread = [len(p['topics']) for p in pubs]
    print(f"\nSujets par publication : moyenne {sum(spread)/len(spread):.1f}, "
          f"max {max(spread)}")


def build_graph(pubs):
    """Nodes with their weight, edges with raw co-occurrence and normalised strength."""
    keep = [t for t in TOPICS
            if sum(t[0] in p['topics'] for p in pubs) >= MIN_PUBS]
    index = {t[0]: i for i, t in enumerate(keep)}

    nodes = [{'id': tid, 'domain': dom, 'fr': fr, 'en': en,
              'shortFr': SHORT.get(tid, (fr, en))[0],
              'shortEn': SHORT.get(tid, (fr, en))[1], 'n': 0}
             for tid, dom, fr, en, _, _ in keep]

    co = {}
    for pub in pubs:
        present = sorted(index[t] for t in pub['topics'] if t in index)
        for i in present:
            nodes[i]['n'] += 1
        for a in range(len(present)):
            for b in range(a + 1, len(present)):
                key = (present[a], present[b])
                co[key] = co.get(key, 0) + 1

    # Association strength, the normalisation VOSviewer uses: it asks whether two
    # topics meet more often than their individual frequencies would predict, so
    # a large node cannot look related to everything simply by being large.
    total = len(pubs)
    every = [(i, j, c, c * total / (nodes[i]['n'] * nodes[j]['n']))
             for (i, j), c in co.items() if c >= 2]

    # Keep each topic's strongest links rather than every link above the floor:
    # the floor alone leaves a hairball in which no structure is visible.
    best = {}
    for edge in every:
        if edge[2] >= MIN_EDGE:
            best.setdefault(edge[0], []).append(edge)
            best.setdefault(edge[1], []).append(edge)
    kept = set()
    for node_links in best.values():
        for edge in sorted(node_links, key=lambda e: -e[3])[:TOP_LINKS]:
            kept.add(edge)

    # A topic whose every link fell under the floor keeps its single strongest
    # one anyway. Otherwise the force layout has nothing to hold it and flings
    # it into a corner, where it reads as an error rather than as a small topic.
    attached = {i for edge in kept for i in edge[:2]}
    for i in range(len(nodes)):
        if i in attached:
            continue
        mine = [e for e in every if i in e[:2]]
        if mine:
            kept.add(max(mine, key=lambda e: e[3]))

    return nodes, sorted(kept, key=lambda e: e[0])


def layout(nodes, edges, iterations=700):
    """Seeded Fruchterman–Reingold. No randomness, so the map is reproducible."""
    n = len(nodes)
    k = math.sqrt(WIDTH * HEIGHT / n)
    # Deterministic start: a circle, spiralled slightly so no two nodes coincide.
    pos = [[WIDTH / 2 + (0.4 * WIDTH) * math.cos(2 * math.pi * i / n) * (0.6 + 0.4 * ((i * 7) % n) / n),
            HEIGHT / 2 + (0.4 * HEIGHT) * math.sin(2 * math.pi * i / n) * (0.6 + 0.4 * ((i * 7) % n) / n)]
           for i in range(n)]

    top = max(s for _, _, _, s in edges)
    pull = [(i, j, 0.25 + 1.35 * (s / top)) for i, j, _, s in edges]
    temp = WIDTH / 8

    for step in range(iterations):
        disp = [[0.0, 0.0] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
                d = max(math.hypot(dx, dy), 0.01)
                f = k * k / d
                ux, uy = dx / d * f, dy / d * f
                disp[i][0] += ux; disp[i][1] += uy
                disp[j][0] -= ux; disp[j][1] -= uy
        for i, j, w in pull:
            dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
            d = max(math.hypot(dx, dy), 0.01)
            f = d * d / k * w
            ux, uy = dx / d * f, dy / d * f
            disp[i][0] -= ux; disp[i][1] -= uy
            disp[j][0] += ux; disp[j][1] += uy
        for i in range(n):
            # A weak pull to the centre; without it, weakly linked topics drift
            # off and the map is mostly empty space. It pulls harder vertically
            # than horizontally so the cloud comes out landscape — a portrait
            # graph wastes half the width of a page and forces a tall scroll.
            disp[i][0] -= (pos[i][0] - WIDTH / 2) * 0.0006 * k
            disp[i][1] -= (pos[i][1] - HEIGHT / 2) * 0.0034 * k
            d = max(math.hypot(*disp[i]), 0.01)
            pos[i][0] += disp[i][0] / d * min(d, temp)
            pos[i][1] += disp[i][1] / d * min(d, temp)
        temp = max(temp * 0.985, 0.6)

    return pos


def radii(nodes):
    lo, hi = min(x['n'] for x in nodes), max(x['n'] for x in nodes)
    return [R_MIN + (R_MAX - R_MIN) * math.sqrt((x['n'] - lo) / (hi - lo))
            for x in nodes]


def fit(pos, rad, pad=8):
    """Rescale to the viewBox, leaving room for each disc and its label."""
    xs = [p[0] for p in pos]; ys = [p[1] for p in pos]
    span_x = max(max(xs) - min(xs), 1); span_y = max(max(ys) - min(ys), 1)
    scale = min((WIDTH - 2 * (R_MAX + pad)) / span_x,
                (HEIGHT - 2 * (R_MAX + pad + 14)) / span_y)
    ox = (WIDTH - span_x * scale) / 2 - min(xs) * scale
    oy = (HEIGHT - span_y * scale) / 2 - min(ys) * scale
    return [[p[0] * scale + ox, p[1] * scale + oy] for p in pos]


def separate(pos, rad, rounds=600):
    """Push overlapping discs apart and keep them in frame.

    This runs *after* the rescale, not before: scaling the layout down would
    otherwise undo the separation and hand back the overlaps it just removed.
    """
    for _ in range(rounds):
        moved = False
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                gap = rad[i] + rad[j] + 10
                dx, dy = pos[j][0] - pos[i][0], pos[j][1] - pos[i][1]
                d = math.hypot(dx, dy)
                if d == 0:
                    dx, dy, d = 0.7, 0.7, 1.0
                if d < gap:
                    push = (gap - d) / 2
                    ux, uy = dx / d * push, dy / d * push
                    pos[i][0] -= ux; pos[i][1] -= uy
                    pos[j][0] += ux; pos[j][1] += uy
                    moved = True
        for i, (x, y) in enumerate(pos):
            pos[i][0] = min(max(x, rad[i] + 4), WIDTH - rad[i] - 4)
            pos[i][1] = min(max(y, rad[i] + 4), HEIGHT - rad[i] - 16)
        if not moved:
            break
    return [[round(x, 1), round(y, 1)] for x, y in pos]


# Where a label may sit relative to its disc, in order of preference. The
# browser recomputes the same four positions when the discs resize, so the
# offsets live in one place conceptually even though they are applied twice.
SIDES = ('below', 'above', 'right', 'left')


def label_box(side, cx, cy, r, w, h):
    if side == 'below':
        return cx - w / 2, cy + r + 2
    if side == 'above':
        return cx - w / 2, cy - r - 2 - h
    if side == 'right':
        return cx + r + 4, cy - h / 2
    return cx - r - 4 - w, cy - h / 2


def place_labels(nodes, pos, rad):
    """Greedy, largest first: a label is drawn only where it does not collide.

    Four positions are tried around each disc before giving up. Whatever is left
    over appears on hover or focus — fifty-odd labels cannot all be legible at
    once, and a map of overlapping text is worse than one that admits it.
    Placement uses the longer of the two languages so both render identically,
    and every disc is an obstacle: a label over a circle is as unreadable as a
    label over another label.
    """
    placed = [None] * len(nodes)
    boxes = [(p[0] - r, p[1] - r, 2 * r, 2 * r) for p, r in zip(pos, rad)]
    for i in sorted(range(len(nodes)), key=lambda i: -nodes[i]['n']):
        chars = max(len(nodes[i]['shortFr']), len(nodes[i]['shortEn']))
        w, h = chars * 5.7 + 4, 13
        for side in SIDES:
            x, y = label_box(side, pos[i][0], pos[i][1], rad[i], w, h)
            # Generous bounds rather than the canvas edge: the viewBox is cropped
            # to the drawing afterwards, so a label may sit outside the nominal
            # frame and still be in the picture.
            if not (-170 < x and x + w < WIDTH + 170 and -50 < y and y + h < HEIGHT + 50):
                continue
            if any(x < bx + bw and bx < x + w and y < by + bh and by < y + h
                   for bx, by, bw, bh in boxes):
                continue
            # Judged at the point where the label meets its disc, not at the
            # label's centre: a long name's centre is far from its own node by
            # construction, which would reject perfectly readable placements.
            anchor = {'below': (pos[i][0], y), 'above': (pos[i][0], y + h),
                      'right': (x, pos[i][1]), 'left': (x + w, pos[i][1])}[side]
            mine = math.dist(anchor, pos[i])
            if any(math.dist(anchor, pos[j]) < mine
                   for j in range(len(nodes)) if j != i):
                continue
            boxes.append((x, y, w, h))
            placed[i] = side
            break
    return placed, boxes


def crop(boxes, pad=8):
    """The viewBox that exactly contains the drawing, so no margin is dead space."""
    x0 = min(b[0] for b in boxes) - pad
    y0 = min(b[1] for b in boxes) - pad
    x1 = max(b[0] + b[2] for b in boxes) + pad
    y1 = max(b[1] + b[3] for b in boxes) + pad
    return [round(x0, 1), round(y0, 1), round(x1 - x0, 1), round(y1 - y0, 1)]


def emit(pubs, nodes, edges, pos, rad, show, view):
    ids = [x['id'] for x in nodes]
    return {
        'domains': DOMAINS,
        'view': view,
        'nodes': [{'id': x['id'], 'domain': x['domain'], 'fr': x['fr'], 'en': x['en'],
                   'shortFr': x['shortFr'], 'shortEn': x['shortEn'], 'n': x['n'],
                   'x': p[0], 'y': p[1], 'r': round(r, 1), 'side': side}
                  for x, p, r, side in zip(nodes, pos, rad, show)],
        'edges': [{'s': i, 't': j, 'w': c} for i, j, c, _ in edges],
        # Per-publication topics drive the year filter and let a click on a
        # topic filter the catalogue printed below the map.
        'pubs': {p['id']: {'y': p['year'],
                           't': sorted(ids.index(t) for t in p['topics'] if t in ids)}
                 for p in pubs if any(t in ids for t in p['topics'])},
        'years': [min(p['year'] for p in pubs), max(p['year'] for p in pubs)],
    }


if __name__ == '__main__':
    publications = assign(load_publications())
    if '--audit' in sys.argv:
        audit(publications)
        sys.exit(0)

    nodes, edges = build_graph(publications)
    rad = radii(nodes)
    pos = separate(fit(layout(nodes, edges), rad), rad)
    sides, boxes = place_labels(nodes, pos, rad)
    data = emit(publications, nodes, edges, pos, rad, sides, crop(boxes))

    out = ROOT / 'src/data/topics.json'
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')),
                   encoding='utf-8')
    print(f"{out.relative_to(ROOT)} — {len(nodes)} sujets, {len(edges)} liens, "
          f"{sum(n['side'] is not None for n in data['nodes'])}/{len(nodes)} étiquettes "
          f"placées, {out.stat().st_size // 1024} Ko")
