# Adding or Changing a Workflow Step

The workflow is **data**, not implicit call order (ADR-0002, spec 02):
`pipeline.build_workflow()` returns a `Workflow` of `StepDef`s, and
`engine.Workflow._validate()` checks the artifact contract graph at
assembly time — before anything runs.

## Adding a step to `produce-video`

1. Write the step function: `def my_step(ctx: RunContext) -> StepResult`.
   - Read inputs via `ctx.artifact("name")` + `ctx.store.get_json/get_text`.
   - Do the work (call a provider, transform data).
   - Write outputs via `ctx.store.put_json/put_text/put_bytes` — every
     output **must** be an `artifact://` ref; the engine asserts this
     (`engine.Runner.run`, `is_ref` check) and raises `StepError` otherwise.
   - Return `StepResult({"output_name": ref}, provenance_dict)`. Provenance
     (`provider`, `model`, `prompt_ref`, `prompt_hash`, `seed`) is optional
     but should be included whenever a provider call happened — it's what
     makes `manifest.json` a real audit trail.
   - **Validate at the boundary.** Degenerate results (empty list, empty
     string, zero duration) must raise `ValidationError` here — the
     pipeline must never "succeed" into a broken package (spec 02).
2. Add a `StepDef(name, inputs, outputs, fn)` to the list in
   `pipeline.build_workflow()`, in the position it should run.
3. `inputs` and `outputs` are tuples of artifact names (strings). Get this
   wrong and `Workflow.__init__` raises `ValidationError` immediately:
   consuming an artifact no earlier step produces, or re-producing one
   that already exists, both fail at assembly — you cannot ship a
   mis-wired workflow.
4. If the step is genuinely new content (not a variation of an existing
   one), add a corresponding prompt template under
   `docs/prompts/youtube/` and reference it via `prompt_ref` in
   provenance, and update the step table in
   `docs/workflow/produce-video.md` and `docs/specs/02-workflow-and-pipeline.md`.

## Adding a second workflow

The engine is workflow-agnostic — `produce-video` is workflow #1, not the
only one the engine can run (see ADR notes in spec 02 on this point). A new
workflow is:

```python
def build_my_workflow() -> Workflow:
    return Workflow(name="my-workflow", initial=("some_input",), steps=[...])
```

Give it a business-level definition in `docs/workflow/` before writing
code, per the repo's Vision → Knowledge → Architecture → Workflow → Prompt
→ Runtime ordering (`docs/architecture/overview.md`) — the workflow layer
is not allowed to lag the code.

## The human-approval gate

A step's `StepRecord.status` can be `awaiting_approval`
(`manifest.STATUS_AWAITING_APPROVAL`). `engine.Runner.run` halts — does not
execute — when it encounters this status. If your step should support a
review gate before continuing (e.g. before `publish`), set that status on
the record externally (not from inside the step function) and the runner
will stop there until it's cleared back to `pending`/`done`.

## Common mistakes the engine catches for you

| Mistake | What happens |
|---------|---------------|
| Step consumes an artifact no earlier step produces | `ValidationError` at `Workflow()` construction |
| Two steps produce the same artifact name | `ValidationError` at `Workflow()` construction |
| Step returns fewer outputs than declared | `StepError` at run time, step marked `failed` |
| Step returns a non-`artifact://` value | `StepError` at run time |
| Duplicate step name | `ValidationError` at `Workflow()` construction |
