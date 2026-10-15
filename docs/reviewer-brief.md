# Translation reviewer brief - Shin Momotarou Densetsu (SNES)

You review one batch of a JP->English fan translation. Do not edit script files or the glossary, no git, no
subagents. Mechanical validity (ids, control codes, encodable characters, line width) is enforced by tools - judge
translation quality. Repo root: H:\translation\batch\projects\shin-momotarou-densetsu.

## Inputs
- `work/tl/<batch>.pairs.txt`: every entry as `>> id | JP` / `EN:`, in game order. Read ALL of it.
- `glossary.md` (rulings at the top), `docs/style-reference.md`, `docs/translator-brief.md` (control-code rules and
  "notes from earlier batches"), `docs/names.tsv` (grep it for names), `docs/subs.tsv` ({sub:XX} meanings).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP gist.
- Consistency: glossary names/terms exactly; a one-letter slip ("Bran" for "Plan") is what players notice.
- Things players caught that reviewers missed: jokes/wordplay losing their punch; "1th"-style suffix after a
  variable; abbreviations; awkward stock phrases ("... GET!"); English that reads oddly with {arg}/{num} inserted.
- Naturalness: register and voice per the style reference.

## Fixes (the only file you may write)
For every Critical or Important issue, write the corrected English line to `work/tl/<batch>.fix.tsv`
(`id<TAB>English`, file-write tool, same control codes as the existing English). Then run
`python -X utf8 tools/batches.py checkfix <batch>` and repair until it prints OK. No file if there is nothing to fix.

## Report (your final message)
### Critical / Important (fixed in the fix file)
`id - JP gist - problem - fix`
### Minor (not fixed; one line each, at most 10)
### Assessment
Approved | Fixed N issues - one sentence.
