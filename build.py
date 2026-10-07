"""Builds the EU5 formable countries overview.

Outputs:
  formables.html          standalone page with every language embedded (open locally)
  site/index.html         page for publishing, loads site/data/<lang>.json on demand
"""
import colorsys
import glob
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from pdx import parse, get, get_all, load_loc, clean

HERE = os.path.dirname(os.path.abspath(__file__))
# Path to the game's "game" folder; override with the EU5_GAME environment variable.
G = os.environ.get("EU5_GAME", "E:/SteamLibrary/steamapps/common/Europa Universalis V/game").rstrip("/\\") + "/"
LANGS = ["english", "russian", "german", "french", "spanish", "braz_por", "polish", "turkish",
         "japanese", "korean", "simp_chinese"]
VERSION = "1.4"

# ================================================================ phrases
# Only the connecting phrases are ours; every game term comes from the game's localization.
# Russian is used for the Russian build, English for every other language.
EN = {
    "Любое из:": "Any of:", "Все из:": "All of:", "НЕ выполнено:": "Not:", "Ни одно из:": "None of:",
    "Если": "If", "Иначе, если": "Else if", "условие:": "condition:", "то требуется:": "then requires:",
    "то:": "then:", "Иначе требуется:": "Otherwise requires:", "Иначе:": "Otherwise:", "Условие:": "Condition:",
    "Всегда": "Always", "Никогда (недоступно)": "Never (unavailable)",
    "Основная культура:": "Primary culture:", "Основная культура: {}": "Primary culture: {}",
    "Группа культур: {}": "Culture group: {}",
    "Любая основная, принятая или терпимая культура:": "Any primary, accepted or tolerated culture:",
    "Язык культуры: {}": "Culture language: {}", "Диалект: {}": "Dialect: {}", "Язык двора: {}": "Court language: {}",
    "Религия: {}": "Religion: {}", "Группа религий: {}": "Religion group: {}", "Группа религий НЕ {}": "Religion group is not {}",
    "Владеет локацией: {}": "Owns location: {}", "Страна: {}": "Country: {}",
    "Является страной {}": "Is the country {}", "Не является страной {}": "Is not the country {}",
    "Существует страна {}": "Country exists: {}", "Страна не существует": "Country does not exist",
    "Является или была страной {}": "Is or was the country {}", "Текущая эпоха: {}": "Current age: {}",
    "Эпоха не раньше: {}": "Age is at least: {}", "Есть реформа правления: {}": "Has government reform: {}",
    "Тип правления: {}": "Government type: {}", "Есть привилегия сословия: {}": "Has estate privilege: {}",
    "Изучено развитие: {}": "Has advance: {}", "Является субъектом": "Is a subject", "Не является субъектом": "Is not a subject",
    "Ведёт войну": "Is at war", "Не ведёт войну": "Is not at war", "Идёт гражданская война": "Is in a civil war",
    "Нет гражданской войны": "Is not in a civil war", "Является гегемоном": "Is a hegemon", "Не является гегемоном": "Is not a hegemon",
    "Культура коренных американцев": "Native American culture", "Культура не коренных американцев": "Not a Native American culture",
    "Государство франкократии": "Frankokratia state", "Не государство франкократии": "Not a Frankokratia state",
    "Ранг страны: {}": "Country rank: {}", "Ранг ниже, чем «{}»": "Rank below {}", "Ранг выше, чем «{}»": "Rank above {}",
    "Уровень ранга {} {}": "Rank level {} {}", "Столица:": "Capital:", "Столица: {}": "Capital: {}",
    "Член организации: {}": "Member of organization: {}", "Состоит в организации": "Is in an organization",
    "Не состоит в организации": "Is not in an organization", "Член организации типа: {}": "Member of organization type: {}",
    "Лидер организации: {}": "Leader of organization: {}", "Есть DLC «{}»": "Has DLC: {}", "Есть присутствие в: {}": "Has presence in: {}",
    "Является ядром страны {}": "Is a core of {}", "Ситуация завершилась": "Situation has ended",
    "Ситуация не завершилась": "Situation has not ended", "Активна ситуация: {}": "Situation is active: {}",
    "Сила сословия «{}» {} {}": "{} estate power {} {}", "Есть правитель": "Has a ruler", "Нет правителя": "Has no ruler",
    "Субъект страны {}": "Subject of {}", "В унии со страной {}": "In a union with {}",
    "Только если начали за {}": "Only if you started as {}",
    "Объединённая группа включает культуру {}": "Merged culture group includes {}",
    "Есть переменная «{}» (событие/решение)": "Has variable “{}” (event/decision)", "Год {} {}": "Year {} {}",
    "Существует: {}": "Exists: {}", "Регион: {}": "Region: {}",
    "НЕ ": "NOT ", "да": "yes", "нет": "no",
    "Скрытые эффекты:": "Hidden effects:", "Ранг страны становится: {}": "Country rank becomes: {}",
    "Открывает реформу правления: {}": "Unlocks government reform: {}", "Добавляет реформу: {}": "Adds reform: {}",
    "Убирает реформу: {}": "Removes reform: {}", "Меняет тип правления на: {}": "Changes government type to: {}",
    "Открывает политику: {}": "Unlocks policy: {}", "Открывает повод к войне: {}": "Unlocks casus belli: {}",
    "Изучает развитие: {}": "Researches advance: {}", "Модификатор «{}»": "Modifier: {}", " на {} лет": " for {} years",
    "Столица переносится в {}": "Capital moves to {}", "Предлагает перенести столицу в {}": "Offers to move the capital to {}",
    "Меняет цвет страны на карте": "Changes the map color", "Добавляет ядро: {}": "Adds core: {}",
    "Переименовывает локацию": "Renames a location", "Событие: {}": "Event: {}", "Событие {}": "Event {}",
    "Распускает международную организацию {}": "Dissolves the international organization {}",
    "Выходит из международной организации": "Leaves an international organization",
    "Меняет уровень интеграции локаций": "Changes the integration level of locations",
    "Сдвигает общественную ценность: {}": "Shifts societal value: {}",
    "Только событием": "Event only", "диалект": "dialect", "Стабильность": "Stability", "Сила правительства": "Government power",
    "Легитимность": "Legitimacy", "Престиж": "Prestige",
    "Отряд": "Unit", "Здание": "Building", "Ополчение": "Levy", "Закон": "Law", "Городское право": "Town right",
    "Реформа правления": "Government reform", "Действие кабинета": "Cabinet action", "Способ производства": "Production method",
    "Привилегия сословия": "Estate privilege", "Политика": "Policy", "Тип субъекта": "Subject type",
    "Рыцарский орден": "Chivalric order", "Наследование": "Heir selection", "Повод к войне": "Casus belli",
    "Тип дорог": "Road type", "Дипломатия": "Diplomacy", "Способность": "Ability", "Взаимодействие": "Interaction",
    "в локации": "in the location", "Континенты": "Continents", "Субконтиненты": "Subcontinents", "Регионы": "Regions", "Области": "Areas",
    "Провинции": "Provinces", "Локации": "Locations",
}

LANG = "russian"
loc = {}
loc_en = {}


def T(template, *args):
    tpl = template if LANG == "russian" else EN.get(template, template)
    return tpl.format(*args) if args else tpl


def L(key, fallback=None):
    v = loc.get(key) or loc_en.get(key)
    return clean(v, loc) if v else (fallback if fallback is not None else key)


def adj(key, lang_word=False):
    """Russian and Polish store culture/language names as adjective stems ("Шведск", "Szwedz")."""
    s = L(key).rstrip(".")
    if LANG == "russian" and re.search(r"[кнгхцвлмрстдпбз]$", s):
        return s + ("ий" if lang_word else "ая")
    if LANG == "polish" and re.search(r"(s|z|c|k)$", s) and not s.endswith("ska"):
        return s + ("ki" if lang_word else "ka")
    return s


# ================================================================ game data (language independent)
def P(path):
    return parse(open(path, encoding="utf-8-sig").read())


defs = P(G + "in_game/map_data/definitions.txt")
dmap = P(G + "in_game/map_data/default.map")
excluded = set()
# The game counts non_ownable land in a formable's total (Egypt: 82 + 19 = 101, 75% = 76), so only water and
# impassable mountains are left out.
for key in ("sea_zones", "lakes", "impassable_mountains"):
    for blk in get_all(dmap, key):
        excluded |= {v for k, _, v in blk if k is None and isinstance(v, str)}

members, level_of = {}, {}
LEVELS = ["continent", "sub_continent", "region", "area", "province"]


geo_parent, geo_children, loc_parent = {}, {}, {}


def walk(block, depth, parent=None):
    acc = set()
    for k, _, v in block:
        if k is None:
            if isinstance(v, str):
                loc_parent[v] = parent
            if isinstance(v, str) and v not in excluded:
                acc.add(v)
            continue
        if isinstance(v, list):
            s = walk(v, depth + 1, k)
            members[k] = s
            level_of[k] = LEVELS[min(depth, 4)]
            geo_parent[k] = parent
            if parent:
                geo_children.setdefault(parent, []).append(k)
            acc |= s
    return acc


walk(defs, 0)
loc_continent = {l: name for name, lv in level_of.items() if lv == "continent" for l in members[name]}

named_colors = {}
for f in glob.glob(G + "main_menu/common/named_colors/*.txt"):
    for _, _, v in P(f):
        if isinstance(v, list):
            for k, _, c in v:
                if k and isinstance(c, tuple):
                    named_colors[k] = c


def to_hex(c):
    if not isinstance(c, tuple):
        return None
    kind, vals = c
    nums = [float(x) for _, _, x in vals if isinstance(x, str)][:3]
    if len(nums) < 3:
        return None
    if kind == "rgb":
        r, g, b = [n / 255 if max(nums) > 1 else n for n in nums]
    elif kind == "hsv360":
        r, g, b = colorsys.hsv_to_rgb(nums[0] / 360, nums[1] / 100, nums[2] / 100)
    else:
        r, g, b = colorsys.hsv_to_rgb(*nums)
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(x * 255))) for x in (r, g, b))


mod_types = {}
for f in glob.glob(G + "main_menu/common/modifier_type_definitions/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            mod_types[k] = {kk: vv for kk, _, vv in v if isinstance(vv, str)}

static_mods = {}
for f in glob.glob(G + "main_menu/common/static_modifiers/*.txt") + glob.glob(G + "in_game/common/static_modifiers/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            static_mods[k] = [(kk, vv) for kk, _, vv in v if kk and kk != "game_data" and isinstance(vv, str)]

script_values = {}
for f in glob.glob(G + "in_game/common/script_values/*.txt") + glob.glob(G + "main_menu/common/script_values/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, str) and re.fullmatch(r"-?\d+(\.\d+)?", v):
            script_values[k] = float(v)

rank_src = [(k, v) for k, _, v in P(G + "in_game/common/country_ranks/00_default.txt") if k and isinstance(v, list)]
rank_level = {k: int(get(v, "level", "1")) for k, v in rank_src}

UNLOCKS = {
    "unlock_unit": "Отряд", "unlock_building": "Здание", "unlock_levy": "Ополчение", "unlock_law": "Закон",
    "unlock_town_rights": "Городское право", "unlock_government_reform": "Реформа правления",
    "unlock_cabinet_action": "Действие кабинета", "unlock_production_method": "Способ производства",
    "unlock_estate_privilege": "Привилегия сословия", "unlock_policy": "Политика", "unlock_subject_type": "Тип субъекта",
    "unlock_chivalric_order": "Рыцарский орден", "unlock_heir_selection": "Наследование", "unlock_casus_belli": "Повод к войне",
    "unlock_road_type": "Тип дорог", "unlock_diplomacy": "Дипломатия", "unlock_ability": "Способность",
    "unlock_interaction": "Взаимодействие", "unlock_country_interaction": "Взаимодействие",
}
TAG_RE = re.compile(r"^(has_or_had_tag|tag)$")


def tags_in(block):
    found = set()
    for k, _, v in block:
        if k and TAG_RE.match(k) and isinstance(v, str):
            found.add(v)
        elif k in ("OR", "AND") and isinstance(v, list):
            found |= tags_in(v)
    return found


# Country-specific government reforms ("state principles"): reforms whose potential names a tag.
reform_src = {}  # tag -> [(id, block)]
for f in glob.glob(G + "in_game/common/government_reforms/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            for tg in tags_in(get(v, "potential") or []):
                reform_src.setdefault(tg, []).append((k, v))


def _unlock_targets(block, out):
    """Collect reform ids unlocked anywhere inside a block."""
    for k, _, v in block:
        if k == "unlock_government_reform_effect" and isinstance(v, list):
            t = get(v, "type")
            if t:
                out.add(t)
        elif k == "unlock_government_reform" and isinstance(v, str):
            out.add(v)
        elif isinstance(v, list):
            _unlock_targets(v, out)


reform_unlockers = {}  # reform id -> [("decision"|"advance"|"formable"|"event", key)]
for kind, pattern in (("decision", "in_game/common/decisions/*.txt"), ("advance", "in_game/common/advances/*.txt"),
                      ("event", "in_game/events/**/*.txt")):
    for f in glob.glob(G + pattern, recursive=True):
        try:
            blocks = P(f)
        except Exception:
            continue
        for k, _, v in blocks:
            if k and isinstance(v, list):
                found = set()
                _unlock_targets(v, found)
                for r in found:
                    reform_unlockers.setdefault(r, []).append((kind, k))

# What unlockable things give, so "Unlocks: X" can show X's modifiers.
town_right_defs = {}
for f in glob.glob(G + "in_game/common/town_rights/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            town_right_defs[k] = v
levy_defs = {}
for f in glob.glob(G + "in_game/common/levies/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            levy_defs[k] = v
reform_defs = {}
for f in glob.glob(G + "in_game/common/government_reforms/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            reform_defs[k] = v

adv_src = {}  # tag -> [(id, block)]
for f in glob.glob(G + "in_game/common/advances/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            for tg in tags_in(get(v, "potential") or []):
                adv_src.setdefault(tg, []).append((k, v))

# Tags that already exist (own locations) at the 1337 start; they can be formed only once the original is gone.
_setup = get(get(P(G + "main_menu/setup/1337/10_countries.txt"), "countries") or [], "countries") or []
start_tags = {k for k, _, v in _setup if k and isinstance(v, list) and
              any(kk and kk.startswith("own") and isinstance(vv, list) and vv for kk, _, vv in v)}

# What each starting nation looks like in 1337, for the list of nations that can't be formed.
start_setup = {k: v for k, _, v in _setup if k in start_tags}
start_def = {}
for f in glob.glob(G + "in_game/setup/countries/*.txt"):
    for k, _, v in P(f):
        if k in start_tags and isinstance(v, list):
            start_def[k] = {"culture": get(v, "culture_definition"), "religion": get(v, "religion_definition"),
                            "color": get(v, "color")}


def start_locations(v):
    locs = set()
    for kk, _, vv in v:
        if kk and kk.startswith("own") and isinstance(vv, list):
            locs |= {x for _, _, x in vv if isinstance(x, str)}
    return locs


formables = [(fid, b) for fid, _, b in P(G + "in_game/common/formable_countries/00_formable_countries.txt")
             if fid and isinstance(b, list)]

# ---------------------------------------------------------------- territory cards
TERR_KEYS = ("continents", "sub_continents", "regions", "areas", "provinces", "locations")
formable_req = {}
for fid, b in formables:
    req = set()
    for key in TERR_KEYS:
        for _, _, g in (get(b, key) or []):
            if isinstance(g, str):
                req |= members.get(g, {g} if g not in excluded else set())
    formable_req[fid] = req
owner_of = {}
for _t, _v in start_setup.items():
    for _l in start_locations(_v):
        owner_of[_l] = _t
geo_info = {}
for g, lv in level_of.items():
    locs = members.get(g, set())
    if not locs:
        continue
    f = sorted(((fid, len(req & locs)) for fid, req in formable_req.items() if req & locs), key=lambda x: -x[1])
    top = 10 if lv == "province" else 20
    f = f[:top]
    o = Counter(owner_of[l] for l in locs if l in owner_of).most_common(top)
    geo_info[g] = {"lv": lv, "c": len(locs), "par": geo_parent.get(g), "kids": [k for k in geo_children.get(g, []) if k in level_of], "f": f,
                   "o": o, "free": len(locs) - sum(1 for l in locs if l in owner_of)}

# ---------------------------------------------------------------- cultures
culture_info = {}  # culture -> groups, dialect, color
for f in glob.glob(G + "in_game/common/cultures/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            groups = get(v, "culture_groups") or []
            culture_info[k] = {"groups": [x for _, _, x in groups if isinstance(x, str)], "dialect": get(v, "language"),
                               "color": get(v, "color")}
dialect_lang = {}


def _dialects(block, lang):
    for k, _, v in block:
        if k and isinstance(v, list):
            if k.endswith("_dialect"):
                dialect_lang[k] = lang
            _dialects(v, lang)


for f in glob.glob(G + "in_game/common/languages/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list):
            dialect_lang[k] = k
            _dialects(v, k)


def _strip(v, prefix):
    return v.split(":", 1)[1] if isinstance(v, str) and v.startswith(prefix + ":") else v


def _comb_and(vals):
    vals = [x for x in vals if x is not None]
    return None if not vals else (False if False in vals else True)


def _comb_or(vals):
    if any(x is None for x in vals):   # a non-culture alternative: culture isn't required
        return True if True in vals else None
    return True in vals if vals else None


def _neg(x):
    return None if x is None else not x


def cul_scope(block, cul):
    """Culture-scope block (inside `culture = { ... }`) for one culture."""
    info = culture_info.get(cul, {"groups": [], "dialect": None})
    out = []
    for k, op, v in block:
        neg = op == "!="
        if k == "has_culture_group":
            r = _strip(v, "culture_group") in info["groups"]
        elif k in ("this", "merged_culture_group_contains_culture") and isinstance(v, str):
            r = _strip(v, "culture") == cul
        elif k == "language":
            r = dialect_lang.get(info["dialect"]) == _strip(v, "language")
        elif k == "dialect":
            r = info["dialect"] == _strip(v, "dialect")
        elif k in ("OR", "AND", "NOT", "NOR", "not") and isinstance(v, list):
            sub = [cul_scope([x], cul) for x in v]
            r = _comb_or(sub) if k == "OR" else _comb_and(sub) if k == "AND" else _neg(_comb_or(sub))
        else:
            r = None
        out.append(_neg(r) if neg else r)
    return _comb_and(out)


def cul_eval(block, cul):
    """Country-scope trigger judged on culture alone: True / False, or None when it says nothing about culture."""
    info = culture_info.get(cul, {"groups": [], "dialect": None})
    out = []
    for k, op, v in block:
        k = k.strip('"') if k else k
        neg = op == "!="
        if k in ("culture", "any_primary_or_accepted_or_tolerated_culture") and isinstance(v, list):
            r = cul_scope(v, cul)
        elif k == "culture" and isinstance(v, str):
            r = _strip(v, "culture") == cul
        elif k == "culture.language":
            r = dialect_lang.get(info["dialect"]) == _strip(v, "language")
        elif k == "culture.dialect":
            r = info["dialect"] == _strip(v, "dialect")
        elif k in ("OR", "AND", "NOT", "NOR", "not") and isinstance(v, list):
            sub = [cul_eval([x], cul) for x in v]
            r = _comb_or(sub) if k == "OR" else _comb_and(sub) if k == "AND" else _neg(_comb_or(sub))
        else:
            r = None
        out.append(_neg(r) if neg else r)
    return _comb_and(out)


def _mentions_culture(block):
    s = repr(block)
    return any(w in s for w in ("'culture'", "culture.language", "culture.dialect", "any_primary_or_accepted_or_tolerated_culture"))


all_cultures = sorted(culture_info)
# formable -> cultures that meet its culture conditions (potential and allow together)
formable_cultures = {}
for fid, b in formables:
    trig = (get(b, "potential") or []) + (get(b, "allow") or [])
    if not _mentions_culture(trig):
        continue
    res = {c: cul_eval(trig, c) for c in all_cultures}
    if any(r is False for r in res.values()):
        formable_cultures[fid] = sorted(c for c, r in res.items() if r is True)
# advances gated by culture -> cultures that unlock them
cul_adv_src = {}
culture_advs = {}
for f in glob.glob(G + "in_game/common/advances/*.txt"):
    for k, _, v in P(f):
        if not (k and isinstance(v, list)):
            continue
        pot = get(v, "potential") or []
        if not _mentions_culture(pot):
            continue
        hit = [c for c in all_cultures if cul_eval(pot, c) is True]
        if hit and len(hit) <= len(all_cultures) // 2:  # "everyone except X" advances are not culture advances
            cul_adv_src[k] = v
            for c in hit:
                culture_advs.setdefault(c, []).append(k)
# ---------------------------------------------------------------- religions
religion_info = {}  # religion -> group, color
for f in glob.glob(G + "in_game/common/religions/*.txt"):
    for k, _, v in P(f):
        if k and isinstance(v, list) and get(v, "group"):
            religion_info[k] = {"group": get(v, "group"), "color": get(v, "color")}
all_religions = sorted(religion_info)


def rel_eval(block, rel):
    """Trigger judged on religion alone: True / False, or None when it says nothing about religion."""
    grp = religion_info.get(rel, {}).get("group")
    out = []
    for k, op, v in block:
        k = k.strip('"') if k else k
        neg = op == "!="
        if k == "religion" and isinstance(v, str):
            r = _strip(v, "religion") == rel
        elif k == "religion.group" and isinstance(v, str):
            r = _strip(v, "religion_group") == grp
        elif k == "religion" and isinstance(v, list):
            r = rel_eval([(("religion.group" if a == "group" else a), b, c) for a, b, c in v], rel)
        elif k in ("OR", "AND", "NOT", "NOR", "not") and isinstance(v, list):
            sub = [rel_eval([x], rel) for x in v]
            r = _comb_or(sub) if k == "OR" else _comb_and(sub) if k == "AND" else _neg(_comb_or(sub))
        else:
            r = None
        out.append(_neg(r) if neg else r)
    return _comb_and(out)


def _mentions_religion(block):
    s = repr(block)
    return "'religion'" in s or "'religion.group'" in s


formable_religions = {}
for fid, b in formables:
    trig = (get(b, "potential") or []) + (get(b, "allow") or [])
    if not _mentions_religion(trig):
        continue
    res = {r: rel_eval(trig, r) for r in all_religions}
    if any(x is False for x in res.values()):
        formable_religions[fid] = sorted(r for r, x in res.items() if x is True)
rel_adv_src, religion_advs = {}, {}
for f in glob.glob(G + "in_game/common/advances/*.txt"):
    for k, _, v in P(f):
        if not (k and isinstance(v, list)):
            continue
        pot = get(v, "potential") or []
        # only advances granted by religion itself; culture or nation advances that merely need a religion stay with them
        if not _mentions_religion(pot) or _mentions_culture(pot) or tags_in(pot) or "has_or_had_tag" in repr(pot):
            continue
        hit = [r for r in all_religions if rel_eval(pot, r) is True]
        if hit and len(hit) <= len(all_religions) // 2:
            rel_adv_src[k] = v
            for r in hit:
                religion_advs.setdefault(r, []).append(k)
start_by_religion = {}
for t in start_tags:
    r = start_def.get(t, {}).get("religion")
    if r:
        start_by_religion.setdefault(r, []).append(t)

start_by_culture = {}
for t in start_tags:
    c = start_def.get(t, {}).get("culture")
    if c:
        start_by_culture.setdefault(c, []).append(t)


# ================================================================ rendering (per language)
def fmt_num(x):
    return "%g" % x


def mod_line(key, val):
    name = L("MODIFIER_TYPE_NAME_" + key, key)
    t = mod_types.get(key, {})
    if t.get("boolean") == "yes" or val in ("yes", "no"):
        return f"{name}: {T('да') if val == 'yes' else T('нет')}"
    try:
        x = float(val)
    except ValueError:
        x = script_values.get(val)
        if x is None:
            return f"{name}: {val}"
    if t.get("percent") == "yes":
        return f"{name}: {'+' if x > 0 else ''}{fmt_num(round(x * 100, 2))}%"
    return f"{name}: {'+' if x > 0 else ''}{fmt_num(x)}"


def ref(v):
    """Localize a scripted reference such as culture:swedish or c:SWE."""
    if not isinstance(v, str):
        return "…"
    m = re.match(r"^([a-z_]+):(.+)$", v)
    if not m:
        return L(v, v)
    kind, key = m.groups()
    if kind == "c":
        return f"{L(key, key)} ({key})"
    if kind in ("language", "dialect"):
        return adj(key, lang_word=True)
    if kind in ("culture", "culture_group"):
        return adj(key)
    return L(key, key)


def node(text, children=None, kind=None, link=None):
    n = {"t": text}
    if link:
        n["r"] = link  # "cul.<key>", "grp.<key>" or "lang:<name>": the page turns these into links
    if children:
        n["c"] = children
    if kind:
        n["k"] = kind
    return n


def yesno(v):
    return v == "yes"


def trig_list(block):
    return [n for n in (trig(k, op, v) for k, op, v in block) if n]


GROUPS = {"OR": "Любое из:", "AND": "Все из:", "NOT": "НЕ выполнено:", "NOR": "Ни одно из:", "not": "НЕ выполнено:"}
YESNO = {
    "is_subject": ("Является субъектом", "Не является субъектом"), "at_war": ("Ведёт войну", "Не ведёт войну"),
    "in_civil_war": ("Идёт гражданская война", "Нет гражданской войны"),
    "is_hegemon": ("Является гегемоном", "Не является гегемоном"),
    "is_culture_native_american": ("Культура коренных американцев", "Культура не коренных американцев"),
    "is_frankokratia_state": ("Государство франкократии", "Не государство франкократии"),
    "situation_has_ended": ("Ситуация завершилась", "Ситуация не завершилась"),
    "has_ruler": ("Есть правитель", "Нет правителя"),
}
SIMPLE = {  # key -> phrase with one placeholder for ref(value)
    "has_culture_group": "Группа культур: {}", "culture.language": "Язык культуры: {}", "language": "Язык культуры: {}",
    "culture.dialect": "Диалект: {}", "court_language": "Язык двора: {}", "religion": "Религия: {}", "owns": "Владеет локацией: {}",
    "current_age": "Текущая эпоха: {}", "has_reform": "Есть реформа правления: {}", "government_type": "Тип правления: {}",
    "has_estate_privilege": "Есть привилегия сословия: {}", "has_advance": "Изучено развитие: {}",
    "country_rank": "Ранг страны: {}", "is_member_of_international_organization": "Член организации: {}",
    "is_leader_of_international_organization": "Лидер организации: {}", "has_presence_in": "Есть присутствие в: {}",
    "is_core_of": "Является ядром страны {}", "is_situation_active": "Активна ситуация: {}",
    "is_subject_or_below_of": "Субъект страны {}", "in_union_with": "В унии со страной {}", "exists": "Существует: {}",
}


def trig(k, op, v):
    k = k.strip('"') if k else k
    neg = op == "!="
    pre = T("НЕ ") if neg else ""
    if k is None:
        return node(str(v)) if isinstance(v, str) else None
    if k in GROUPS and isinstance(v, list):
        return node(T(GROUPS[k]), trig_list(v), "group")
    if k in ("trigger_if", "trigger_else_if") and isinstance(v, list):
        lim = get(v, "limit") or []
        rest = [(a, b, c) for a, b, c in v if a != "limit"]
        return node(T("Если" if k == "trigger_if" else "Иначе, если"),
                    [node(T("условие:"), trig_list(lim), "group"), node(T("то требуется:"), trig_list(rest), "group")], "if")
    if k == "trigger_else" and isinstance(v, list):
        return node(T("Иначе требуется:"), trig_list(v), "group")
    if k == "limit" and isinstance(v, list):
        return node(T("Условие:"), trig_list(v), "group")
    if k == "custom_tooltip":
        key = get(v, "text") if isinstance(v, list) else v
        return node(L(key, key), None, "tooltip")
    if k == "always":
        return node(T("Всегда") if yesno(v) else T("Никогда (недоступно)"))
    if k == "culture" and isinstance(v, list):
        return node(pre + T("Основная культура:"), trig_list(v), "group")
    if k == "culture":
        return node(pre + T("Основная культура: {}", ref(v)), None, None, "cul." + _strip(v, "culture"))
    if k == "merged_culture_group_contains_culture" and isinstance(v, str):
        return node(pre + T("Объединённая группа включает культуру {}", ref(v)), None, None, "cul." + _strip(v, "culture"))
    if k == "has_culture_group" and isinstance(v, str):
        return node(pre + T("Группа культур: {}", ref(v)), None, None, "grp." + _strip(v, "culture_group"))
    if k in ("culture.language", "language") and isinstance(v, str):
        return node(pre + T("Язык культуры: {}", ref(v)), None, None, "lang:" + ref(v))
    if k == "any_primary_or_accepted_or_tolerated_culture":
        return node(T("Любая основная, принятая или терпимая культура:"),
                    trig_list(v) if isinstance(v, list) else [node(ref(v))], "group")
    if k == "religion.group":
        return node(T("Группа религий НЕ {}" if neg else "Группа религий: {}", ref(v)), None, None,
                    "rgr." + _strip(v, "religion_group") if isinstance(v, str) else None)
    if k == "religion" and isinstance(v, str):
        return node(pre + T("Религия: {}", ref(v)), None, None, "rel." + _strip(v, "religion"))
    if k == "tag":
        return node(pre + T("Страна: {}", f"{L(v, v)} ({v})"))
    if k == "this" and isinstance(v, str):
        return node(T("Не является страной {}" if neg else "Является страной {}", ref(v)))
    if k == "country_exists":
        return node(T("Существует страна {}", ref(v)) if v != "no" else T("Страна не существует"))
    if k == "has_or_had_tag":
        return node(T("Является или была страной {}", f"{L(v, v)} ({v})"))
    if k == "original_tag" and isinstance(v, str):
        return node(pre + T("Только если начали за {}", f"{L(v, v)} ({v})"), None, "orig")
    if k == "current_age_or_later":
        return node(T("Эпоха не раньше: {}", ref(get(v, "age") if isinstance(v, list) else v)))
    if k in YESNO:
        return node(T(YESNO[k][0] if yesno(v) else YESNO[k][1]))
    if k == "country_rank_level":
        names = {lv: L(r, r) for r, lv in rank_level.items()}
        try:
            lv = int(v)
        except ValueError:
            return node(T("Уровень ранга {} {}", op, v), None, "raw")
        if op in ("<", ">"):
            return node(T("Ранг ниже, чем «{}»" if op == "<" else "Ранг выше, чем «{}»", names.get(lv, lv)))
        return node(T("Уровень ранга {} {}", op, v))
    if k == "capital" and isinstance(v, list):
        return node(T("Столица:"), trig_list(v), "group")
    if k == "capital":
        return node(T("Столица: {}", ref(v)))
    if k == "is_member_of_international_organization" and v in ("yes", "no"):
        return node(T("Состоит в организации" if v == "yes" else "Не состоит в организации"))
    if k == "is_member_of_international_organization_of_type":
        return node(pre + T("Член организации типа: {}", ref(get(v, "type") if isinstance(v, list) else v)))
    if k == "has_dlc":
        small = {"of", "the", "and", "in", "on", "to", "a"}
        words = re.sub(r"^d\d+_", "", v).split("_")
        pretty = " ".join(w if (i and w in small) else w.capitalize() for i, w in enumerate(words))
        return node(T("Есть DLC «{}»", L(v, "") or pretty))
    if k.startswith("estate_power("):
        est = re.search(r"estate_type:(\w+)", k)
        return node(T("Сила сословия «{}» {} {}", L(est.group(1)) if est else k, op, v))
    if k == "has_variable":
        return node(T("Есть переменная «{}» (событие/решение)", v))
    if k == "current_year":
        return node(T("Год {} {}", op, v))
    if k == "region" and isinstance(v, str):
        return dict(node(T("Регион: {}", ref(v))), g=v)
    if k in SIMPLE and isinstance(v, str):
        return dict(node(pre + T(SIMPLE[k], ref(v))), g=v)  # g: the game reference, e.g. location:vienna (used by the mod)
    if isinstance(v, list):
        return node(f"{ref(k) if ':' in k else k}:", trig_list(v), "group")
    rhs = T("да") if v == "yes" else T("нет") if v == "no" else ref(v)
    return node(f"{k} {op} {rhs}", None, "raw")


def eff_list(block):
    return [n for n in (eff(k, op, v) for k, op, v in block) if n]


def val(v):
    if isinstance(v, str):
        return fmt_num(script_values[v]) if v in script_values else v
    return "…"


GOOD_EFF = {  # key -> (phrase, which value)
    "unlock_government_reform_effect": ("Открывает реформу правления: {}", "type"),
    "add_reform": ("Добавляет реформу: {}", None), "add_replacing_gov_reform": ("Добавляет реформу: {}", "reform"),
    "unlock_policy_effect": ("Открывает политику: {}", "type"),
    "unlock_casus_belli_effect": ("Открывает повод к войне: {}", "type"), "research_advance": ("Изучает развитие: {}", None),
}
PLAIN_EFF = {
    "remove_reform": ("Убирает реформу: {}", None), "change_government_type": ("Меняет тип правления на: {}", None),
    "set_capital": ("Столица переносится в {}", None), "move_capital_event_effect": ("Предлагает перенести столицу в {}", "to"),
    "set_court_language": ("Язык двора: {}", None), "add_core": ("Добавляет ядро: {}", None),
    "destroy_international_organization": ("Распускает международную организацию {}", "target"),
    "change_societal_value": ("Сдвигает общественную ценность: {}", "type"),
}
FLAT_EFF = {"change_country_color": "Меняет цвет страны на карте", "rename_location": "Переименовывает локацию",
            "remove_country_from_international_organization": "Выходит из международной организации",
            "change_integration_level": "Меняет уровень интеграции локаций"}
GAIN = {"add_stability": "stability", "add_government_power": "government_power", "add_legitimacy": "legitimacy",
        "add_prestige": "prestige"}
GAIN_FALLBACK = {"add_stability": "Стабильность", "add_government_power": "Сила правительства",
                 "add_legitimacy": "Легитимность", "add_prestige": "Престиж"}


def eff(k, op, v):
    if k is None or k in ("limit", "remove_variable", "set_variable"):
        return None
    if k in ("if", "else_if") and isinstance(v, list):
        kids = eff_list([(a, b, c) for a, b, c in v if a != "limit"])
        if not kids:
            return None
        return node(T("Если" if k == "if" else "Иначе, если"),
                    [node(T("условие:"), trig_list(get(v, "limit") or []), "group"), node(T("то:"), kids, "group")], "if")
    if k == "else" and isinstance(v, list):
        return node(T("Иначе:"), eff_list(v), "group")
    if k == "hidden_effect" and isinstance(v, list):
        kids = eff_list(v)
        return node(T("Скрытые эффекты:"), kids, "group") if kids else None
    if k == "set_country_rank_effect":
        r = get(v, "rank")
        return node(T("Ранг страны становится: {}", ref(r)), None, "rank:" + r.split(":")[-1])
    if k in GOOD_EFF or k in PLAIN_EFF:
        phrase, sub = GOOD_EFF.get(k) or PLAIN_EFF[k]
        target = get(v, sub) if sub and isinstance(v, list) else v
        return node(T(phrase, ref(target)), None, "good" if k in GOOD_EFF else None)
    if k in FLAT_EFF:
        return node(T(FLAT_EFF[k]))
    if k == "add_country_modifier":
        m = get(v, "modifier")
        yrs = get(v, "years")
        kids = [node(mod_line(a, b)) for a, b in static_mods.get(m, [])]
        name = L("STATIC_MODIFIER_NAME_" + m, L(m, m))
        return node(T("Модификатор «{}»", name) + (T(" на {} лет", yrs) if yrs else ""), kids, "good")
    if k in GAIN:
        name = L(GAIN[k], "") or T(GAIN_FALLBACK[k])
        return node(f"{name}: +{val(v)}", None, "good")
    if k == "trigger_event_non_silently":
        title = L(v + ".title", "") or L(v + ".t", "")
        return node(T("Событие: {}", title) if title else T("Событие {}", v))
    if isinstance(v, list):
        kids = eff_list(v)
        label = ref(k) if ":" in k else L(k, k)
        return node(f"{label}:", kids, "group") if kids else node(label, None, "raw")
    return node(f"{L(k, k)}{'' if v == 'yes' else ' = ' + ref(v)}", None, "raw")


def _mods(block):
    return [mod_line(a, b) for a, _, b in (block or []) if a and a != "potential_trigger" and isinstance(b, str)]


def unlock_entry(kind, key):
    """{"t": "Town right: X", "m": [modifier lines], "loc": [local modifier lines]} for an unlock."""
    name = L(key, "")
    if not name and kind == "unlock_levy":
        unit = get(levy_defs.get(key, []), "unit")
        name = L(unit, "") if unit else ""
        name = name or L(key.removeprefix("levy_"), "") or key.removeprefix("levy_").replace("_", " ").capitalize()
    e = {"t": f"{T(UNLOCKS[kind])}: {name or key}", "kind": kind, "k": key}
    if kind == "unlock_town_rights" and key in town_right_defs:
        v = town_right_defs[key]
        e["loc"] = _mods(get(v, "location_modifier"))
        e["m"] = _mods(get(v, "country_modifier"))
    elif kind == "unlock_government_reform" and key in reform_defs:
        e["m"] = [x for blk in get_all(reform_defs[key], "country_modifier") if isinstance(blk, list) for x in _mods(blk)]
    return e


def build_lang(lang):
    global LANG, loc, loc_en
    LANG = lang
    loc = load_loc([G + f"main_menu/localization/{lang}", G + f"in_game/localization/{lang}"])
    if not loc_en:
        loc_en = load_loc([G + "main_menu/localization/english"])

    ranks = {}
    for k, v in rank_src:
        rm = get(v, "rank_modifier") or []
        ranks[k] = {"name": L(k, k), "level": rank_level[k],
                    "mods": [mod_line(a, b) for a, _, b in rm if a and not a.startswith("ai_") and isinstance(b, str)]}

    def reforms(tag):
        out = []
        for k, v in reform_src.get(tag, []):
            pot = get(v, "potential") or []
            groups = []
            for kk, _, blk in v:
                if kk != "country_modifier" or not isinstance(blk, list):
                    continue
                cond = get(blk, "potential_trigger")
                lines = [mod_line(a, b) for a, _, b in blk if a and a != "potential_trigger" and isinstance(b, str)]
                if lines:
                    groups.append({"if": trig_list(cond) if cond else [], "m": lines})
            extra = [(a, b, c) for a, b, c in pot if not (a and TAG_RE.match(a)) and a != "has_unlocked_government_reform_trigger"
                     and not (a == "OR" and isinstance(c, list) and all(TAG_RE.match(x or "") for x, _, _ in c))]
            src = []
            for kind, key in reform_unlockers.get(k, []):
                name = L(key + ".title", "") or L(key + ".t", "") or (L(key, "") if kind != "event" else "")
                src.append({"k": kind, "n": name or key})
            age = get(v, "age", "")
            m = re.match(r"age_(\d+)_", age or "")
            out.append({"id": k, "n": L(k, k), "d": L(k + "_desc", ""), "gov": L(get(v, "government", ""), "") if get(v, "government") else "",
                        "age": int(m.group(1)) if m else 0, "ageN": L(age, "") if age else "",
                        "g": groups, "cond": trig_list(extra), "src": src,
                        "locked": any(a == "has_unlocked_government_reform_trigger" for a, _, _ in pot)})
        return sorted(out, key=lambda r: (r["age"], r["n"]))

    def advances(tag):
        out = []
        for k, v in adv_src.get(tag, []):
            pot = get(v, "potential") or []
            age = get(v, "age", "")
            m = re.match(r"age_(\d+)_", age)
            bonuses, unlocks = [], []
            for kk, _, vv in v:
                if not kk or not isinstance(vv, str):
                    continue
                if kk in UNLOCKS:
                    unlocks.append(unlock_entry(kk, vv))
                elif kk in mod_types:
                    bonuses.append(mod_line(kk, vv))
            # original_tag stays visible: such advances need you to have started as that nation, forming it is not enough
            extra = [(a, b, c) for a, b, c in pot if not (a and TAG_RE.match(a))
                     and not (a == "OR" and isinstance(c, list) and any(x and TAG_RE.match(x) and y == tag for x, _, y in c)) and not (
                a == "OR" and isinstance(c, list) and all(TAG_RE.match(x or "") for x, _, _ in c))]
            out.append({"id": k, "n": L(k, k), "age": int(m.group(1)) if m else 0, "ageN": L(age, age),
                        "req": [L(r, r) for r in get_all(v, "requires")], "b": bonuses, "u": unlocks,
                        "cond": trig_list(extra), "d": L(k + "_desc", "")})
        return sorted(out, key=lambda a: (a["age"], a["n"]))

    items = []
    for fid, b in formables:
        tag = get(b, "tag", "")
        terr, req = {}, set()
        for key, label in (("continents", "Континенты"), ("sub_continents", "Субконтиненты"), ("regions", "Регионы"),
                           ("areas", "Области"), ("provinces", "Провинции"), ("locations", "Локации")):
            lst = [x for _, _, x in (get(b, key) or []) if isinstance(x, str)]
            if not lst:
                continue
            entries = []
            for g in lst:
                ms = members.get(g, {g} if g not in excluded else set())
                req |= ms
                entries.append({"n": L(g, g), "c": len(ms), "k": g})
            terr[T(label)] = entries
        frac = float(get(b, "required_locations_fraction", "1.0"))
        cont = Counter(loc_continent.get(l) for l in req if loc_continent.get(l)).most_common(1)
        color = get(b, "color")
        effect = eff_list(get(b, "form_effect") or [])
        pot_raw = get(b, "potential") or []
        by_event = [(k2, v2) for k2, _, v2 in pot_raw] == [("always", "no")]
        adv = advances(tag)
        items.append({
            "id": fid, "tag": tag, "name": L(get(b, "name", tag), tag),
            "level": int(get(b, "level", "1")), "rule": get(b, "rule", "historical"),
            "frac": frac, "cap": get(b, "capital_required", "yes") != "no",  # 1.4 default: capital must be inside
            "own": get(b, "potential_requires_own", "yes") != "no",
            "color": to_hex(named_colors.get(color)) if isinstance(color, str) else to_hex(color),
            "terr": terr, "total": len(req), "need": math.ceil(len(req) * frac) if req else 0,
            "contk": cont[0][0] if cont else "",
            "cont": L(cont[0][0], cont[0][0]) if cont else (T("Только событием") if by_event else "—"),
            "pot": trig_list(pot_raw), "allow": trig_list(get(b, "allow") or []), "eff": effect,
            "ranks": sorted(set(re.findall(r'"k": "rank:(\w+)"', json.dumps(effect, ensure_ascii=False)))),
            "event": by_event, "start": tag in start_tags, "desc": L(fid + "_desc", ""), "adv": adv, "nadv": len(adv), "ref": reforms(tag),
        })
    items.sort(key=lambda x: (-x["level"], x["name"]))

    # Nations that exist in 1337 but have no formable entry (no tier): they can't be formed.
    formable_tags = {get(b, "tag", "") for _, b in formables}
    fixed = []
    for tag, v in start_setup.items():
        if tag in formable_tags:
            continue
        d = start_def.get(tag, {})
        locs = start_locations(v)
        cap = get(v, "capital")
        cont = loc_continent.get(cap) or (Counter(loc_continent.get(l) for l in locs if loc_continent.get(l)).most_common(1) or [[None]])[0][0]
        rank = get(v, "country_rank")
        color = d.get("color")
        adv = advances(tag)
        fixed.append({
            "id": tag, "tag": tag, "name": L(tag, tag), "rank": L(rank, "") if rank else "", "rankLevel": rank_level.get(rank, 0),
            "cul": adj(d["culture"]) if d.get("culture") else "", "rel": L(d["religion"], "") if d.get("religion") else "",
            "cap": L(cap, cap) if cap else "", "capk": loc_parent.get(cap) or "", "contk": cont or "",
            "cont": L(cont, cont) if cont else "—", "locs": len(locs),
            "color": to_hex(named_colors.get(color)) if isinstance(color, str) else to_hex(color),
            "adv": adv, "nadv": len(adv), "ref": reforms(tag), "ck": d.get("culture"), "rk": d.get("religion"),
        })
    fixed.sort(key=lambda x: (-x["locs"], x["name"]))
    for it in items:
        cul = formable_cultures.get(it["id"])
        it["cul"] = cul if cul is not None else None   # None: no culture requirement
    for fid, b in formables:
        pot = get(b, "potential") or []
        # visibility conditions beyond culture (religion, tags, events, special states)
        xc = any(not _mentions_culture([(k, o, v)]) for k, o, v in pot)
        for it in items:
            if it["id"] == fid:
                it["xc"] = xc

    # Cultures: their advances (stored once in cadv), formables they can form, nations that start with them.
    cadv = {}
    for k, v in cul_adv_src.items():
        pot = get(v, "potential") or []
        age = get(v, "age", "")
        m = re.match(r"age_(\d+)_", age or "")
        bonuses, unlocks = [], []
        for kk, _, vv in v:
            if not kk or not isinstance(vv, str):
                continue
            if kk in UNLOCKS:
                unlocks.append(unlock_entry(kk, vv))
            elif kk in mod_types:
                bonuses.append(mod_line(kk, vv))
        # culture conditions are what the list itself shows; keep only the other conditions
        extra = [(a, b, c) for a, b, c in pot if not _mentions_culture([(a, b, c)]) and not (a and TAG_RE.match(a))
                 and "merged_culture_group_contains_culture" not in repr(c)]
        gk = sorted(set(re.findall(r"culture_group:(\w+)", repr(pot))))  # granted through a culture group
        cadv[k] = {"id": k, "n": L(k, k), "age": int(m.group(1)) if m else 0, "ageN": L(age, age),
                   "req": [L(r, r) for r in get_all(v, "requires")], "b": bonuses, "u": unlocks,
                   "cond": trig_list(extra), "d": L(k + "_desc", ""), "gk": gk, "grp": [adj(g) for g in gk]}
    forms_by_culture = {}
    for fid, cs in formable_cultures.items():
        for c in cs:
            forms_by_culture.setdefault(c, []).append(fid)
    cultures = []
    for c in all_cultures:
        info = culture_info[c]
        advs = sorted(culture_advs.get(c, []), key=lambda a: (cadv[a]["age"], cadv[a]["n"]))
        color = info.get("color")
        lang_key = dialect_lang.get(info.get("dialect"))
        cultures.append({
            "id": "cul." + c, "key": c, "name": adj(c), "gk": info["groups"],
            "groups": [adj(g) for g in info["groups"]], "lang": adj(lang_key, lang_word=True) if lang_key else "",
            "dia": (adj(info["dialect"], lang_word=True) + " " + T("диалект")) if info.get("dialect") and info.get("dialect") != lang_key else "",
            "color": to_hex(named_colors.get(color)) if isinstance(color, str) else to_hex(color),
            "adv": advs, "nadv": len(advs), "forms": forms_by_culture.get(c, []), "st": sorted(start_by_culture.get(c, [])),
        })
    cultures.sort(key=lambda x: (-x["nadv"], x["name"]))
    group_keys = sorted({g for c in culture_info.values() for g in c["groups"]})
    groups = []
    for g in group_keys:
        members_ = [c for c in all_cultures if g in culture_info[c]["groups"]]
        gadv = sorted([a for a, x in cadv.items() if g in x["gk"]], key=lambda a: (cadv[a]["age"], cadv[a]["n"]))
        groups.append({"id": "grp." + g, "key": g, "name": adj(g), "cultures": members_, "adv": gadv})
    geo = {g: {**x, "n": L(g, g)} for g, x in geo_info.items()}

    # Religions: advances (stored once in radv), formables they allow, nations that start with them.
    for it in items:
        it["rel"] = formable_religions.get(it["id"])   # None: no religion requirement
    radv = {}
    for k, v in rel_adv_src.items():
        pot = get(v, "potential") or []
        age = get(v, "age", "")
        m = re.match(r"age_(\d+)_", age or "")
        bonuses, unlocks = [], []
        for kk, _, vv in v:
            if not kk or not isinstance(vv, str):
                continue
            if kk in UNLOCKS:
                unlocks.append(unlock_entry(kk, vv))
            elif kk in mod_types:
                bonuses.append(mod_line(kk, vv))
        extra = [(a, b, c) for a, b, c in pot if not _mentions_religion([(a, b, c)])]
        gk = sorted(set(re.findall(r"religion_group:(\w+)", repr(pot))))
        radv[k] = {"id": k, "n": L(k, k), "age": int(m.group(1)) if m else 0, "ageN": L(age, age),
                   "req": [L(r, r) for r in get_all(v, "requires")], "b": bonuses, "u": unlocks,
                   "cond": trig_list(extra), "d": L(k + "_desc", ""), "rgk": gk, "rgrp": [L(g, g) for g in gk]}
    forms_by_rel = {}
    for fid, rs in formable_religions.items():
        for r in rs:
            forms_by_rel.setdefault(r, []).append(fid)
    religions = []
    for r in all_religions:
        info = religion_info[r]
        advs = sorted(religion_advs.get(r, []), key=lambda a: (radv[a]["age"], radv[a]["n"]))
        color = info.get("color")
        religions.append({"id": "rel." + r, "key": r, "name": L(r, r), "gk": info["group"], "group": L(info["group"], info["group"]),
                          "color": to_hex(named_colors.get(color)) if isinstance(color, str) else to_hex(color),
                          "adv": advs, "nadv": len(advs), "forms": forms_by_rel.get(r, []), "st": sorted(start_by_religion.get(r, []))})
    religions.sort(key=lambda x: (-x["nadv"], x["name"]))
    rgroups = []
    for g in sorted({x["group"] for x in religion_info.values()}):
        mem = [r for r in all_religions if religion_info[r]["group"] == g]
        gadv = sorted([a for a, x in radv.items() if g in x["rgk"]], key=lambda a: (radv[a]["age"], radv[a]["n"]))
        rgroups.append({"id": "rgr." + g, "key": g, "name": L(g, g), "religions": mem, "adv": gadv})
    return {"lang": lang, "geo": geo, "items": items, "fixed": fixed, "cultures": cultures, "groups": groups, "religions": religions, "rgroups": rgroups, "radv": radv, "cadv": cadv, "ranks": ranks, "version": VERSION}


# ================================================================ output
def full_page(body):
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n</head>\n<body>\n"
            + body + "\n</body>\n</html>\n")


def main():
    all_data = {}
    os.makedirs(os.path.join(HERE, "site", "data"), exist_ok=True)
    for lang in LANGS:
        d = build_lang(lang)
        all_data[lang] = d
        p = os.path.join(HERE, "site", "data", f"{lang}.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"{lang:13} {len(d['items'])} formables, {os.path.getsize(p) // 1024} KB")
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    rev = hashlib.sha1(json.dumps(all_data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:10]
    tpl = tpl.replace("__REV__", rev)
    with open(os.path.join(HERE, "site", "index.html"), "w", encoding="utf-8") as fh:
        fh.write(tpl.replace("/*__EMBED__*/null", "null"))
    # the offline file embeds Russian and English only, to stay a reasonable size
    embed = {k: all_data[k] for k in ("russian", "english")}
    standalone = full_page(tpl.replace("/*__EMBED__*/null", json.dumps(embed, ensure_ascii=False, separators=(",", ":"))))
    # GitHub Pages version: a complete document that loads data/<lang>.json
    with open(os.path.join(HERE, "site", "pages.html"), "w", encoding="utf-8") as fh:
        fh.write(full_page(tpl.replace("/*__EMBED__*/null", "null")))
    with open(os.path.join(HERE, "formables.html"), "w", encoding="utf-8") as fh:
        fh.write(standalone)
    print("standalone:", os.path.getsize(os.path.join(HERE, "formables.html")) // 1024, "KB")


if __name__ == "__main__":
    main()
