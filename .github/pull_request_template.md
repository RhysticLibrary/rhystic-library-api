<!-- Title format suggestion: `type(scope): short summary`
     e.g. `feat(adr): add foo`, `fix(validate): handle bar`, `docs: update README` -->

## Summary

<!-- 1-3 bullets describing what changes and why. -->

## Test plan

- [ ] `pytest` passes locally
- [ ] `python tools/adr/validate.py --merge-gate` exits 0
- [ ] `ruff check tools/adr` and `ruff format --check tools/adr` are clean
- [ ] CI is green

## ADRs

<!-- Does this change embody a significant decision that should be captured?
     See `.claude/skills/creating-an-adr/SKILL.md`. -->

- [ ] No ADR needed
- [ ] ADR included or updated under `docs/adr/`
