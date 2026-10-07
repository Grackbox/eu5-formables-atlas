"""Minimal Clausewitz/Jomini script parser and localization loader."""
import os
import re

TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[<>!?]=|[={}<>]|[^\s={}<>"#]+|#[^\n]*')


def tokenize(text):
    for m in TOKEN.finditer(text):
        tok = m.group(0)
        if tok.startswith('#'):
            continue
        yield tok


def parse(text):
    """Return a block: list of (key, op, value); bare values are (None, None, value).
    value is a str or a nested block (list)."""
    toks = list(tokenize(text.lstrip('﻿')))
    pos = 0

    def block():
        nonlocal pos
        items = []
        while pos < len(toks):
            t = toks[pos]
            if t == '}':
                pos += 1
                return items
            if t == '{':
                pos += 1
                items.append((None, None, block()))
                continue
            nxt = toks[pos + 1] if pos + 1 < len(toks) else None
            if nxt in ('=', '<', '>', '<=', '>=', '!=', '?='):
                key, op = t, nxt
                pos += 2
                v = toks[pos]
                if v == '{':
                    pos += 1
                    items.append((key, op, block()))
                else:
                    pos += 1
                    # typed values such as rgb { ... } / hsv360 { ... }
                    if pos < len(toks) and toks[pos] == '{' and re.fullmatch(r'(rgb|hsv|hsv360|hsv_raw)', v):
                        pos += 1
                        items.append((key, op, (v, block())))
                    else:
                        items.append((key, op, v.strip('"')))
            else:
                pos += 1
                items.append((None, None, t.strip('"')))
        return items

    return block()


def get(block, key, default=None):
    for k, _, v in block:
        if k == key:
            return v
    return default


def get_all(block, key):
    return [v for k, _, v in block if k == key]


LOC_LINE = re.compile(r'^\s*([^\s:#][^:]*?):\d*\s*"(.*)"\s*(?:#.*)?$')


def load_loc(dirs):
    loc = {}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if not f.endswith('.yml'):
                    continue
                with open(os.path.join(root, f), encoding='utf-8-sig', errors='ignore') as fh:
                    for line in fh:
                        m = LOC_LINE.match(line)
                        if m and m.group(1) not in loc:
                            loc[m.group(1)] = m.group(2)
    return loc


def clean(s, loc, depth=0):
    """Resolve $refs$ and strip formatting markup."""
    if s is None:
        return None
    if depth < 3:
        s = re.sub(r'\$([A-Za-z0-9_\.]+)\$', lambda m: clean(loc.get(m.group(1), m.group(1)), loc, depth + 1), s)
    s = re.sub(r"@\[[^\]]*\]!", "", s)  # inline flags/icons
    s = re.sub(r"\[Concept\('[^']*',\s*'([^']*)'\)\|?\w*\]", r"\1", s)
    s = re.sub(r"\[GetCountry\('(\w+)'\)\.Custom\('CL_ACC'\)\|?\w*\]",
               lambda m: clean(loc.get(m.group(1) + "_RU_ACC_CL") or loc.get(m.group(1), m.group(1)), loc, depth + 1), s)
    # [ShowAreaName('balearics_area')], [ShowScriptedGeographyNameWithNoTooltip('x')], ... -> localized name
    s = re.sub(r"\[Show\w*?Name(?:WithNoTooltip)?\('([\w.]+)'\)\|?\w*\]",
               lambda m: clean(loc.get(m.group(1), m.group(1).replace("_", " ")), loc, depth + 1), s)
    # [GetCountry('MLL').GetAdjective] / .GetName... / .GetLongName...
    s = re.sub(r"\[GetCountry\('(\w+)'\)\.(GetAdjective|Get\w*Name\w*)\|?\w*\]",
               lambda m: clean(loc.get(m.group(1) + ("_ADJ" if m.group(2) == "GetAdjective" else ""), m.group(1)), loc, depth + 1), s)
    # [GetUniqueInternationalOrganization('x').GetName], [GetReligion('x').GetAdjective], ... -> localized key
    s = re.sub(r"\[Get\w+\('(\w+)'\)\.Get(Name|Adjective|LongName)\w*\|?\w*\]",
               lambda m: clean(loc.get(m.group(1) + ("_ADJ" if m.group(2) == "Adjective" and m.group(1) + "_ADJ" in loc else ""),
                                       m.group(1).replace("_", " ")), loc, depth + 1), s)
    # [capital|e] -> the game concept's name
    s = re.sub(r"\[(\w+)\|[eE]\w*\]",
               lambda m: clean(loc.get("game_concept_" + m.group(1)) or loc.get(m.group(1), m.group(1).replace("_", " ")), loc, depth + 1), s)
    s = re.sub(r"#ONCLICK:\S*\s?", "", s)
    s = re.sub(r"#TOOLTIP:[^,]*,[^,]*,X\s?", "", s)
    s = re.sub(r'#[A-Za-z_]+(?:;[A-Za-z_]+)* ?', '', s)
    s = s.replace('#!', '').replace('\\n', ' ').replace('�', '')  # one broken character in the game's braz_por text
    s = re.sub(r'@[A-Za-z_]+!', '', s)
    s = re.sub(r'\[[^\]]*\]', '…', s)
    return re.sub(r'\s+', ' ', s).strip()
