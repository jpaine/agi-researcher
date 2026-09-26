# Critique → method edits

Source: [`critique.md`](critique.md) (gpt-5 critique pass; not experimental results).  
Edited: [`input_files/methods.md`](input_files/methods.md) (mirrored to [`methods.md`](methods.md)).

| Critique ask | Edit |
| --- | --- |
| Primary comparator A vs B | Methods overview + §5.3 + §8.2: claim test is Cards vs Prose. C secondary. D appendix / exploratory foil, excluded from the primary claim. |
| Shared `N_target` | §6.1 and §7.2: dev min throughput across A–C; test uses the same first `N_target` steps and one seed. |
| Kill differing denominators | §8.2 drops “eligible portion before cutoff.” |
| Stronger prose baseline | §3.3: headings, bullets, `card_id` tags, identical examples; §5.3 mirrors A/B instruction text. |
| Blinding | §6.2 and §10: hide `risk_score` in the human UI; randomize within priority bands. |
| Public-trace limitation | §1.1 and §13: SWE-agent traces are a proxy; no enterprise claim. |
| Minor | §1.3 simple hash by default; §11 bootstrap ok, formal tests secondary; no metrics invented. |

Card YAML and matched prose live under `brainstorm/minutes-and-mandates/cards/`. Gate A checkboxes stay open until a real pilot produces evidence.
