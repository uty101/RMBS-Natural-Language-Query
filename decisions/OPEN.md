# Open decisions

Raised in session 4 (`instructions/04_section_4.md`). Evidence is in
`review/section_4.md`. O-37 was decided as (b) by instruction 04 A and is recorded in
`docs/CONVENTIONS_RESOLVED.md` N5.

## O-38. Step 4.4: `narrate` needs the catalogue for the number guard

F.1 gives `narrate(question, spec, display_table, client, cfg)`, and F.2 gives
`number_guard(text, question, display_table, catalog)`. The guard strips the catalogue's
deal names, which come from the database, so `narrate` can't run the guard without a
catalogue loaded with `db`.

- (a) `narrate(question, spec, display_table, client, cfg, catalog)`: the catalogue is a
  6th positional argument, which `answer` already holds. **This is what is built.**
- (b) Keep the F.1 signature, and have `answer` run the guard and swap in the template,
  so `narrate` returns only the model's text.

## O-39. Step 4.3: "Filters are processed in key order"

E says filters are processed in key order and values in list order. The first value
that becomes clarify or unsupported decides the result, so the order matters when 2
filters both fail.

- (a) The spec's own key order, as the model wrote the filters. **This is what is
  built**; `test_first_failure_decides` checks both orders.
- (b) Sorted dimension names.
