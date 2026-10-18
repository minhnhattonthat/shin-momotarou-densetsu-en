Shin Momotarou Densetsu (SNES) - English translation patch v{version}
=====================================================================

"The New Legend of Momotaro" (Hudson Soft, 1993), the Super Famicom sequel to Momotaro Densetsu,
fully translated into English: all dialogue, menus, item/art/monster names, the name entry
screen, the family tree and command chart, status icons, the ending credits and the title logo.

This is an unofficial fan translation. No ROM data is included; do not ask for ROMs.

How to patch
------------
Apply {bps} with any BPS patcher (Floating IPS / flips, beat, or the web-based RomPatcher.js)
to this ROM (No-Intro name, headerless):

  Shin Momotarou Densetsu (Japan) (Rev 1).sfc
  Size:   {o[size]} bytes (2 MB)
  CRC32:  {o[crc32]}
  MD5:    {o[md5]}
  SHA-1:  {o[sha1]}

Patched ROM (4 MB, expanded):
  CRC32:  {p[crc32]}
  SHA-1:  {p[sha1]}

If your ROM has a 512-byte copier header, remove it first (or use a patcher that does).
Rev 0 is not supported.

Notes
-----
- Tested in MesenCE 2.2.1: a cold boot through the opening into the first field, the field
  menus and status screen; every dialogue block and every menu/window screen was also checked
  with a debug warp. It was not played through to the end, so please report anything odd.
- Start a new game; saves made with the Japanese version still show Japanese names that
  were stored in the save itself.
- Honorifics are dropped; names are given-name first. Puns and parodies were rewritten
  so the joke still works in English.
- The ROM is expanded to 4 MB (HiROM); use an emulator or flash cart that supports it.

Changes
-------
v1.1: fixed a freeze in battle (enemy list window); aligned menu, battle Arts list, item list
      and shop borders; opening credits no longer wrap; prologue page fits its box.
v1.0: first release.

Known issues
------------
- Status icons are single 8x8 tiles, so they use short tags: Lv (level), HP, SP, ry (ryo),
  Cu (cursed), Po (poison), Pa (paralysis).
- The small calligraphy signature in the corner of the title screen is left as drawn.
- The status screen's top row has one blank (see-through) cell at its right end.

Credits
-------
Translation, hacking and QA: minhnhattonthat, with AI assistance (Anthropic Claude) for
reverse engineering, translation drafts, review and testing. All text was machine-assisted;
please report errors.
Original game (c) 1993 Hudson Soft / Sakuma Akira. This patch is not affiliated with them.
