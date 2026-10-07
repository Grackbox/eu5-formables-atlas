# Formables Atlas (EU5 mod)

In-game atlas of Europa Universalis V formable nations, nations without a tier, cultures and religions.
Four buttons in the Formables panel open the game's own list windows with sortable columns and filters; the game's
tooltips get an "Atlas" block (territory, required cultures and religions, conditions, state principles, culture and
religious advances).

Steam Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=3813746228
Website with the same data: https://grackbox.github.io/eu5-formables/ (repo `Grackbox/eu5-formables`)

## Build

```
python build.py        # reads the game files, writes site/data/<lang>.json and the site pages
python mod_build.py    # builds the mod from site/data into Documents/Paradox Interactive/Europa Universalis V/mod/formables_atlas
```

`EU5_GAME` points at the game's `game` folder (default `E:/SteamLibrary/steamapps/common/Europa Universalis V/game`),
`FMX_OUT` overrides the mod output folder.

| File | What it does |
|---|---|
| `build.py`, `pdx.py`, `template.html` | game data parser and the site generator |
| `mod_build.py` | the mod: tooltip blocks, panel buttons, Journal columns, hidden concepts for nations without a tier |
| `native_lists.py` | the four game list windows (generic actions, attribute columns, filters, script values) |
| `cover.png` / `cover.jpg` | launcher thumbnail / Workshop preview |

The mod overrides form_new_country.gui, cultures_ledger.gui, religions_ledger.gui and the country, culture and religion
attribute columns and filters. The tooltip templates it extends (formablecountry_info, culture_group_tooltip,
culture_tooltip, religion_tooltip, religion_group_tooltip) are replaced by name from `fmx_*_tooltips.gui`, so the rest
of the game's tooltip files (Glorp UI's CountryTooltip, for one) is left to other mods in any load order.

The build stops when a localization key of the mod shares its MurmurHash3 with a game key: the game then shows one
key's text for the other. The local build is named "Formables Atlas [LOCAL]"; `upload_item.py` takes the mark off.
