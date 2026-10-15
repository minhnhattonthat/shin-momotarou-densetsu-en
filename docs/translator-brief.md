# Translator brief - Shin Momotarou Densetsu (SNES, Hudson Soft, 1993)

You translate part of the Japanese script of Shin Momotarou Densetsu ("The New Legend of Momotaro") into English for
a fan patch. A comic folk-tale RPG by Sakuma Akira: Momotaro (the Peach Boy) and friends - Kintaro, Urashima, the oni
princess Yasha - fight the oni king Basara and the scheming Karura, six years after the first game. Lots of puns,
parody of Japanese folklore and pop culture, rustic villagers, pompous sages.
Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.
Repo root: H:\translation\batch\projects\shin-momotarou-densetsu (run commands from there).

## Read first
1. `glossary.md` - rulings, style rules and binding names/terms. Use those English forms exactly.
2. `docs/style-reference.md` - approved example pairs (voice, speaker-line format, wrapping).
3. `docs/names.tsv` (if present) - approved English for every item, monster, place and character name in the game.
   When dialogue mentions one of these, use the same English. Exception: `character` rows are 8-character menu
   forms; in dialogue use the glossary's full form (福の神 "the God of Fortune", 黒河童 "the Black Kappa",
   天の邪鬼 "Amanojaku", はらだし "Bellyman", 夜叉姫 "Yasha" or "Princess Yasha").
   Search it with grep, e.g. `grep -F 'きびだんご' docs/names.tsv`.

## Input: `work/tl/<batch>.tsv`
`id<TAB>form<TAB>limit<TAB>Japanese`. Lines are in game order: use neighbours for context.
- form `dlg`: dialogue or narration. The limit (224px/line) is enforced by an automatic line wrapper; you do not
  count characters. A line of about 40 average characters fits.
- form `name`: a name or label shown in a fixed-width menu field. The limit is a hard maximum in characters
  (e.g. `16ch`). Count every character including spaces. Use the full word; if it truly cannot fit, choose a
  shorter synonym (not an abbreviation) and report `LONG: id`.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII only: straight quotes, `...` for ellipses,
`--` for dashes; no tabs inside the English, no Japanese or fullwidth characters, no `\uXXXX`.

## Control codes (copy rules)
- `{n}` = line break. In `dlg` keep `{n}` where the Japanese starts a new speaker/name line, a new quote or a blank
  line (`{n}{n}`); inside one quote write the sentence on one line and let the wrapper break it. You may also keep
  a `{n}` where a deliberate break helps (narration, poems).
- Speaker lines look like `{c1}Name{n}{c0}"Text"`. Keep `{c0}`..`{c3}` (colours) exactly where they are.
- `{0B}`, `{wait}`, `{page}`, `{0D}`, `{0E}`, `{10}`, `{12}` and `[XX]` are box/flow codes: keep every one, in order,
  at the same position relative to the text (usually the end).
- `{hero}` (hero's name), `{arg}` (a name, item or amount the game inserts), `{num}` (a number): keep each one exactly as many times as the Japanese.
  Sentences must read naturally whatever is inserted: no "a/an" right before them, no suffix glued on
  ("No. {num}" not "{num}th"), plural-safe wording ("{num} ryo" is fine).
  `{arg}{arg}` pairs occur (a prefix + a name): keep both together where the name goes.
- `{kata}` / `{hira}` (kana mode switches): delete them.
- `{sub:XX}` (dictionary fragments, e.g. {sub:A0} = 桃太郎 Momotaro, {sub:C5} = ください please, {sub:B6} = おまえ you,
  {sub:A8} = ウヒャヒャ… (Heavenly Sage's laugh "Uhyahya..."), {sub:B5} = チュチュン! (sparrow chirp "Chuchun!")):
  never keep them; write the words out in English. The full list is in `docs/subs.tsv`.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it prints OK.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese
  doesn't state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Names and terms exactly as in the glossary / names list. Never abbreviate.
- Honorifics dropped (さん, 様, 殿): use register instead; "King Enma", "Princess Kaguya" where the Japanese uses
  a title. Given name first.
- Natural English a player enjoys reading: contractions in casual speech, characterful voices (Karura sneers and
  cackles, Basara is regal, villagers are folksy, Kintaro is brash, Yasha is a proud but kind princess).
- Notes from earlier batches: 順安 (pickle shop) = Jun'an; 辰巳 = Tatsumi; トメ = Tome (carpenter);
  『桃伝』 = the Famicom 'Momotaro Densetsu'; 四天王 = the Four Heavenly Kings; 臥龍 = Garyu (Sleeping Dragon).
  鬼道 = "Oni Arts" (鬼道吸い取り = Oni Arts Drain); つづら = wicker chest; 道具袋 = Item Bag.
  Ashura's riddle poems (quote them exactly): 夜をこめて 黄泉路をわたる つのかくし -> 'Before the night is through, /
  crossing the Road of Yomi, / the horn-hider'; よもつ国 たたえて咲くや 夢見草 -> 'The Land of Yomi-- / blooming
  in its praise, / the dream-seeing flower'; 黄金さす みほとけまもる つばくらめ -> 'Golden-gleaming, / guarding
  the holy Buddha, the tsubakurame'. 仙豆 = sage bean; 智将 = the Wise General; 稲妻仙人 = the Bolt Sage.
  {sub:A0}のおじいさん / おばあさん = "Momotaro's Grandpa" / "Momotaro's Grandma" (other old folk: Old Man / Old Woman).
  "{arg}'s" (possessive) is fine. Keep each speaker line's name exactly as the glossary.

## Consistency
Never edit `glossary.md` or script files. For a recurring name or term not in the glossary/names list, pick a form,
use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
