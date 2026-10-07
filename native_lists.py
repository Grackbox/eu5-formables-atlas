"""The game's own selection lists (sortable, searchable, filterable) for religions, cultures and nations without a tier.

Each list is a generic action that does nothing, with a select_trigger over every object of the type. The atlas adds
columns (attribute_columns + their widgets) whose numbers come from the site data: shown through loc keys keyed by the
object's key, sorted through script values. Continent/family filters are added to the game's scripted filters.
"""

import re

RU = "russian"


class Col:
    def __init__(self, key, width, kind, ru, en, tt_ru, tt_en, icon, show=None, sort=None, prefix=None, count=None):
        self.key, self.width, self.kind = key, width, kind
        self.ru, self.en, self.tt_ru, self.tt_en, self.icon = ru, en, tt_ru, tt_en, icon
        self.show, self.sort, self.prefix, self.count = show, sort, prefix, count


def lists(d, idx, cul_cont, religion_part, fam_keys):
    by_id = {i["id"] for i in d["items"]}
    fixed = d["fixed"]
    groups = sorted({r["gk"] for r in d["religions"]})
    L = {}
    L["r"] = {
        "action": "fmx_atlas_religions", "type": "religion", "target": "InteractionTarget.GetReligion",
        "cols_file": "17_religion.txt", "filters_file": "17_religion.txt",
        "default_filter": "religion_religious_present_in_country", "filter_tag": "religion",
        "visible": None, "cond": "this = religion:{k}", "objects": d["religions"], "okey": lambda r: r["key"],
        "name": ("Атлас: религии", "Atlas: religions"),
        "cols": [
            Col("fmx_rel_group", 150, "text", "Группа", "Group", "Сортировать по религиозной группе", "Sort by religion group", "group",
                show="[InteractionTarget.GetReligion.GetGroup.GetName]", sort="[ROOT.GetReligion.GetGroup.GetNameWithNoTooltip]"),
            Col("fmx_rel_adv", 60, "sv", "Улучшения", "Advances", "Сортировать по числу религиозных улучшений",
                "Sort by the number of religious advances", "unique_content", prefix="FMX_RA_", count=lambda r: len(r["adv"])),
            Col("fmx_rel_forms", 60, "sv", "Формаблы", "Formables", "Сортировать по числу формаблов, доступных этой религии",
                "Sort by the number of formables open to this religion", "countries", prefix="FMX_RF_",
                count=lambda r: len([f for f in r["forms"] if f in by_id])),
            Col("fmx_rel_st", 60, "sv", "На старте", "At start", "Сортировать по числу стран этой религии на старте 1337 года",
                "Sort by the number of nations of this religion at the 1337 start", "start_date", prefix="FMX_RS_", count=lambda r: len(r["st"])),
        ],
        "filters": [(f"fmx_religion_family_{fam}", 0, "\n".join(f"\t\t\troot.group = religion_group:{g}" for g in groups if religion_part(g) == n))
                    for n, fam in enumerate(fam_keys)],
        "key_of": lambda r: idx["r"].get(r["key"]),
    }
    L["c"] = {
        "action": "fmx_atlas_cultures", "type": "culture", "target": "InteractionTarget.GetCulture",
        "cols_file": "16_culture.txt", "filters_file": "16_culture.txt", "name_w": 170,
        "default_filter": "culture_present_in_country", "filter_tag": "culture",
        "visible": None, "cond": "this = culture:{k}", "objects": d["cultures"], "okey": lambda c: c["key"],
        "name": ("Атлас: культуры", "Atlas: cultures"),
        "cols": [
            # the GUI has no getter for a culture's groups, so their links come from loc keyed by the culture's index
            Col("fmx_cul_group", 130, "text", "Группа", "Group", "Сортировать по культурной группе", "Sort by culture group", "group",
                show="[Localize(Concatenate('FMX_CGN_', InteractionTarget.GetCulture.GetKey))]",
                sort="[Localize(Concatenate('FMX_GI_', ROOT.GetCulture.GetKey))]"),
            Col("fmx_cul_lang", 100, "text", "Язык", "Language", "Сортировать по языку", "Sort by language", "language",
                show="[InteractionTarget.GetCulture.GetLanguage.GetName]", sort="[ROOT.GetCulture.GetLanguage.GetNameWithNoTooltip]"),
            Col("fmx_cul_adv", 50, "sv", "Улучшения", "Advances", "Сортировать по числу культурных улучшений",
                "Sort by the number of culture advances", "unique_content", prefix="FMX_CA_", count=lambda c: len(c["adv"])),
            Col("fmx_cul_forms", 50, "sv", "Формаблы", "Formables", "Сортировать по числу формаблов, доступных этой культуре",
                "Sort by the number of formables open to this culture", "countries", prefix="FMX_CF_",
                count=lambda c: len([f for f in c["forms"] if f in by_id])),
            Col("fmx_cul_st", 50, "sv", "На старте", "At start", "Сортировать по числу стран этой культуры на старте 1337 года",
                "Sort by the number of nations of this culture at the 1337 start", "start_date", prefix="FMX_CS_", count=lambda c: len(c["st"])),
        ],
        "filters": [(f"fmx_culture_{cont}", 0, "\n".join(f"\t\t\troot = culture:{c['key']}" for c in d["cultures"] if cul_cont[c["key"]] == cont))
                    for n, cont in enumerate(["europe", "asia", "africa", "america", "oceania"])],
        "key_of": lambda c: idx["c"].get(c["key"]),
    }
    items = d["items"]
    rule_n = {"historical": 1, "plausible": 2, "fantasy": 3}
    L["f"] = {
        "action": "fmx_atlas_formables", "type": "formable_country", "target": "InteractionTarget.GetFormableCountry",
        "cols_file": "60_formable_country.txt", "filters_file": None,
        "default_filter": None, "filter_tag": None,
        "visible": None, "cond": "this = formable_country:{k}", "objects": items, "okey": lambda i: i["id"],
        "name": ("Атлас: формируемые", "Atlas: formables"),
        "cols": [
            Col("fmx_f_tier", 70, "sv", "Тир", "Tier", "Сортировать по тиру", "Sort by tier", "rank", count=lambda i: i["level"]),
            Col("fmx_f_need", 90, "sv", "Локаций", "Locations", "Сортировать по числу нужных локаций", "Sort by the number of locations needed",
                "location", count=lambda i: 0 if i["event"] else i["need"]),
            Col("fmx_f_adv", 80, "sv", "Улучшения", "Advances", "Сортировать по числу улучшений", "Sort by the number of advances",
                "unique_content", count=lambda i: len(i["adv"])),
            Col("fmx_f_ref", 80, "sv", "Принципы", "Principles", "Сортировать по числу уникальных государственных принципов",
                "Sort by the number of unique state principles", "type", count=lambda i: len(i.get("ref") or [])),
        ],
        "filters": [(f"fmx_formable_{cont}", 0, "\n".join(f"\t\t\troot = formable_country:{i['id']}" for i in items
                                                         if (cont == "event" and i["event"]) or (not i["event"] and i.get("contk") == cont)))
                    for cont in ["europe", "asia", "africa", "america", "oceania", "event"]]
                   + [(f"fmx_formable_tier_{n}", 1, "\n".join(f"\t\t\troot = formable_country:{i['id']}" for i in items if i["level"] == n))
                      for n in range(1, 6)]
                   + [(f"fmx_formable_rule_{r}", 2, "\n".join(f"\t\t\troot = formable_country:{i['id']}" for i in items if i["rule"] == r))
                      for r in rule_n],
        "key_of": lambda i: i["id"],
    }
    L["x"] = {
        "action": "fmx_atlas_notier", "type": "country", "target": "InteractionTarget.GetCountry",
        "cols_file": "06_country.txt", "filters_file": "06_country.txt",
        "default_filter": "country_only_within_diplomatic_range", "filter_tag": "diplomacy",
        "visible": "\n".join(f"\t\t\t\ttag = {x['tag']}" for x in fixed), "cond": "tag = {k}", "objects": fixed, "okey": lambda x: x["tag"],
        "name": ("Атлас: страны без тира", "Atlas: nations without a tier"),
        "cols": [
            Col("fmx_x_cul", 130, "text", "Культура", "Culture", "Сортировать по культуре", "Sort by culture", "culture",
                show="[InteractionTarget.GetCountry.GetCulture.GetName]", sort="[ROOT.GetCountry.GetCulture.GetNameWithNoTooltip]"),
            Col("fmx_x_rel", 130, "text", "Религия", "Religion", "Сортировать по религии", "Sort by religion", "religion",
                show="[InteractionTarget.GetCountry.GetReligion.GetName]", sort="[ROOT.GetCountry.GetReligion.GetNameWithNoTooltip]"),
            Col("fmx_x_adv", 70, "sv", "Улучшения", "Advances", "Сортировать по числу уникальных страновых улучшений",
                "Sort by the number of unique country advances", "unique_content", prefix="FMX_XA_", count=lambda x: len(x["adv"])),
            Col("fmx_x_ref", 70, "sv", "Принципы", "Principles", "Сортировать по числу уникальных государственных принципов",
                "Sort by the number of unique state principles", "type", prefix="FMX_XR_", count=lambda x: len(x.get("ref") or [])),
        ],
        "filters": [(f"fmx_notier_{cont}", 0, "\t\t\tscope:target = {\n\t\t\t\tOR = {\n" + "\n".join(
            f"\t\t\t\t\ttag = {x['tag']}" for x in fixed if x.get("contk") == cont) + "\n\t\t\t\t}\n\t\t\t}")
                    for n, cont in enumerate(["europe", "asia", "africa", "america", "oceania"])],
        "key_of": lambda x: x["tag"],
        "loc_key": ".GetTag",
    }
    return L


FLAG_OF_FORMABLE = '''			country_flag = {
				size = { 40 27 }
				blockoverride "tooltip" { tooltip_enabled = no tagtooltip_enabled = no }
				blockoverride "contextmenu" { contextmenu_enabled = no }
				blockoverride "flag" {
					datacontext = "[InteractionTarget.GetFormableCountry.GetOrCreateCoatOfArms(Player.Self)]"
					texture = "[CoatOfArmsWrapper.GetTexture('(int32)144','(int32)96')]"
					frame = "[CoatOfArmsWrapper.GetFrame('(int32)144','(int32)96')]"
					framesize = "[CoatOfArmsWrapper.GetFrameSizeOrFallback('(int32)144','(int32)96','(float)0.5')]"
					texture_density = 2
				}
				blockoverride "click" {}
				blockoverride "double_click" {}
				blockoverride "hover" {}
			}
'''

# Our own name column for each list: the game's name cells show the action's tooltip ("X - select"); ours open the
# object's own tooltip (with the atlas block), so the list can be browsed by hovering.
NAME_COLS = {
    "formable_country": ("SORT_TEXT_FORMABLE_COUNTRY_NAME", "[InteractionTarget.GetFormableCountry.GetName]",
                         FLAG_OF_FORMABLE, "[InteractionTarget.GetFormableCountry.GetNameWithNoTooltip]"),
    "culture": ("SORT_TEXT_CULTURE_NAME", "[InteractionTarget.GetCulture.GetName]",
                "", "[InteractionTarget.GetCulture.GetNameWithNoTooltip]"),
    "religion": ("SORT_TEXT_RELIGION_NAME", "[InteractionTarget.GetReligion.GetName]",
                 '\t\t\ticon = {\n\t\t\t\tsize = { 28 28 }\n\t\t\t\ttexture = "[GetReligionIcon(InteractionTarget.GetReligion)]"\n\t\t\t}\n',
                 "[InteractionTarget.GetReligion.GetNameWithNoTooltip]"),
    # a nation without a tier opens its atlas card (the hidden concept), not the live country tooltip; the concept link
    # comes from loc keyed by the nation's index, since its tag can't build a key in the GUI
    "country": ("SORT_TEXT_COUNTRY_NAME",
                "[Localize(Concatenate('FMX_XI_', ToString_int32(FixedPointToInt(InteractionTarget.GetCountry.MakeScope.ScriptValue('fmx_x_index_value')))))]",
                '\t\t\tcountry_flag_small = {\n\t\t\t\tsize = { 40 27 }\n\t\t\t\tdatacontext = "[InteractionTarget.GetCountry]"\n\t\t\t}\n',
                "[InteractionTarget.GetCountry.GetNameWithNoTooltip]"),
}


def name_col(s):
    return f"fmx_{s['type']}_name"


def files(G, L):
    out = {}
    actions = []
    for t, s in L.items():
        visible = f"\t\tvisible = {{\n\t\t\tOR = {{\n{s['visible']}\n\t\t\t}}\n\t\t}}\n" if s["visible"] else ""
        cols = "".join(f"\t\tcolumn = {{\n\t\t\tdata = {k}\n\t\t}}\n" for k in [name_col(s)] + s.get("extra_cols", []) + [c.key for c in s["cols"]])
        actions.append(f'''{s["action"]} = {{
	type = owncountry
	potential = {{
	}}
	allow = {{
	}}
	ai_tick = never
	ai_tick_frequency = 12

	select_trigger = {{
		looking_for_a = {s["type"]}
		target_flag = target
		name = "{s["action"]}_select"
		none_available_msg_key = "{s["action"]}_none"
{cols}{visible}	}}

	effect = {{
	}}

	ai_will_do = {{
		value = 0
	}}
}}
''')
        # attribute columns: the game's file for this type plus ours
        vanilla = open(G + "in_game/common/attribute_columns/" + s["cols_file"], encoding="utf-8-sig").read().replace("\r", "")
        cut = vanilla.rindex("}")
        sort_key, tooltip, icon, name_text = NAME_COLS[s["type"]]
        extra = [f"\n\t{name_col(s)} = {{\n\t\twidget = {name_col(s)}\n\t\twidth = {s.get('name_w', 190)}\n\t\tfixed_height = 32\n\t\tis_constant_width = no\n"
                 f"\t\tsort = {{\n\t\t\tsort_text = {{\n\t\t\t\tvalue = \"{sort_key}\"\n\t\t\t}}\n\t\t\tsort_by_tooltip_key = \"SORT_TEXT_NAME_TT\"\n\t\t}}\n\t}}\n"]
        for c in s["cols"]:
            if c.kind == "text":
                sort = f'\t\t\tsort_text = {{\n\t\t\t\tvalue = "FMX_SORT_{c.key}"\n\t\t\t}}\n'
            else:
                sort = f'\t\t\tsort_value = {{\n\t\t\t\tvalue = {c.key}_value\n\t\t\t}}\n'
            extra.append(f"\n\t{c.key} = {{\n\t\twidget = {c.key}\n\t\twidth = {c.width}\n\t\tfixed_height = 32\n\t\tis_constant_width = yes\n"
                         f"\t\tsort = {{\n{sort}\t\t\tsort_by_tooltip_key = \"FMX_SORT_TT_{c.key}\"\n\t\t}}\n\t}}\n")
        out[f"in_game/common/attribute_columns/{s['cols_file']}"] = vanilla[:cut] + "".join(extra) + "}\n"

        # the widgets of our columns
        gui = [f"types Fmx{s['type'].title()}Columns\n{{",
               f"\ttype {name_col(s)} = select_cell_default {{\n\t\tsize = {{ {s.get('name_w', 190)} 32 }}\n"
               # like the game's religion name cell: the action's tooltip pops out to the side, and the name's link
               # opens the object's own tooltip
               + (f"\t\tblockoverride \"interaction_target_action_provider_tooltip\" {{\n\t\t\ttooltipwidget = {{\n\t\t\t\tusing = action_tooltip_pop_out\n\t\t\t}}\n\t\t}}\n"
                  f"\t\ttagtooltip_enabled = yes\n\t\ttooltip = \"{tooltip}\"\n" if tooltip else "") +
               f"\t\tsort_by_highlight = {{\n\t\t\tsize = {{ 100% 100% }}\n\t\t\tname = \"{name_col(s)}\"\n\t\t}}\n"
               f"\t\thbox = {{\n\t\t\tmargin = {{ 10 0 }}\n\t\t\tspacing = 5\n\t\t\tlayoutpolicy_horizontal = expanding\n{icon}"
               f"\t\t\ttext_single = {{\n\t\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\t\talign = nobaseline\n"
               f"\t\t\t\tdefault_format = \"#yellow_titles\"\n\t\t\t\ttext = \"{name_text}\"\n\t\t\t}}\n\t\t}}\n\t}}\n"]
        for c in s["cols"]:
            if c.kind == "text":
                text = c.show
            elif c.kind == "sv":        # the script value itself, for objects with no key getter in the GUI
                text = f"[{s['target']}.MakeScope.ScriptValue('{c.key}_value')|0]"
            else:
                text = f"[Localize(Concatenate('{c.prefix}', {s['target']}{s.get('loc_key', '.GetKey')}))]"
            gui.append(f"\ttype {c.key} = select_cell_default {{\n\t\tsize = {{ {c.width} 32 }}\n"
                       f"\t\tsort_by_highlight = {{\n\t\t\tsize = {{ 100% 100% }}\n\t\t\tname = \"{c.key}\"\n\t\t}}\n"
                       f"\t\thbox = {{\n\t\t\tmargin = {{ 10 0 }}\n\t\t\tlayoutpolicy_horizontal = expanding\n"
                       f"\t\t\ttext_single = {{\n\t\t\t\tlayoutpolicy_horizontal = expanding\n\t\t\t\talign = {'center|nobaseline' if c.kind != 'text' else 'nobaseline'}\n"
                       f"\t\t\t\ttext = \"{text}\"\n\t\t\t}}\n\t\t}}\n\t}}\n")
        gui.append("}\n")
        out[f"in_game/gui/attribute_columns/fmx_{s['type']}.gui"] = "\n".join(gui)

        # script values for the numeric sorts
        sv = []
        for c in s["cols"]:
            if c.kind == "text":
                continue
            branches = "".join(f"\tif = {{ limit = {{ {s['cond'].format(k=s['okey'](o))} }} value = {c.count(o)} }}\n"
                               for o in s["objects"] if c.count(o))
            sv.append(f"{c.key}_value = {{\n\tvalue = 0\n{branches}}}\n")
        if s["type"] == "country":
            # 1-based position of a nation without a tier (0 for any other country): the GUI turns it into the loc key
            # of the atlas block in the country tooltip, since a country's tag can't be used to build a key there
            branches = "".join(f"\tif = {{ limit = {{ tag = {o['tag']} }} value = {n + 1} }}\n" for n, o in enumerate(s["objects"]))
            sv.append(f"fmx_x_index_value = {{\n\tvalue = 0\n{branches}}}\n")
        out[f"in_game/common/script_values/fmx_{s['type']}_values.txt"] = "\n".join(sv)

        # the game's filter file is overridden only to switch its default filter off; ours live in a file of their own
        if s["default_filter"]:
            flt = open(G + "in_game/gui/filters/" + s["filters_file"], encoding="utf-8-sig").read().replace("\r", "")
            start = flt.index(s["default_filter"] + " = {")
            at = flt.index("enabled_at_start = yes", start)
            out[f"in_game/gui/filters/{s['filters_file']}"] = flt[:at] + "enabled_at_start = no" + flt[at + len("enabled_at_start = yes"):]
        flt = f"# {s['type'].upper()} (Formables Atlas)\n"
        for key, grp, cond in s["filters"]:
            if not cond.strip():
                continue
            body = cond if cond.lstrip().startswith("scope:") else f"\t\tOR = {{\n{cond}\n\t\t}}"
            tag = f"\ttag = {s['filter_tag']}\n" if s["filter_tag"] else ""
            flt += (f"\n{key} = {{\n\tscope = {s['type']}\n{tag}\tgroup = {90 + grp}\n\texclusive_group = yes\n"
                    f"\ttrigger = {{\n{body}\n\t}}\n}}\n")
        out[f"in_game/gui/filters/90_fmx_{s['type']}.txt"] = flt

        out[f"main_menu/gfx/interface/icons/sort/{name_col(s)}.dds"] = ("copy", G + "main_menu/gfx/interface/icons/sort/name.dds")
        for c in s["cols"]:
            out[f"main_menu/gfx/interface/icons/sort/{c.key}.dds"] = ("copy", G + f"main_menu/gfx/interface/icons/sort/{c.icon}.dds")
    out["in_game/common/generic_actions/fmx_atlas.txt"] = "\n".join(actions)
    return out


def loc(lang, L, filter_names):
    ru = lang == RU
    out = {"FMX_XI_0": "", "FMX_NATIVE_HINT": "Список откроется в окне игры: сортировка по любой колонке, поиск и фильтры (кнопка-воронка). Наведите на название — откроется карточка с данными атласа."
            if ru else "The list opens in the game's own window: sort by any column, search and filters (funnel button). Hover a name for its card with the atlas data."}
    for t, s in L.items():
        name = s["name"][0 if ru else 1]
        out[s["action"]] = name
        out[s["action"] + "_desc"] = "Список с данными атласа. Ничего не делает." if ru else "A list with the atlas data. Does nothing."
        out[s["action"] + "_select"] = name
        out[s["action"] + "_none"] = "Пусто" if ru else "Nothing here"
        short = name.split(": ", 1)[-1]            # the panel buttons drop the "Atlas:" prefix to fit
        out[f"FMX_NATIVE_{t.upper()}"] = short[:1].upper() + short[1:]
        for c in s["cols"]:
            out[c.key] = c.ru if ru else c.en
            out[f"FMX_SORT_TT_{c.key}"] = c.tt_ru if ru else c.tt_en
            if c.kind == "text":
                out[f"FMX_SORT_{c.key}"] = c.sort
            elif c.kind == "num":
                for o in s["objects"]:
                    k = s["key_of"](o)
                    if k is not None:
                        out[f"{c.prefix}{k}"] = str(c.count(o))
        out[name_col(s)] = "Название" if ru else "Name"
        for (key, n, _), fname in zip(s["filters"], filter_names[t]):
            out[f"search_filter_{key}_name"] = fname
            out[f"search_filter_{key}_desc"] = ("Атлас: " if ru else "Atlas: ") + fname
    return out
