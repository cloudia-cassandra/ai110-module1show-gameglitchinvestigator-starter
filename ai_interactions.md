# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->

**What did the agent do?**

<!-- List the steps the agent took (files edited, commands run, etc.) -->

**What did you have to verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

**Prompts used**

1. Earlier in the project, to build the regression suite:

   ```
   add 9 regression tests, one per row of the bug reproduction log in reflection.md,
   so every documented bug has a test that would have caught it
   ```

2. For Challenge 1 (the edge-case suite):

   ```
   Challenge 1: Advanced Edge-Case Testing
   identify three potential "edge case" inputs (e.g., negative numbers, decimals, or
   extremely large values) that might still break your game - i think we did, but make
   sure that we have them covered to complete this challenge.
   Generate a suite of pytest cases that verify your game handles these inputs gracefully.
   ```

   The useful part of this prompt was *"make sure that we have them covered"* rather than
   "write tests". Instead of generating tests from the function signatures, the AI first ran the
   three edge cases against the real `parse_guess()`, `check_guess()` and `update_score()` and
   printed what actually came back. Three of the cases I assumed were covered were, and three
   problems nobody had looked for were not.

**Edge cases and results**

| Edge Case | Why This Case | AI-Suggested Test | Did It Pass? | Reasoning |
|-----------|---------------|-------------------|--------------|-----------|
| Negative numbers (`-1`, `-5`, `-999999`, `-0`) | They parse as valid ints, so the range check is the only thing stopping them. | `test_negative_guesses_are_rejected`, `test_negative_zero_is_rejected_like_zero` | ✅ Passed first run | Already handled by the range validation added in Phase 2 — the tests confirm it rather than fix it. I kept `-0` separately because it parses to `0`, which is a different failure from a negative. |
| Decimals (`3.9`, `.5`, `50.`, `-2.5`) | `int(float("3.9"))` is `3`, so the game used to score a number the player never typed. | `test_decimals_are_rejected_never_truncated`, `test_decimal_is_not_silently_rounded_to_a_valid_guess` | ✅ Passed first run | Already fixed in Phase 2; the second test is the one that matters, since it asserts no usable value comes back, not just that `ok` is `False`. |
| Extremely large values (`12390921309213`, `9`×100, `10**1000`) | This is the exact input from my bug log — the old string comparison judged 12 trillion as *lower* than 60. Python ints are unbounded, so there is no natural ceiling. | `test_oversized_guesses_are_rejected`, `test_huge_values_compare_numerically_not_as_text`, `test_huge_values_do_not_raise` | ✅ Passed first run | The headline bug from the project, now locked down from both sides: rejected at input, and still compared numerically if one ever reached `check_guess()`. |
| `int()`-permissive formats (`"5_0"`, full-width `"１０"`, Arabic-Indic `"١٠"`) | Found while probing — `int()` accepts PEP 515 underscores and any Unicode decimal digit. | `test_intish_strings_are_rejected`, `test_harmless_formatting_is_still_accepted` | ❌ Failed → fixed | `"5_0"` was accepted as **50** and `"１０"` as **10**. A player typing those did not mean those numbers. I added a `^[+-]?[0-9]+$` check, plus a second test proving `"+50"`, `"00050"` and `" 50 "` still work, so the stricter rule did not break ordinary typing. |
| Non-string input (`50`, `50.0`, `True`) | Found while probing — Streamlit always passes a `str`, but the function should not crash if something else arrives. | `test_non_string_input_does_not_raise` | ❌ Failed → fixed | Raised `AttributeError: 'int' object has no attribute 'strip'` instead of returning the `(ok, value, error)` contract every caller expects. Coerced with `str()` first. |
| Scoring boundaries (`attempt_number` of `0`, `-1`, `1000`) | Found while probing — the win bonus clamped only its lower end. | `test_win_bonus_is_capped_at_100`, `test_win_bonus_never_falls_below_10`, `test_score_floor_holds_across_a_whole_losing_round` | ❌ Failed → fixed | `update_score(0, "Win", 0)` returned **110**, above the intended 100 maximum. Clamped at both ends. Not reachable through the UI today, but it is a silent invariant break if the counter ever changes. |

**Result:** 64 tests passing (`tests/test_edge_cases.py` + `tests/test_game_logic.py`). Full
terminal output is in the Test Results section of [`README.md`](README.md).

**What I would keep doing:** asking the AI to *probe the real functions and show the output*
before writing any test. Tests written straight from a function signature only confirm what the
code already does. Running the inputs first is what separated "three cases I had covered" from
"three problems I did not know about."

---

## Linting & Style (SF9)

> Document your use of AI for linting or code style improvements.

**Prompt used:**

```
Challenge 3: Professional Documentation and Linting

Add professional-grade docstrings to every function in logic_utils.py.
Then, review your code for PEP 8 style compliance and apply its suggestions to
resolve any formatting or naming issues it identifies.
In ai_interactions.md, include the prompt(s) you used, paste the linting output
(in a code block or committed .txt), and add a short note on what
formatting/naming changes the AI suggested and which you applied.
```

The project had **no linter installed** when this started (`requirements.txt` was just
`streamlit`, `altair`, `pytest`), so step one was installing `ruff` and `pycodestyle` and
recording a real "before" run rather than reasoning about style by eye.

**Tools used**

| Tool | Version | What it checks |
|------|---------|----------------|
| `ruff` | 0.16.10 | pycodestyle (`E`/`W`), pyflakes (`F`), isort (`I`), **pep8-naming (`N`)**, **pydocstyle (`D`)**, pyupgrade (`UP`), bugbear (`B`) |
| `pycodestyle` | 2.15.0 | PEP 8 layout only — used as an independent second opinion |

Rules are committed in [`pyproject.toml`](pyproject.toml) rather than passed as flags, so
`ruff check .` reproduces exactly the run below. Full before/after output is committed at
[`docs/lint_output.txt`](docs/lint_output.txt).

**Linting output before:**

```
$ python -m ruff check . --output-format concise
app.py:1:1: D100 Missing docstring in public module
app.py:1:1: I001 [*] Import block is un-sorted or un-formatted
app.py:111:5: D205 1 blank line required between summary line and description
app.py:111:5: D212 [*] Multi-line docstring summary should start at the first line
app.py:136:5: D205 1 blank line required between summary line and description
app.py:136:5: D212 [*] Multi-line docstring summary should start at the first line
logic_utils.py:33:5: D212 [*] Multi-line docstring summary should start at the first line
logic_utils.py:83:5: D212 [*] Multi-line docstring summary should start at the first line
logic_utils.py:151:5: D212 [*] Multi-line docstring summary should start at the first line
logic_utils.py:173:5: D212 [*] Multi-line docstring summary should start at the first line
tests/test_edge_cases.py:1:1: D212 [*] Multi-line docstring summary should start at the first line
tests/test_game_logic.py:1:1: D100 Missing docstring in public module
tests/test_game_logic.py:1:1: I001 [*] Import block is un-sorted or un-formatted
tests/test_game_logic.py:24:1: E402 Module level import not at top of file
tests/test_ui_helpers.py:1:1: D212 [*] Multi-line docstring summary should start at the first line
tests/test_ui_helpers.py:10:1: I001 [*] Import block is un-sorted or un-formatted
... (43 further D103 "Missing docstring in public function" on test functions)
Found 60 errors.
[*] 12 fixable with the `--fix` option.

$ python -m pycodestyle --max-line-length=100 app.py logic_utils.py tests/
tests/test_game_logic.py:3:1: E302 expected 2 blank lines, found 1
tests/test_game_logic.py:8:1: E302 expected 2 blank lines, found 1
tests/test_game_logic.py:13:1: E302 expected 2 blank lines, found 1
tests/test_game_logic.py:24:1: E402 module level import not at top of file
```

**Linting output after:**

```
$ python -m ruff check .
All checks passed!

$ python -m pycodestyle --max-line-length=100 app.py logic_utils.py tests/
(no output - clean)

$ python -m pytest
collected 85 items

logic_utils.py ......                                                    [  7%]
tests/test_edge_cases.py ............................................... [ 62%]
.....                                                                    [ 68%]
tests/test_game_logic.py ............                                    [ 82%]
tests/test_ui_helpers.py ...............                                 [100%]

============================== 85 passed in 0.04s ==============================
```

**Changes suggested and which I applied**

| Rule | What the linter flagged | Applied? | Note |
|------|------------------------|----------|------|
| `D212` ×8 | Multi-line docstring summaries started on the line *below* `"""`. | ✅ Applied (autofix) | Purely cosmetic, but it is the convention `ruff --fix` enforces, so there was no reason to argue. |
| `D205` ×2 | No blank line between a docstring's summary line and its description. | ✅ Applied (manual) | Forced me to actually write one-line summaries. Both offenders were `app.py` render functions whose docstrings opened with `"""UI [1]: the plain st.info()...` — a note, not a summary. Rewrote as `"""Render the metrics row and attempts progress bar.` with the UI note below. |
| `I001` ×4 | Import blocks unsorted / ungrouped. | ✅ Applied (autofix) | Split stdlib from third-party in `app.py` (`import random`, blank line, `import streamlit as st`). |
| `D100` ×2 | `app.py` and `tests/test_game_logic.py` had no module docstring. | ✅ Applied (manual) | Used `app.py`'s to document the `# FIX [n]` / `# EDGE CASE [n]` / `# UI [n]` / `# COLLAB` comment markers, which were previously undocumented conventions a reader had to infer. |
| `E402` ×1 | `tests/test_game_logic.py` imported `get_range_for_difficulty`, `parse_guess` and `update_score` *halfway down the file*. | ✅ Applied (manual) | A genuine mess left from appending tests to the file earlier. Merged into the single import block at the top. |
| `E302` ×4 | Only one blank line between top-level functions. | ✅ Applied (manual) | In the three original project tests and one of mine. |
| `D103` ×43 | Every test function was "missing a docstring". | ❌ **Not applied** | This is the one I pushed back on. Names like `test_closer_guesses_are_never_colder` and `test_score_never_goes_negative` already say what they assert; adding `"""Test that closer guesses are never colder."""` to all 43 would be pure restatement. I added a `per-file-ignores` entry in `pyproject.toml` disabling `D103` for `tests/*` only, with a comment explaining why. **`D100` stays on**, so test *modules* still need a docstring explaining what the file covers. |
| `N` (pep8-naming) | *No findings.* | — | Nothing to fix. Naming was already snake_case for functions and UPPER_CASE for the module constants. |

**Docstrings added**

All six functions in [`logic_utils.py`](logic_utils.py) were rewritten to Google-style docstrings
with `Args:`, `Returns:`, `Raises:`, `Examples:` and `Note:` sections, plus a module-level
docstring listing the public API. Type hints were added to every signature at the same time
(`-> tuple[int, int]`, `low: int | None = None`, and so on).

Two choices worth recording:

1. **The `Note:` section documents the original bug.** Each function that had a bug explains what
   it was — `check_guess` describes the string-comparison fallback that made 12 trillion read as
   lower than 60. A future reader seeing `int()` coercion on both arguments would otherwise be
   tempted to "simplify" it away.
2. **The `Examples:` blocks are real doctests, not decoration.** I wired
   `--doctest-modules logic_utils.py` into `addopts` in `pyproject.toml`, so the 20 examples run
   as part of `pytest`. If a docstring claims `update_score(0, "Win", 4)` returns `70` and the
   scoring changes, the suite fails. The test count went from 79 to **85** as a result — the
   documentation is now executable rather than something that silently rots.

---

## Model Comparison (SF11)

> Compare two AI models on the same task.

**Task given to both models:**

<!-- Describe what you asked each model to do -->

| | Model A | Model B |
|-|---------|---------|
| **Model name** | | |
| **Response summary** | | |
| **More Pythonic?** | | |
| **Clearer explanation?** | | |

**Which did you prefer and why?**

<!-- Your conclusion -->
