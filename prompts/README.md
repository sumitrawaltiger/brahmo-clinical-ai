# Prompt library — what was actually used

Two kinds of prompts exist in this build and both are deliverables:

1. **Agent-level prompts** — the instructions given to the coding agent (Claude Code, model Claude Fable 5.1) that
   produced this repository. They are reproduced verbatim or as the exact working instructions in
   `prompts/agent/`. Everything in `src/` was written by the agent under those instructions, reviewed and run by
   the candidate; the commit history shows the sequence.
2. **Runtime prompts** — prompts the *system* sends to a model at run time. There is exactly one
   (`prompts/runtime/grounded_answer_v1.md`), used only in `answering.mode=llm`. Its sha256 is the
   `prompt_version` recorded in every Q&A run and trace. The deterministic rail has no prompt by design.

| file | kind | used for | replayable how |
|---|---|---|---|
| `agent/00_kickoff.md` | agent | the candidate's opening instruction + the kit handed to the agent | paste into a fresh Claude Code session in a folder containing the kit |
| `agent/01_working_instructions.md` | agent | the standing instructions the agent followed for every module (derived from the brief's laws; these are the "conventions" the agent operated under, now also encoded in `CLAUDE.md`) | same |
| `agent/02_module_prompts.md` | agent | the per-module task prompts in the order they were issued | same, one at a time |
| `agent/03_review_prompts.md` | agent | the self-review / verification prompts used after each module | same |
| `runtime/grounded_answer_v1.md` | runtime | LLM composition in Module B (`llm` mode) | `BRAHMO_ANSWERING__MODE=llm brahmo ask "..."` |

What the AI tools got wrong and how it was caught is recorded in `DESIGN.md` §"What the coding agent got wrong".
