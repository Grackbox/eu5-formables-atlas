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

The mod overrides form_new_country.gui, country_tooltips.gui, society_tooltips.gui, religion_tooltips.gui,
cultures_ledger.gui, religions_ledger.gui and the country, culture and religion attribute columns and filters.
