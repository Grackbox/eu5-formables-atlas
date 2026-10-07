"""Builds the EU5 mod "Formables Atlas" from the site data (site/data/<lang>.json, made by build.py).

* The game's own tooltips for formables, cultures, religions and religion groups get an extra block (what the site
  knows and the game doesn't show: territory, required cultures, what a culture can form, nations at the start...).
  Culture.GetKey / Religion.GetKey / ReligionGroup.GetKey return the object's index in load order, so the blocks are
  keyed by that index; formables are keyed by FormableCountry.GetFlagTag.
* Nations without a tier are hidden game concepts (the game has no tooltip for a country that isn't on the map).
* Every other name is a native game link, so the game shows it in the player's language and opens its own tooltip.
* A window with four tables opens from a button in the Formables panel. Each table is split into parts (continents,
  religion families) picked with buttons, and sorted by clicking a column header. A column is one multi-line text per
  100 rows whose loc key is built from the part/sort variables, so switching costs no extra widgets.
"""
import collections
import json
import os
import re
import shutil

import native_lists

HERE = os.path.dirname(os.path.abspath(__file__))
G = os.environ.get("EU5_GAME", "E:/SteamLibrary/steamapps/common/Europa Universalis V/game").rstrip("/\\") + "/"
OUT = os.environ.get("FMX_OUT", os.path.expanduser("~/Documents/Paradox Interactive/Europa Universalis V/mod/formables_atlas"))
LANGS = ["english", "russian", "german", "french", "spanish", "braz_por", "polish", "turkish", "japanese", "korean", "simp_chinese"]
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII"]
SHOW = {"continent": "ShowContinentName", "sub_continent": "ShowSubContinentName", "region": "ShowRegionName",
        "area": "ShowAreaName", "province": "ShowProvinceDefinitionName"}
CHUNK = 100
WINDOW_W = 1480
REVERSIBLE = {"f", "r"}     # the big tables get one direction per sort to keep the loc files small
CONTINENTS = ["europe", "asia", "africa", "america", "oceania"]
RELIGION_PARTS = [
    ("christian",),
    ("muslim", "israelite_group", "zoroastrian_group", "druze_group", "mandean_group", "manichaean_group", "yazidi_group"),
    ("buddhist", "tonal_group", "dharmic"),
    ("folk_asian_group", "folk_se_asian_group", "folk_african_group", "folk_european_group", "folk_permic_group"),
    None,                   # every other folk group: the Americas and Oceania
]

UI = {
    "russian": {
        "title": "Атлас формируемых стран", "open": "Атлас формируемых стран, культур и религий",
        "tabs": {"f": "Формируемые", "x": "Без тира", "c": "Культуры", "r": "Религии"},
        "hint": "Нажмите на заголовок колонки, чтобы отсортировать. Наведите на название — откроется карточка игры с данными атласа.",
        "rparts": ["Христианство", "Ислам и Ближний Восток", "Восточные", "Народные: Старый Свет", "Народные: Новый Свет и Океания"],
        "tier": "Тир", "rules": {"historical": "историческое", "plausible": "правдоподобное", "fantasy": "фантазийное"},
        "atlas": "Атлас", "rights": "Городские права", "unlocks": "Также открывает", "terr": "Территория", "own": "нужно {p}% локаций: {a} из {b}", "cap_req": "столица должна быть в этих землях",
        "cap_free": "столица может быть где угодно", "event": "формируется только событием или решением",
        "cul": "Нужные культуры", "rel": "Нужные религии", "any_cul": "любая культура", "any_rel": "любая религия",
        "pot": "Кто видит", "allow": "Условия", "adv": "Страновые улучшения",
        "cadv": "Культурные улучшения", "radv": "Религиозные улучшения", "gadv": "Общие улучшения группы",
        "ref": "Государственные принципы", "forms": "Может сформировать", "st": "Страны на старте",
        "lang": "Язык", "more": "и ещё {n}",
        "notier": "Тира нет: эту страну нельзя сформировать, только играть за неё с начала.",
        "start": "Существует на старте 1337 года — формируется, когда её не станет; начав за неё, вы уже на этом тире.",
        "capital": "Столица", "culture": "Культура", "religion": "Религия", "continent": "Континент", "locs": "Локаций",
        "rank": "Ранг", "none": "нет", "xc": "+ условия", "variant": "Вариант", "yes": "да", "no": "нет", "any": "любая",
        "h": {"nation": "Страна", "tag": "Тег", "tier": "Тир", "rule": "Тип", "need": "Нужно локаций",
              "cap": "Столица", "culs": "Культуры", "adv": "Улучшения", "rank": "Ранг", "cul": "Культура", "rel": "Религия",
              "locs": "Локаций", "group": "Группа", "lang": "Язык", "forms": "Формаблы", "st": "На старте"},
        "az": ("А→Я", "Я→А"), "num": ("9→1", "1→9"),
    },
    "english": {
        "title": "Formables Atlas", "open": "Atlas of formable nations, cultures and religions",
        "tabs": {"f": "Formable", "x": "No tier", "c": "Cultures", "r": "Religions"},
        "hint": "Click a column header to sort. Hover a name to open the game's tooltip with the atlas data.",
        "rparts": ["Christianity", "Islam and the Near East", "Eastern", "Folk: Old World", "Folk: New World and Oceania"],
        "tier": "Tier", "rules": {"historical": "historical", "plausible": "plausible", "fantasy": "fantasy"},
        "atlas": "Atlas", "rights": "Town rights", "unlocks": "Also unlocks", "terr": "Territory", "own": "own {p}% of the locations: {a} of {b}", "cap_req": "your capital must be in these lands",
        "cap_free": "your capital can be anywhere", "event": "formed only through an event or decision",
        "cul": "Required cultures", "rel": "Required religions", "any_cul": "any culture", "any_rel": "any religion",
        "pot": "Who sees it", "allow": "Conditions", "adv": "Country advances",
        "cadv": "Culture advances", "radv": "Religious advances", "gadv": "Shared group advances",
        "ref": "State principles", "forms": "Can form", "st": "Nations at the start",
        "lang": "Language", "more": "and {n} more",
        "notier": "No tier: this nation can't be formed; you can only play it from the start.",
        "start": "Exists at the 1337 start: it can be formed once it no longer exists; starting as it puts you on this tier.",
        "capital": "Capital", "culture": "Culture", "religion": "Religion", "continent": "Continent", "locs": "Locations",
        "rank": "Rank", "none": "none", "xc": "+ conditions", "variant": "Variant", "yes": "yes", "no": "no", "any": "any",
        "h": {"nation": "Nation", "tag": "Tag", "tier": "Tier", "rule": "Type", "need": "Locations needed",
              "cap": "Capital", "culs": "Cultures", "adv": "Advances", "rank": "Rank", "cul": "Culture", "rel": "Religion",
              "locs": "Locations", "group": "Group", "lang": "Language", "forms": "Formables", "st": "At start"},
        "az": ("A→Z", "Z→A"), "num": ("9→1", "1→9"),
    },
}


# ---------------------------------------------------------------- game files

def top_level_keys(folder):
    """Object keys in load order (files by name, objects in file order): the index Culture.GetKey returns."""
    keys = []
    for f in sorted(os.listdir(G + folder)):
        if not f.endswith(".txt"):
            continue
        s = re.sub(r"#[^\n]*", "", open(G + folder + "/" + f, encoding="utf-8-sig").read())
        depth = 0
        for m in re.finditer(r"([A-Za-z0-9_\-\.]+)\s*=\s*\{|\{|\}", s):
            if m.group(1):
                if depth == 0:
                    keys.append(m.group(1))
                depth += 1
            elif m.group(0) == "{":
                depth += 1
            else:
                depth -= 1
    return {k: i for i, k in enumerate(keys)}


def culture_continents():
    """Continent where most of a culture's people live at the 1337 start."""
    s = re.sub(r"#[^\n]*", "", open(G + "in_game/map_data/definitions.txt", encoding="utf-8-sig").read())
    stack, loc_cont = [], {}
    for m in re.finditer(r"([A-Za-z0-9_\-\.]+)\s*=\s*\{|\{|\}|([A-Za-z0-9_\-\.]+)", s):
        if m.group(1):
            stack.append(m.group(1))
        elif m.group(0) == "{":
            stack.append("?")
        elif m.group(0) == "}":
            stack.pop()
        else:
            loc_cont[m.group(2)] = stack[0]
    size = collections.defaultdict(collections.Counter)
    cur = None
    for line in open(G + "main_menu/setup/1337/06_pops.txt", encoding="utf-8-sig"):
        m = re.match(r"^\s*([A-Za-z0-9_\-]+)\s*=\s*\{\s*$", line)
        if m:
            cur = m.group(1)
            continue
        m = re.search(r"size\s*=\s*([\d.]+)\s+culture\s*=\s*(\w+)", line)
        if m and loc_cont.get(cur) in CONTINENTS:
            size[m.group(2)][loc_cont[cur]] += float(m.group(1))
    return {c: n.most_common(1)[0][0] for c, n in size.items()}


# ---------------------------------------------------------------- text helpers

def clean(s):
    """Text that is safe inside a Paradox loc string."""
    s = str(s).replace('"', "”").replace("$", "").replace("#", "")
    return s.replace("[", "(").replace("]", ")").replace("\n", " ")


def units(s):
    """Display width of a name in Latin-letter units (CJK glyphs are about twice as wide)."""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in s)


def px(n):
    return int(n * 9.5) + 20


def ck(prefix, key):
    return "fmx_" + prefix + "_" + re.sub(r"[^a-z0-9_]", "_", key.lower())


def native(fn, key):
    return f"[{fn}('{key}')]"


def nlink(kind, key):
    """Native game link: the game shows the name in the player's language and opens its own tooltip."""
    return native({"c": "ShowCultureName", "cg": "ShowCultureGroupName", "r": "ShowReligionName",
                   "rg": "ShowReligionGroupName", "f": "ShowFormableCountryName"}[kind], key)


def joined(items, u, cap=60):
    items = list(items)
    s = ", ".join(items[:cap])
    if len(items) > cap:
        s += " " + u["more"].format(n=len(items) - cap)
    return s


REF_LINK = {"location": "ShowLocationName", "area": "ShowAreaName", "region": "ShowRegionName", "province": "ShowProvinceDefinitionName",
            "sub_continent": "ShowSubContinentName", "continent": "ShowContinentName", "culture": "ShowCultureName",
            "culture_group": "ShowCultureGroupName", "religion": "ShowReligionName", "religion_group": "ShowReligionGroupName",
            "language": "ShowLanguageName", "dialect": "ShowDialectName", "advance": "ShowAdvanceName"}
UNLOCK_LINK = {"unlock_town_rights": "ShowTownRightsName", "unlock_government_reform": "ShowGovernmentReformName",
               "unlock_building": "ShowBuildingTypeName", "unlock_unit": "ShowUnitDefinitionName", "unlock_law": "ShowLawName",
               "unlock_policy": "ShowPolicyName", "unlock_estate_privilege": "ShowEstatePrivilegeName", "unlock_casus_belli": "ShowCasusBelliName"}


def unlock_lines(advs, u):
    """What a set of advances unlocks: town rights on their own line, everything else after."""
    rights, other = [], []
    for a in advs:
        for e in a.get("u", []):
            fn = UNLOCK_LINK.get(e.get("kind"))
            item = native(fn, e["k"]) if fn and e.get("k") else clean(e["t"])
            (rights if e.get("kind") == "unlock_town_rights" else other).append(item)
    out = []
    if rights:
        out.append(f"{u['rights']}: " + ", ".join(dict.fromkeys(rights)))
    if other:
        out.append(f"{u['unlocks']}: " + ", ".join(dict.fromkeys(other)))
    return "\n".join(out)


def tree_text(nodes, d, depth=0):
    """Condition tree -> bullet lines; culture/religion references become native links."""
    out = []
    for n in nodes:
        t = clean(n["t"])
        r = n.get("r") or ""
        target = None
        for pre, kind, pool in (("cul.", "c", "culByKey"), ("grp.", "cg", "grpByKey"), ("rel.", "r", "relByKey"), ("rgr.", "rg", "rgrByKey")):
            if r.startswith(pre) and r[4:] in d[pool]:
                target = (d[pool][r[4:]]["name"], nlink(kind, r[4:]))
        g = n.get("g") or ""
        if not target and ":" in g and ": " in t and g.split(":", 1)[0] in REF_LINK:
            # a game reference such as location:vienna: its name in the text becomes the game's own link
            target = (t.split(": ", 1)[1], native(REF_LINK[g.split(":", 1)[0]], g.split(":", 1)[1]))
        if target and clean(target[0]) in t:
            i = t.rfind(clean(target[0]))
            t = t[:i] + target[1] + t[i + len(clean(target[0])):]
        out.append("  " * depth + "• " + t)
        out += tree_text(n.get("c", []), d, depth + 1)
    return out


def adv_lines(advs, title):
    if not advs:
        return []
    by_age = {}
    for a in advs:
        by_age.setdefault(a["age"], []).append(native("ShowAdvanceName", a["id"]))
    lines = [f"{title} ({len(advs)}):"]
    for age in sorted(by_age):
        lines.append(f"  {ROMAN[age] if age < len(ROMAN) else age}: " + ", ".join(by_age[age]))
    return lines


def by_groups(keys, groups, members, kind, gkind):
    """Links for a set of cultures/religions; a whole group in the set is shown as the group."""
    left, out = set(keys), []
    for g in sorted(groups, key=lambda g: -len(g[members])):
        m = set(g[members])
        if len(m) > 1 and m <= left:
            out.append(nlink(gkind, g["key"]))
            left -= m
    return out + [nlink(kind, k) for k in keys if k in left]


def formable_lines(i, d, u, max_cond=8):
    """Our part of a formable's tooltip; the game already shows its rank, advances, effects and flavour text."""
    L = [f"{u['tier']} {i['level']} · {u['rules'].get(i['rule'], i['rule'])}" + (" · " + clean(i["cont"]) if i.get("cont") else "")]
    if i.get("start"):
        L.append(clean(u["start"]))
    if i["event"]:
        L.append(f"{u['terr']}: {u['event']}")
    else:
        geo = []
        for lst in i["terr"].values():
            for e in lst:
                g = d["geo"].get(e.get("k", ""))
                geo.append(native(SHOW[g["lv"]], e["k"]) if g and g["lv"] in SHOW else
                           native("ShowLocationName", e["k"]) if e.get("k") else clean(e["n"]))
        L.append(f"{u['terr']}: {u['own'].format(p=round(i['frac'] * 100), a=i['need'], b=i['total'])}; "
                 + (u["cap_req"] if i["cap"] else u["cap_free"]))
        L.append("  " + ", ".join(geo))
    L.append(f"{u['cul']}: " + (u["any_cul"] if i.get("cul") is None else
                                 joined(by_groups(i["cul"], d["groups"], "cultures", "c", "cg"), u, 15)))
    L.append(f"{u['rel']}: " + (u["any_rel"] if i.get("rel") is None else
                                 joined(by_groups(i["rel"], d["rgroups"], "religions", "r", "rg"), u, 15)))
    # who sees the formable mostly repeats the cultures above; the conditions are kept short
    if i["allow"]:
        lines = [l for l in tree_text(i["allow"], d, 1) if l.startswith("  ") and not l.startswith("      ")]
        L += [f"{u['allow']}:"] + lines[:max_cond] + (["  …"] if len(lines) > max_cond else [])
    if i.get("ref"):
        L.append(f"{u['ref']}: " + ", ".join(native("ShowGovernmentReformName", r["id"]) for r in i["ref"]))
    return L


def block(u, lines):
    """Text of an extra tooltip block; empty when there is nothing to add, so the game hides the block."""
    lines = [l for l in lines if l]
    if not lines:
        return ""
    return (f"{u['atlas']}:\n" + "\n".join(lines)).replace("\n", "\\n")


# ---------------------------------------------------------------- tables

class Col:
    def __init__(self, hk, width, cell, key=None, num=False):
        self.hk, self.width, self.cell, self.key, self.num = hk, width, cell, key, num


def load(lang):
    d = json.load(open(os.path.join(HERE, "site", "data", f"{lang}.json"), encoding="utf-8"))
    d["culByKey"] = {c["key"]: c for c in d["cultures"]}
    d["grpByKey"] = {g["key"]: g for g in d["groups"]}
    d["relByKey"] = {r["key"]: r for r in d["religions"]}
    d["rgrByKey"] = {g["key"]: g for g in d["rgroups"]}
    return d


def name_widths(datas):
    """Native names can't be shortened, so a name column is as wide as its longest name in any language."""
    w = {}
    for d in datas:
        for k, names in (("f", [i["name"] for i in d["items"]]), ("c", [c["name"] for c in d["cultures"]]),
                         ("cg", [g["name"] for g in d["groups"]]), ("r", [r["name"] for r in d["religions"]]),
                         ("rg", [g["name"] for g in d["rgroups"]])):
            w[k] = max(w.get(k, 0), px(max(map(units, names))))
    return w


def religion_part(group):
    for n, keys in enumerate(RELIGION_PARTS):
        if keys and group in keys:
            return n
    return 4 if group.startswith("folk_") else 1


def tables(d, u, nw, cul_cont):
    def cut(s, w):
        s = clean(s)
        while px(units(s)) > w and len(s) > 4:
            s = s[:-2].rstrip() + "…"
        return s

    def text(w, f):
        return lambda r: cut(f(r), w)

    def x_name(x):
        short = cut(x["name"], 250)
        return f"[{ck('x', x['tag'])}|e]" if short == clean(x["name"]) else f"[Concept('{ck('x', x['tag'])}','{short.replace(chr(39), '’')}')|e]"

    cont_name = {}
    for r in d["items"] + d["fixed"]:
        if r.get("contk"):
            cont_name[r["contk"]] = r["cont"]
    event_name = next((i["cont"] for i in d["items"] if i["event"]), "—")

    culs, rels, grps, rgrs = d["culByKey"], d["relByKey"], d["grpByKey"], d["rgrByKey"]
    first_group = lambda c: next((g for g in c["gk"] if g in grps), None)
    rule_order = {"historical": 0, "plausible": 1, "fantasy": 2}
    T = {}
    # (rows, part names, part of a row, columns)
    T["f"] = (d["items"], [cont_name.get(c, c) for c in CONTINENTS] + [event_name],
              lambda i: len(CONTINENTS) if i["event"] else CONTINENTS.index(i["contk"]), [
        Col("nation", nw["f"], lambda i: nlink("f", i["id"]), lambda i: i["name"].casefold()),
        Col("tag", 70, lambda i: i["tag"]),
        Col("tier", 80, lambda i: ROMAN[i["level"]], lambda i: i["level"], True),
        Col("rule", 170, text(170, lambda i: u["rules"].get(i["rule"], i["rule"])), lambda i: rule_order.get(i["rule"], 9)),
        Col("need", 170, lambda i: "—" if i["event"] else str(i["need"]), lambda i: -1 if i["event"] else i["need"], True),
        Col("adv", 130, lambda i: str(len(i["adv"])), lambda i: len(i["adv"]), True),
    ])
    T["x"] = (d["fixed"], [cont_name.get(c, c) for c in CONTINENTS], lambda x: CONTINENTS.index(x["contk"]), [
        Col("nation", 250, x_name, lambda x: x["name"].casefold()),
        Col("tag", 70, lambda x: x["tag"]),
        Col("rank", 150, text(150, lambda x: x["rank"] or u["none"]), lambda x: x.get("rankLevel") or 0, True),
        Col("cul", nw["c"], lambda x: nlink("c", x["ck"]) if x.get("ck") in culs else cut(x["cul"] or "", nw["c"]),
            lambda x: (x["cul"] or "~").casefold()),
        Col("rel", nw["r"], lambda x: nlink("r", x["rk"]) if x.get("rk") in rels else cut(x["rel"] or "", nw["r"]),
            lambda x: (x["rel"] or "~").casefold()),
        Col("locs", 100, lambda x: str(x["locs"]), lambda x: x["locs"], True),
        Col("adv", 110, lambda x: str(len(x["adv"])), lambda x: len(x["adv"]), True),
    ])
    T["c"] = (d["cultures"], [cont_name.get(c, c) for c in CONTINENTS], lambda c: CONTINENTS.index(cul_cont[c["key"]]), [
        Col("cul", nw["c"], lambda c: nlink("c", c["key"]), lambda c: c["name"].casefold()),
        Col("group", nw["cg"], lambda c: nlink("cg", first_group(c)) if first_group(c) else "—",
            lambda c: grps[first_group(c)]["name"].casefold() if first_group(c) else "~"),
        Col("lang", 220, text(220, lambda c: c["lang"] or "—")),
        Col("adv", 120, lambda c: str(len(c["adv"])), lambda c: len(c["adv"]), True),
        Col("forms", 120, lambda c: str(len(c["forms"])), lambda c: len(c["forms"]), True),
        Col("st", 120, lambda c: str(len(c["st"])), lambda c: len(c["st"]), True),
    ])
    T["r"] = (d["religions"], u["rparts"], lambda r: religion_part(r["gk"]), [
        Col("rel", nw["r"], lambda r: nlink("r", r["key"]), lambda r: r["name"].casefold()),
        Col("group", nw["rg"], lambda r: nlink("rg", r["gk"]) if r["gk"] in rgrs else "—",
            lambda r: rgrs[r["gk"]]["name"].casefold() if r["gk"] in rgrs else "~"),
        Col("adv", 130, lambda r: str(len(r["adv"])), lambda r: len(r["adv"]), True),
        Col("forms", 130, lambda r: str(len(r["forms"])), lambda r: len(r["forms"]), True),
        Col("st", 130, lambda r: str(len(r["st"])), lambda r: len(r["st"]), True),
    ])

    loc, shape = {}, {}
    for t, (rows, parts, part_of, cols) in T.items():
        if t in NATIVE_TABS:
            continue
        name = cols[0].key
        by_part = [[r for r in rows if part_of(r) == p] for p in range(len(parts))]
        chunks = max((len(p) + CHUNK - 1) // CHUNK for p in by_part)
        for p, pname in enumerate(parts):
            loc[f"FMX_P_{t}_{p}"] = clean(pname)
            loc[f"FMX_P_{t}_{p}_on"] = "• " + clean(pname) + " •"
        for s, col in enumerate(cols):
            loc[f"FMX_H_{t}_{s}"] = u["h"][col.hk]
            if not col.key:
                continue
            labels = u["num"] if col.num else u["az"]
            loc[f"FMX_H_{t}_{s}_a"] = f"{u['h'][col.hk]} ({labels[0]})"
            loc[f"FMX_H_{t}_{s}_r"] = f"{u['h'][col.hk]} ({labels[1]})"
            for p, prow in enumerate(by_part):
                cells = [[c.cell(r) for c in cols] for r in prow]
                order = sorted(range(len(prow)), key=lambda n: name(prow[n]))
                order.sort(key=lambda n: col.key(prow[n]), reverse=col.num)
                for dkey, seq in ((("a", order), ("r", order[::-1])) if t in REVERSIBLE else (("a", order),)):
                    for ch in range(chunks):
                        part = seq[ch * CHUNK:(ch + 1) * CHUNK]
                        for ci in range(len(cols)):
                            loc[f"FMX_T_{t}_{p}_{s}_{dkey}_{ch}_{ci}"] = "\\n".join(cells[n][ci] for n in part)
        shape[t] = (len(parts), chunks, [(c.width, bool(c.key)) for c in cols])
    return loc, shape


# ---------------------------------------------------------------- localization

def build(lang, nw, idx, cul_cont):
    d = load(lang)
    u = dict(UI["english"], **UI.get(lang, {}))
    by_id = {i["id"]: i for i in d["items"]}
    fixed_by_tag = {x["tag"]: x for x in d["fixed"]}
    form_by_tag = {}
    for i in d["items"]:
        form_by_tag.setdefault(i["tag"], i)

    def nation(tag):
        if tag in fixed_by_tag:
            return f"[{ck('x', tag)}|e]"
        if tag in form_by_tag:
            return nlink("f", form_by_tag[tag]["id"])
        return tag

    def forms_line(ids, xc):
        forms = sorted((by_id[f] for f in ids if f in by_id), key=lambda f: -f["level"])
        if not forms:
            return ""
        return f"{u['forms']} ({len(forms)}): " + ", ".join(
            nlink("f", f["id"]) + f" ({u['tier']} {f['level']}{', ' + u['xc'] if xc and f.get('xc') else ''})" for f in forms)

    def start_line(tags):
        return f"{u['st']} ({len(tags)}): " + joined((nation(t) for t in tags), u, 20) if tags else ""

    concepts, loc = [], {}

    # extra blocks for the game's own tooltips
    # one block per formable; the variants of a tag get distinct names (see variant_names), so the tooltip can tell them apart
    for i in d["items"]:
        loc[f"FMX_FC_{i['id']}"] = block(u, formable_lines(i, d, u))
    for g in d["groups"]:
        advs = [d["cadv"][a] for a in g["adv"] if a in d["cadv"]]
        loc[f"FMX_CG_{g['key']}"] = block(u, ["\n".join(adv_lines(advs, u["gadv"])), unlock_lines(advs, u)])
    for c in d["cultures"]:
        advs = [d["cadv"][a] for a in c["adv"] if a in d["cadv"]]
        lines = ["\n".join(adv_lines(advs, u["cadv"])), unlock_lines(advs, u),
                 forms_line(c["forms"], True), start_line(c["st"])]
        if c["key"] in idx["c"]:
            n = idx["c"][c["key"]]
            loc[f"FMX_CU_{n}"] = block(u, lines)
            gks = [g for g in c["gk"] if g in d["grpByKey"]]
            loc[f"FMX_CGN_{n}"] = ", ".join(nlink("cg", g) for g in gks) or "—"
            loc[f"FMX_GI_{n}"] = clean(d["grpByKey"][gks[0]]["name"]) if gks else "~"
    for r in d["religions"]:
        if r["key"] in idx["r"]:
            loc[f"FMX_RE_{idx['r'][r['key']]}"] = block(u, [
                "\n".join(adv_lines([d["radv"][a] for a in r["adv"] if a in d["radv"]], u["radv"]))])
    for g in d["rgroups"]:
        if g["key"] in idx["rg"]:
            loc[f"FMX_RG_{idx['rg'][g['key']]}"] = block(u, ["\n".join(adv_lines([d["radv"][a] for a in g["adv"] if a in d["radv"]], u["gadv"]))])
    # every object the game may show gets a key, even an empty one, so no raw key ever shows up
    for kind, prefix in (("c", "FMX_CU_"), ("r", "FMX_RE_"), ("rg", "FMX_RG_")):
        for n in idx[kind].values():
            loc.setdefault(f"{prefix}{n}", "")

    # nations without a tier: hidden concepts
    for x in d["fixed"]:
        xn = idx["x"][x["tag"]]          # same number as fmx_x_index_value (english order), whatever this language sorts by
        L = [clean(u["notier"]),
             f"{x['tag']} · {u['rank']}: {clean(x['rank']) or u['none']} · {u['locs']}: {x['locs']}",
             f"{u['capital']}: {clean(x['cap'])}" + (f" ({native('ShowProvinceDefinitionName', x['capk'])})" if x.get("capk") else ""),
             f"{u['culture']}: " + (nlink("c", x["ck"]) if x.get("ck") in d["culByKey"] else clean(x["cul"])),
             f"{u['religion']}: " + (nlink("r", x["rk"]) if x.get("rk") in d["relByKey"] else clean(x["rel"])),
             f"{u['continent']}: " + (native("ShowContinentName", x["contk"]) if x.get("contk") else clean(x["cont"]))]
        L += adv_lines(x["adv"], u["adv"])
        if x.get("ref"):
            L.append(f"{u['ref']}: " + ", ".join(native("ShowGovernmentReformName", r["id"]) for r in x["ref"]))
        key = ck("x", x["tag"])
        concepts.append(key)
        loc[f"game_concept_{key}"] = clean(x["name"])
        loc[f"game_concept_{key}_desc"] = "\\n".join(L).replace("\n", "\\n")
        loc[f"FMX_XI_{xn}"] = f"[{key}|e]"     # the atlas card in the native list's tooltip

    tloc, shape = tables(d, u, nw, cul_cont)
    loc.update(tloc)
    loc["FMX_TITLE"] = u["title"]
    loc["FMX_OPEN"] = u["open"]
    loc["FMX_HINT"] = u["hint"]
    for m, name in u["tabs"].items():
        loc[f"FMX_TAB_{m.upper()}"] = name
        loc[f"FMX_TAB_{m.upper()}_on"] = "• " + name + " •"
    return concepts, loc, shape


# ---------------------------------------------------------------- GUI

GUI_WINDOW = r'''window = {
	name = "fmx_window"
	layer = top
	movable = yes
	resizable = no
	alwaystransparent = no
	filter_mouse = all
	parentanchor = center
	widgetanchor = center
	size = { WIDTH 900 }
	using = bg_window_default_alt
	allow_outside = yes
	visible = "[GetVariableSystem.Exists('fmx_open')]"

	vbox = {
		using = window_margin_alt
		spacing = 6

		window_header_alt = {
			blockoverride "header_text" {
				text = "FMX_TITLE"
			}
		}

		hbox = {
			layoutpolicy_horizontal = expanding
			spacing = 6
			margin = { 14 0 }
TABS
			expand = {}
		}

		text_single = {
			layoutpolicy_horizontal = expanding
			margin = { 14 0 }
			text = "FMX_HINT"
			default_format = "#low;italic"
		}
TABLES
	}

	widget = {
		parentanchor = right
		position = { -5 5 }
		size = { 40 40 }
		button_close_alt = {
			blockoverride "close_on_action" {
				on_action = "[GetVariableSystem.Clear('fmx_open')]"
			}
		}
	}
}
'''

MODES = ["f", "x", "c", "r"]
VS = "GetVariableSystem"


def tab_visible(m):
    if m == "f":
        return f"[Not(Or({VS}.Exists('fmx_tab_x'), Or({VS}.Exists('fmx_tab_c'), {VS}.Exists('fmx_tab_r'))))]"
    return f"[{VS}.Exists('fmx_tab_{m}')]"


def first_sort(cols):
    return next(s for s, (_, sortable) in enumerate(cols) if sortable)


def defaults(shape):
    """Sort and part variables start set when the window opens, so every loc key built from them exists."""
    out = []
    for t, (_, _, cols) in shape.items():
        for var, val in ((f"fmx_p_{t}", "0"), (f"fmx_s_{t}", str(first_sort(cols))), (f"fmx_d_{t}", "a")):
            out.append(f"onclick = \"[{VS}.SetIf('{var}', '{val}', Not({VS}.Exists('{var}')))]\"")
    return out


def table_gui(t, nparts, chunks, cols):
    pv, sv, dv = f"'fmx_p_{t}'", f"'fmx_s_{t}'", f"'fmx_d_{t}'"
    out = [f'\t\tvbox = {{\n\t\t\tvisible = "{tab_visible(t)}"\n\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\tlayoutpolicy_vertical = expanding\n\t\t\tspacing = 4']
    # parts: continents or religion families
    out.append("\t\t\thbox = {\n\t\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\t\tspacing = 4\n\t\t\t\tmargin = { 14 0 }")
    for p in range(nparts):
        on = f"{VS}.HasValue({pv}, '{p}')"
        out.append(f'\t\t\t\tbutton_regular = {{ size = {{ 210 30 }} visible = "[Not({on})]" text = "FMX_P_{t}_{p}" '
                   f"onclick = \"[{VS}.Set({pv}, '{p}')]\" }}")
        out.append(f'\t\t\t\tbutton_regular = {{ size = {{ 210 30 }} visible = "[{on}]" text = "FMX_P_{t}_{p}_on" }}')
    out.append("\t\t\t\texpand = {}")
    if t in NATIVE_ACTIONS:
        # the same list in the game's own window, with its own sorting, search and filters
        out.append("\t\t\t\t" + native_button(t))
    out.append("\t\t\t}")
    # header: an inactive column sets the sort; the active one flips the direction (small tables only)
    out.append("\t\t\thbox = {\n\t\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\t\tmargin = { 14 0 }")
    for s, (w, sortable) in enumerate(cols):
        if not sortable:
            out.append(f'\t\t\t\tbutton_regular = {{ size = {{ {w} 30 }} enabled = no text = "FMX_H_{t}_{s}" }}')
            continue
        active = f"{VS}.HasValue({sv}, '{s}')"
        rev = f"{VS}.HasValue({dv}, 'r')"
        out.append(f'\t\t\t\tbutton_regular = {{ size = {{ {w} 30 }} visible = "[Not({active})]" text = "FMX_H_{t}_{s}" '
                   f"onclick = \"[{VS}.Set({sv}, '{s}')]\" onclick = \"[{VS}.Set({dv}, 'a')]\" }}")
        flip = f"onclick = \"[{VS}.Set({dv}, 'r')]\" " if t in REVERSIBLE else ""
        out.append(f'\t\t\t\tbutton_regular = {{ size = {{ {w} 30 }} visible = "[And({active}, Not({rev}))]" text = "FMX_H_{t}_{s}_a" {flip}}}')
        if t in REVERSIBLE:
            out.append(f'\t\t\t\tbutton_regular = {{ size = {{ {w} 30 }} visible = "[And({active}, {rev})]" text = "FMX_H_{t}_{s}_r" '
                       f"onclick = \"[{VS}.Set({dv}, 'a')]\" }}")
    out.append("\t\t\t\texpand = {}\n\t\t\t}")
    out.append("\t\t\tscrollbox = {\n\t\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\t\tlayoutpolicy_vertical = expanding\n"
               "\t\t\t\tblockoverride \"scrollbox_content\" {\n\t\t\t\t\tvbox = {\n\t\t\t\t\t\tlayoutpolicy_horizontal = expanding")
    for ch in range(chunks):
        out.append("\t\t\t\t\t\thbox = {\n\t\t\t\t\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\t\t\t\t\tmargin = { 14 0 }")
        for ci, (w, _) in enumerate(cols):
            key = (f"Concatenate('FMX_T_{t}_', Concatenate({VS}.Get({pv}), Concatenate('_', Concatenate({VS}.Get({sv}), "
                   f"Concatenate('_', Concatenate({VS}.Get({dv}), '_{ch}_{ci}'))))))")
            out.append(f"\t\t\t\t\t\t\ttext_multi = {{ min_width = {w} max_width = {w} autoresize = yes margin = {{ 7 0 }} "
                       f"text = \"[Localize({key})]\" }}")
        out.append("\t\t\t\t\t\t\texpand = {}\n\t\t\t\t\t\t}")
    out.append("\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}\n\t\t}")
    return "\n".join(out)


NATIVE_ACTIONS = {"f": "fmx_atlas_formables", "x": "fmx_atlas_notier", "c": "fmx_atlas_cultures", "r": "fmx_atlas_religions"}


def native_button(t, width=240):
    return (f'button_regular = {{ size = {{ {width} 30 }} text = "FMX_NATIVE_{t.upper()}" datacontext = "[GetGenericAction(\'{NATIVE_ACTIONS[t]}\')]" '
            f"onclick = \"[{VS}.Clear('fmx_open')]\" onclick = \"[PerformGenericAction(GenericAction.Self)]\" }}")


def native_tab_gui(t):
    """A tab whose list is the game's own selection list: one button opens it."""
    return (f'\t\tvbox = {{\n\t\t\tvisible = "{tab_visible(t)}"\n\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\tlayoutpolicy_vertical = expanding\n'
            f'\t\t\tmargin = {{ 14 20 }}\n\t\t\tspacing = 10\n\t\t\ttext_single = {{ text = "FMX_NATIVE_HINT" default_format = "#low;italic" }}\n'
            f"\t\t\t{native_button(t, 400)}\n\t\t\texpand = {{}}\n\t\t}}")


def gui_window(shape):
    for t, (_, _, cols) in shape.items():
        total = sum(w for w, _ in cols) + 28
        assert total <= WINDOW_W - 40, f"table {t} is {total}px wide"
    tabs = []
    for m in MODES:
        on = tab_visible(m)[1:-1]
        clear = " ".join(f"onclick = \"[{VS}.Clear('fmx_tab_{o}')]\"" for o in MODES if o != m)
        set_ = f"onclick = \"[{VS}.Set('fmx_tab_{m}', 'yes')]\" " if m != "f" else ""
        tabs.append(f'\t\t\tbutton_regular = {{ size = {{ 200 32 }} visible = "[Not({on})]" text = "FMX_TAB_{m.upper()}" {set_}{clear} }}')
        tabs.append(f'\t\t\tbutton_regular = {{ size = {{ 200 32 }} visible = "[{on}]" text = "FMX_TAB_{m.upper()}_on" }}')
    tables_gui = "\n".join(table_gui(t, *shape[t]) if t in shape else native_tab_gui(t) for t in MODES)
    return GUI_WINDOW.replace("WIDTH", str(WINDOW_W)).replace("TABS", "\n".join(tabs)).replace("TABLES", tables_gui)


def form_panel_override(shape):
    src = open(G + "in_game/gui/form_new_country.gui", encoding="utf-8-sig").read().replace("\r", "")
    anchor = '''		header_main_tabs = {
			blockoverride "content" {
				using = content_main_tabs
			}
		}
'''
    assert anchor in src, "form_new_country.gui changed: update the anchor"
    # Formables Atlas: one button per list, each opening the game's own list straight away
    buttons = "\n".join(
        f'\t\t\tbutton_regular = {{ layoutpolicy_horizontal = expanding size = {{ -1 28 }} text = "FMX_NATIVE_{t.upper()}" '
        f'datacontext = "[GetGenericAction(\'{NATIVE_ACTIONS[t]}\')]" onclick = "[PerformGenericAction(GenericAction.Self)]" }}'
        for t in MODES)
    block = anchor + f"\n\t\t# Formables Atlas\n\t\thbox = {{\n\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\tspacing = 4\n{buttons}\n\t\t}}\n"
    return src.replace(anchor, block)


BLOCK_W = 820     # our tooltip blocks are wider than the game's text blocks, so long lists take fewer lines
WIDE = f'blockoverride "tooltip_minimumsize" {{ minimumsize = {{ {BLOCK_W} -1 }} }}'
SCROLL = 'blockoverride "block_scrollarea" { maximumsize = { -1 160 } }'     # long blocks scroll instead of running off the screen


def atlas_block(indent, prefix, getter):
    text = f"Localize(Concatenate('{prefix}', {getter}))"
    i = "\t" * indent
    return (f"{i}# Formables Atlas\n{i}TooltipScrolledTextBlock = {{\n{i}\tvisible = \"[Not(StringIsEmpty({text}))]\"\n{i}\t{WIDE}\n{i}\t{SCROLL}\n"
            f"{i}\tblockoverride \"text\" {{\n{i}\t\ttext = \"[{text}]\"\n{i}\t\tmax_width = {BLOCK_W} fontsize = 15\n{i}\t}}\n{i}}}\n")


def formable_variants(items):
    out = {}
    for i in items:
        out.setdefault(i["tag"], []).append(i)
    return out


VARIANT_MARKS = {   # the distinguishing part of a variant's id -> its mark ("$TRE$" is the game's own name of Trebizond)
    "trebizond": {"": "$TRE$"},
    "high_kingship": {"": "High Kingship", "russian": "верховное королевство"},
    "lordship_of_ireland": {"": "Lordship", "russian": "сеньория"},
    "REDUCED_REQUIREMENTS": {"": "Reduced Requirements", "russian": "упрощённые требования"},
}


def variant_names(items, lang):
    """The game names every variant of a formable like the first one (ROM_BYZ_f: "$ROM_f$"); the later variants get
    a mark in brackets, e.g. "Roman Empire (BYZ)", so they can be told apart everywhere."""
    import pdx
    game = pdx.load_loc([G + "main_menu/localization/english"])
    out = {}
    for tag, variants in formable_variants(items).items():
        for i in variants[1:]:
            if game.get(i["id"], "").strip() != f"${variants[0]['id']}$":
                continue                # a formable of its own that only shares the tag (Rum and the Ottomans)
            part = i["id"][len(tag) + 1:].removesuffix("_f")
            marks = VARIANT_MARKS.get(part)
            part = (marks.get(lang) or marks[""]) if marks else part if part.isupper() and len(part) <= 4 else part.replace("_", " ").title()
            out[i["id"]] = f"${variants[0]['id']}$ ({part})"
    return out


def formable_blocks(indent, groups):
    """One scrollable block per formable tag, shown when the tooltip's formable has the name of one of its variants."""
    i = "\t" * indent
    out = [f"{i}# Formables Atlas"]
    for tag, ids in groups.items():
        tests = [f"EqualTo_string(FormableCountry.GetNameWithNoTooltip, Localize('{k}'))" for k in ids]
        cond = tests[-1]
        for t in reversed(tests[:-1]):          # Or() takes two arguments
            cond = f"Or({t}, {cond})"
        out.append(f"{i}TooltipScrolledTextBlock = {{ visible = \"[{cond}]\" {WIDE} blockoverride \"block_scrollarea\" {{ maximumsize = {{ -1 420 }} }} "
                   f"blockoverride \"text\" {{ text = \"FMX_FC_{tag}\" max_width = {BLOCK_W} fontsize = 15 }} }}")
    return "\n".join(out) + "\n"


def matched_blocks(indent, obj, keys, prefix):
    """One block per object, shown when the tooltip's object has that object's name (these types have no key getter)."""
    i = "\t" * indent
    return f"{i}# Formables Atlas\n" + "".join(
        f"{i}TooltipScrolledTextBlock = {{ visible = \"[EqualTo_string({obj}.GetNameWithNoTooltip, Localize('{k}'))]\" {WIDE} {SCROLL} "
        f"blockoverride \"text\" {{ text = \"{prefix}{k}\" max_width = {BLOCK_W} fontsize = 15 }} }}\n" for k in keys)


def insert_in_template(src, template, anchor, text):
    """Puts text before the line holding `anchor`, inside `template`."""
    start = src.index(f"template {template} {{")
    at = src.index(anchor, start)
    at = src.rindex("\n", 0, at) + 1
    return src[:at] + text + src[at:]


def template_text(src, template):
    """The whole top-level `template <name> { ... }` block."""
    start = src.index(f"template {template} {{")
    depth = 0
    for at in range(src.index("{", start), len(src)):
        depth += {"{": 1, "}": -1}.get(src[at], 0)
        if depth == 0:
            return src[start:at + 1] + "\n"


def tooltip_overrides(formables, groups):
    """Only the templates the atlas changes, in files of its own: a template is replaced by name, so the rest of the
    game's tooltip files stays with whatever loads them (Glorp UI's CountryTooltip, for one), in any load order."""
    files = {}
    src = open(G + "in_game/gui/shared/country_tooltips.gui", encoding="utf-8-sig").read().replace("\r", "")
    src = insert_in_template(src, "formablecountry_info", "TooltipScrolledRowList = {", formable_blocks(1, formables))
    files["fmx_country_tooltips.gui"] = template_text(src, "formablecountry_info")

    src = open(G + "in_game/gui/shared/society_tooltips.gui", encoding="utf-8-sig").read().replace("\r", "")
    src = insert_in_template(src, "culture_group_tooltip", "TooltipFlavorTextBlock = {", matched_blocks(3, "CultureGroup", groups, "FMX_CG_"))
    start = src.index("template culture_tooltip {")
    anchor = src.index("using = culture_tooltip_content", start)
    close = src.index("}\n", anchor) + 2               # end of the TooltipContentSection
    src = src[:close] + atlas_block(3, "FMX_CU_", "Culture.GetKey") + src[close:]
    files["fmx_society_tooltips.gui"] = template_text(src, "culture_group_tooltip") + "\n" + template_text(src, "culture_tooltip")

    src = open(G + "in_game/gui/shared/religion_tooltips.gui", encoding="utf-8-sig").read().replace("\r", "")
    src = insert_in_template(src, "religion_tooltip", "TooltipFlavorTextBlock = {", atlas_block(3, "FMX_RE_", "Religion.GetKey"))
    src = insert_in_template(src, "religion_group_tooltip", "TooltipFlavorTextBlock = {", atlas_block(3, "FMX_RG_", "ReligionGroup.GetKey"))
    files["fmx_religion_tooltips.gui"] = template_text(src, "religion_tooltip") + "\n" + template_text(src, "religion_group_tooltip")
    return files


def murmur3(text):
    """MurmurHash3 x86 32-bit, seed 0: the hash the game files localization keys under."""
    data = text.encode("utf-8")
    h, n = 0, len(data) // 4
    def mix(k):
        k = (k * 0xcc9e2d51) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        return (k * 0x1b873593) & 0xffffffff
    for i in range(n):
        h ^= mix(int.from_bytes(data[4 * i:4 * i + 4], "little"))
        h = ((h << 13) | (h >> 19)) & 0xffffffff
        h = (h * 5 + 0xe6546b64) & 0xffffffff
    tail = data[4 * n:]
    if tail:
        h ^= mix(int.from_bytes(tail, "little"))
    h ^= len(data)
    h ^= h >> 16
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= h >> 13
    h = (h * 0xc2b2ae35) & 0xffffffff
    return h ^ (h >> 16)


def check_key_hashes(keys):
    """Stops the build when a key of ours shares its hash with a game key or another of ours: the game then shows one
    key's text for the other (FMX_XL_714 took the name of the NTR tag)."""
    game = {}
    for root, _, names in os.walk(G + "main_menu/localization/english"):
        for name in names:
            if name.endswith(".yml"):
                for line in open(os.path.join(root, name), encoding="utf-8-sig", errors="replace"):
                    m = re.match(r"\s+([A-Za-z0-9_.\-']+):\d*\s", line)
                    if m:
                        game.setdefault(murmur3(m.group(1)), m.group(1))
    seen, clashes = {}, []
    for key in keys:
        h = murmur3(key)
        other = seen.get(h) or (game.get(h) if game.get(h) != key else None)
        if other:
            clashes.append(f"{key} / {other}")
        seen[h] = key
    if clashes:
        raise SystemExit("localization key hash collisions: " + ", ".join(clashes))


def write(path, text, bom=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="\n") as fh:
        fh.write(text)


REL_FAMILY_KEYS = ["christian", "near_east", "eastern", "folk_old", "folk_new"]
NATIVE_TABS = {"f", "x", "c", "r"}     # every tab opens the game's own list (sortable, searchable, filterable)


# ---------------------------------------------------------------- Journal: extra columns in the Religions and Cultures tabs

LEDGER_COLS = [("ADV", "Улучшения", "Advances"), ("FORMS", "Формаблы", "Formables"), ("ST", "На старте", "At start")]


def ledger_cells(indent, values, obj):
    """Journal cells showing the script values the atlas lists sort by (see native_lists)."""
    i = "\t" * indent
    return "".join(
        f"\n{i}text_single = {{\n{i}\tusing = layoutpolicy_expanding\n{i}\tlayoutstretchfactor_horizontal = 1\n{i}\tautoresize = no\n"
        f"{i}\talign = left|nobaseline\n{i}\ttext = \"[{obj}.MakeScope.ScriptValue('{v}')|0]\"\n{i}}}\n" for v in values)


def ledger_headers(indent):
    i = "\t" * indent
    return "".join(
        f"{i}text_single = {{ using = layoutpolicy_expanding autoresize = no align = left|nobaseline margin_left = 10 "
        f"default_format = \"#subtle_name\" text = \"FMX_COL_{k}\" }}\n" for k, _, _ in LEDGER_COLS)


def ledger_overrides():
    files = {}
    src = open(G + "in_game/gui/religions_ledger.gui", encoding="utf-8-sig").read().replace("\r", "")
    anchor = "\t\t\t\t\t\twidget = { size = { 20 -1 } layoutpolicy_vertical = expanding }\n"
    assert src.count(anchor) == 1, "religions_ledger.gui changed"
    src = src.replace(anchor, ledger_headers(6) + anchor)
    anchor = 'sort_by_highlight = { name = "countries" }\n\t\t\t\t\t\t\t\t\t\t}\n'
    assert src.count(anchor) == 1, "religions_ledger.gui changed"
    src = src.replace(anchor, anchor + ledger_cells(10, ["fmx_rel_adv_value", "fmx_rel_forms_value", "fmx_rel_st_value"], "ReligionItem.GetReligion"))
    files["religions_ledger.gui"] = src

    src = open(G + "in_game/gui/cultures_ledger.gui", encoding="utf-8-sig").read().replace("\r", "")
    at = src.index('name = "country"')
    at = src.rindex("\n", 0, src.rindex("sort_by_key_button", 0, at)) + 1
    src = src[:at] + ledger_headers(6) + src[at:]
    at = src.index("country_flag_small = {", src.index("CultureItem.GetCulture.GetTradition"))
    at = src.rindex("\n", 0, at) + 1
    src = src[:at] + ledger_cells(10, ["fmx_cul_adv_value", "fmx_cul_forms_value", "fmx_cul_st_value"], "CultureItem.GetCulture") + src[at:]
    files["cultures_ledger.gui"] = src
    return files


def ledger_loc(lang, d, idx):
    loc = {f"FMX_COL_{k}": ru if lang == "russian" else en for k, ru, en in LEDGER_COLS}
    return loc


def main():
    # Culture.GetKey and Religion.GetKey give the load index; ReligionGroup.GetKey gives the key itself
    idx = {"c": top_level_keys("in_game/common/cultures"), "r": top_level_keys("in_game/common/religions"),
           "rg": {k: k for k in top_level_keys("in_game/common/religion_groups")}}
    cul_cont = culture_continents()
    datas = {lang: load(lang) for lang in LANGS}
    idx["x"] = {x["tag"]: n + 1 for n, x in enumerate(datas["english"]["fixed"])}   # the order of fmx_x_index_value
    nw = name_widths(datas.values())
    # the few cultures nobody speaks at the start take the continent of their group
    d = datas["english"]
    for c in d["cultures"]:
        if c["key"] not in cul_cont:
            mates = collections.Counter(cul_cont[o] for g in c["gk"] for o in d["grpByKey"].get(g, {}).get("cultures", []) if o in cul_cont)
            cul_cont[c["key"]] = mates.most_common(1)[0][0] if mates else "europe"
    native = native_lists.lists(d, idx, cul_cont, religion_part, REL_FAMILY_KEYS)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)              # everything in the mod folder is generated
    all_concepts = shape = None
    for lang in LANGS:
        concepts, loc, sh = build(lang, nw, idx, cul_cont)
        dl = datas[lang]
        cont_name = {r["contk"]: r["cont"] for r in dl["items"] + dl["fixed"] if r.get("contk")}
        conts = [cont_name.get(c, c) for c in CONTINENTS]
        loc.update(ledger_loc(lang, dl, idx))
        u = dict(UI["english"], **UI.get(lang, {}))
        event = next((i["cont"] for i in dl["items"] if i["event"]), "—")
        f_names = (conts + [event] + [f"{u['tier']} {ROMAN[n]}" for n in range(1, 6)]
                   + [u["rules"][r].capitalize() for r in ("historical", "plausible", "fantasy")])
        loc.update(native_lists.loc(lang, native, {"r": u["rparts"], "c": conts, "x": conts, "f": f_names}))
        all_concepts = all_concepts or concepts
        shape = shape or sh
        lines = [f"l_{lang}:"] + [f' {k}: "{v}"' for k, v in loc.items()]
        write(os.path.join(OUT, "main_menu", "localization", lang, f"fmx_l_{lang}.yml"), "\n".join(lines) + "\n", bom=True)
        write(os.path.join(OUT, "main_menu", "localization", lang, "replace", f"fmx_replace_l_{lang}.yml"),
              "\n".join([f"l_{lang}:"] + [f' {k}: "{v}"' for k, v in variant_names(d["items"], lang).items()]) + "\n", bom=True)
        if lang == "english":           # the keys are the same in every language
            check_key_hashes(list(loc) + list(variant_names(d["items"], lang)))
        print(f"{lang:13} {len(loc)} loc entries")
    write(os.path.join(OUT, "in_game", "common", "game_concepts", "fmx_concepts.txt"),
          "\n".join(f"{c} = {{\n\ttexture = \"modifiers/_default\"\n\tshown_in_encyclopedia = no\n}}" for c in all_concepts) + "\n", bom=True)
    write(os.path.join(OUT, "in_game", "gui", "form_new_country.gui"), form_panel_override(shape))
    for name, text in tooltip_overrides({i["id"]: [i["id"]] for i in d["items"]}, [g["key"] for g in d["groups"] if g["adv"]]).items():
        write(os.path.join(OUT, "in_game", "gui", "shared", name), text)
    for name, text in ledger_overrides().items():
        write(os.path.join(OUT, "in_game", "gui", name), text)
    for path, text in native_lists.files(G, native).items():
        target = os.path.normpath(os.path.join(OUT, *path.split("/")))
        if isinstance(text, tuple):         # a game file copied as is (header icons)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(text[1], target)
        else:
            write(target, text, bom=path.endswith(".txt"))
    meta = {"name": "Formables Atlas [LOCAL]", "id": "grackbox.formables_atlas", "version": "1.0.2", "game_id": "eu5",
            "supported_game_version": "1.4.*", "short_description": "In-game atlas of formable nations, cultures and religions.",
            "tags": ["Utilities", "User Interface", "1.4"], "relationships": [], "game_custom_data": {}}
    write(os.path.join(OUT, ".metadata", "metadata.json"), json.dumps(meta, indent=4, ensure_ascii=False) + "\n", bom=True)
    shutil.copyfile(os.path.join(HERE, "cover.png"), os.path.join(OUT, ".metadata", "thumbnail.png"))   # the launcher's picture
    print("concepts:", len(all_concepts), "shape:", {t: s[:2] for t, s in shape.items()}, "->", OUT)


if __name__ == "__main__":
    main()
