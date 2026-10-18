# Shin Momotarou Densetsu (新桃太郎伝説) English translation

Unofficial English fan translation of **Shin Momotarou Densetsu** ("The New Legend of Momotaro"), Hudson Soft, Super Famicom, 1993 (Rev 1).

**No game data is included.** Download the BPS patch from the [latest release](../../releases/latest) and apply it to your own headerless No-Intro dump, `Shin Momotarou Densetsu (Japan) (Rev 1).sfc` (CRC32 4A653411). The release README lists the hashes and patching steps. The patched ROM is 4 MB HiROM.

## What is translated
All dialogue, menus, item/art/monster names, the name entry screen, the family tree and command chart, status icons, the opening and ending credits and the title logo. See the release README for known issues.

## Building from source
You need your own ROM under `rom/` (gitignored). See `CLAUDE.md` for the commands (`python -X utf8 build.py`, `tools/check.py`, `tools/release.py`) and `docs/re/text.md` for the text engine research.

- `script/`: text blocks (`bNNN.json`, Japanese + English per string) and window labels (`win.json`)
- `tools/`: extraction, insertion, engine patches, graphics, debug warp and release tools
- `tbl/kanji.txt`: kanji table
- `glossary.md`: naming rulings

Translation, tools and patch were produced with AI assistance (Claude, Anthropic) under the direction of the project owner. Original game © 1993 Hudson Soft / Sakuma Akira.
