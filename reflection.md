# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?

It looked completely normal, which is the part that threw me. The page loaded with no errors, no
red Streamlit traceback, a tidy sidebar with a difficulty dropdown and a "Range / Attempts
allowed" caption, a guess box, Submit and New Game buttons, and a Developer Debug Info panel. If I
had only screenshotted it I would have said it worked. The problems only appeared once I actually
played: the hints started contradicting each other, the attempt counter did not match what the
sidebar promised, and after the round ended the board was permanently dead. Nothing ever *crashed*
— it just quietly gave wrong answers, which made it much harder to pin down than an error message
would have been.

- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").
1. would input "12390921309213" and it said to go lower, tried "1239092130921" and said go higher, tried "12390921309210" and said higher i think, all for it to take 15 attemps, and tell me the number was 60
2. after 15 attempts, game is done, says "game over. start a new game to try again" -> click new game, and won't let me play again
3. "new game" ignores selected difficulty
4. the attempt count didn't match the rules it showed me — the sidebar said 8 attempts allowed,
   but I got 15 guesses in before the round ended, and typing something invalid still seemed to
   cost me a turn
5. sidebar doesn't update the allowed attempts, it's an static "8"

**Bug Reproduction Logs**

Document at least 3 bugs you found. Add rows as needed.

| Input Used | Expected Behavior | Actual Behavior | Console Error / Output | Suspected Code Location |
|------------|-------------------|-----------------|------------------------|-------------------------|
| Guess `60` when the secret is `50` | Display "Too High" and advise the player to go lower. | Displays "Too High" but advises the player to go higher. | None; incorrect message. | `app.py`, `check_guess()` |
| Guess `9` when the secret is `60` on an even-numbered attempt | Compare both values numerically and display "Too Low". | The secret is converted to a string, so the comparison can be lexicographic and display "Too High". | None; incorrect hint. | `app.py`, submit logic and `check_guess()` |
| Click "New Game" after losing | Reset the game and allow a new guess. | The previous `"lost"` status remains, so the app still displays "Game over" and stops. | None; game remains unplayable. | `app.py`, `new_game` branch |
| Select Easy, then click "New Game" | Generate a secret within the Easy range of `1` to `20`. | Generates a secret from `1` to `100`, ignoring the selected difficulty. | None; secret can be outside the displayed range. | `app.py`, `new_game` branch |

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?

I used Claude (in Claude Code, agent mode inside VS Code) and GitHub Copilot. Claude did the
heavy reading and most of the fixes; Copilot was mostly inline autocomplete while I typed.

**A suggestion that was correct: the secret was being turned into a string on every other attempt.**

I went in thinking I had found one bug — the hints were backwards. What I actually reported was
messier than that: I guessed `12390921309213` and it told me to go lower, then guessed
`1239092130921` (one digit shorter) and it told me to go higher. Claude read `app.py` and said
there were really *two* overlapping bugs. The first was the one I had seen: in `check_guess()`,
the outcome label `"Too High"` was paired with the message `"Go HIGHER!"`, so both hint strings
were swapped. The second I had not spotted at all: the submit handler did
`if st.session_state.attempts % 2 == 0: secret = str(st.session_state.secret)`, so on every
even-numbered attempt the secret became text. Comparing `int > str` raises a `TypeError`, which
was caught by a `try/except TypeError` that quietly fell back to comparing the two values as
*strings*. That is why my giant guess was judged lower than 60: character by character,
`"1" < "6"`. It was correct because it explained the exact thing that had confused me — why the
hints contradicted each other between two guesses instead of just being consistently backwards.

(How I verified this is written up in section 3.)

Claude also correctly flagged, from reading the code rather than from my bug report, that
"New Game" never resets `status`/`score`/`history` and that it hardcodes `randint(1, 100)` instead
of using the selected difficulty's range.

- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

**Example 1 — it wanted to start fixing before I understood the code (out of scope).**

My first prompt was deliberately narrow: *"read through the code, and help me understand what's
going on / identify at least 3 bugs or issues, and note the relevant code location or function."*
The AI identified the bugs correctly, but it also offered to run the app and start applying the
corrections itself right away. I did not take that, because the assignment — and the part I
actually needed — was to understand *why* each bug happened and be able to point at the line that
caused it. If I had let it patch everything in the first message I would have had a working game
and nothing to write in this reflection. I asked it instead to place numbered `# FIXME` comments
at each bug site and to propose a fix *order*, so I could read the code bug by bug and decide
what to fix first. (Verification in section 3.)

**Example 2 — a fix that looked right but broke the app on submit.**

While fixing the guess box, the AI wrote `st.session_state.guess_input = ""` after handling a
guess, to clear the input for the next turn. It looks completely reasonable. Streamlit rejects it:
`StreamlitAPIException: st.session_state.guess_input cannot be modified after the widget with key
guess_input is instantiated`. What makes this worth writing down is that the suggestion was not
careless — it is the obvious thing to write, and the app still started up fine with it in place.
I replaced it with `st.form("guess_form", clear_on_submit=True)`, which is Streamlit's supported
way to clear inputs and also makes the Enter key submit the guess. The lesson I took is that
"the AI wrote something plausible and the page loads" is not evidence that it works.
(How it was actually caught, and how I checked the replacement, is in section 3.)

This is also where the Streamlit "rerun" idea finally made sense to me — the script re-runs top to
bottom on every click, so *when* you touch `session_state` relative to when the widget is created
actually matters.


---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?

My rule was that a bug was not fixed until I could re-run the exact row from my Bug Reproduction
Log and get the Expected column instead of the Actual column. Reading the diff and agreeing it
looked right was not enough — that is how the broken code got written in the first place. Bugs
that live in pure logic I checked with `pytest`; bugs that only show up through the UI (New Game,
the attempt counter, switching difficulty) I had to play. The trap I ran into is that the app
**loading** proves almost nothing: after one fix the page rendered fine, returned HTTP 200 and
logged no errors, and it still threw an exception the moment I pressed Submit. "It starts" and
"it works" turned out to be two separate checks.

- Describe at least one test you ran (manual or using pytest) and what it showed you about your code.

**pytest.** The three tests that shipped with the project could not pass at first, for a reason
that had nothing to do with the bugs: they assert `check_guess(50, 50) == "Win"`, but
`check_guess()` returned a *tuple*, `("Win", "🎉 Correct!")`. I changed the function to return just
the outcome string and moved the emoji into an `OUTCOME_MESSAGES` dict, which also gave a cleaner
split — pure logic in `logic_utils.py`, presentation in `app.py`. Then I added one test per row of
my bug table, so every bug I documented has a test that would have caught it:
`test_huge_guess_is_not_judged_as_low()` covers the `12390921309213` case from my log, and
`test_wrong_guess_never_increases_score()` covers the scoring bug that *awarded* +5 points for a
wrong guess on even-numbered attempts. Final run: **12 passed in 0.01s**.

**Simulating a full round.** The UI bugs needed something pytest alone could not give me, so I
drove the app headlessly with `streamlit.testing.v1.AppTest` — set the text box, click Submit,
read `session_state` back — and played whole games that way. This is what caught the failed fix
from section 2: clearing the box with `st.session_state.guess_input = ""` renders perfectly and
then raises `StreamlitAPIException` on submit, because a widget's state cannot be modified after
the widget is instantiated. Re-running the same simulation against the `st.form(clear_on_submit=True)`
version gave a full win, a full loss, and a New Game replay with no exception.

It also caught a bug I had never written down, because I had never played a game all the way to a
loss: losing a full round finished with a score of **-40**, since each wrong guess subtracted 5
with no lower bound. I floored the score at 0 in `update_score()` and added
`test_score_never_goes_negative()`.

The headline symptoms from my log check out the same way. An invalid guess like `abc` no longer
burns an attempt (the counter stays put), a round now ends at exactly 8 valid guesses instead of
the 15 I originally got, clicking New Game after a loss gives a board I can actually win on, and
switching to Easy regenerates the secret inside 1-20 while the prompt updates to "Guess a number
between 1 and 20" instead of the hardcoded "1 and 100".

**Verification record — every repair and the check that confirmed it.**

| # | Repair | How I verified it | Result |
|---|--------|-------------------|--------|
| 1 | New Game now resets `status`, `score` and `history`, and draws the secret from the selected difficulty's range | Played a round to a loss, clicked New Game, played again | Fresh board, `status` back to `playing`, won the next round |
| 2 | `attempts` means one thing everywhere ("valid guesses made", starting at 0); the increment moved after validation | Submitted `abc`, then played a round to the limit | Counter stayed put on bad input; round ended at exactly 8 valid guesses, not 15 |
| 3 | Logic moved out of `app.py` into `logic_utils.py` | `pytest` can import and test it without running Streamlit | 12 passed |
| 4 | `check_guess()` returns just the outcome; emoji moved to `OUTCOME_MESSAGES` | Ran the three tests the project shipped with | They pass as written, no longer blocked by the tuple mismatch |
| 5 | `parse_guess()` takes `low`/`high` and rejects out-of-range guesses | Re-ran the `12390921309213` row from my bug log | "Guess must be between 1 and 100."; `test_guess_outside_range_is_rejected()` |
| 6 | Decimals rejected instead of silently truncated | Entered `3.9` | "Whole numbers only - no decimals."; `test_decimals_are_rejected_not_truncated()` |
| 7 | Input stripped before parsing | Entered `" 50 "` | Accepted as 50; `test_surrounding_whitespace_is_accepted()` |
| 8 | Secret regenerates when difficulty changes | Switched to Easy mid-session with the debug panel open | New secret `12`, inside 1-20, counters reset |
| 9 | Prompt interpolates the real range instead of a hardcoded "1 and 100" | Read the prompt after switching to Easy | "Guess a number between 1 and 20" |
| 10 | "Hard" range widened so it is harder than Normal | Compared the two ranges | `test_hard_range_is_wider_than_normal()` |
| 11 | Scoring no longer rewards wrong guesses; score floored at 0 | Played a full losing round | Ends at 0, not -40; `test_wrong_guess_never_increases_score()`, `test_score_never_goes_negative()` |
| 12 | Running score shown during play | Read the info bar mid-round | Score visible without opening the debug panel |
| 13 | Rejected input no longer appended to `history` | Submitted `abc`, checked the debug panel | `history` stays all ints, no mixed `["abc", 50]` |
| 14 | Guess box moved into `st.form(clear_on_submit=True)` | Re-ran the full-round simulation | Box clears, Enter submits, no `StreamlitAPIException` |

The two repairs I had already made before this pass — the swapped hint messages and the secret
being cast to `str()` on alternating attempts — are covered by
`test_huge_guess_is_not_judged_as_low()` and the three original `check_guess()` tests, and I
re-confirmed them by guessing just above the secret with the debug panel open and reading the
hint direction.

- Did AI help you design or understand any tests? How?

Yes, in two fairly different ways. For design, Claude drafted the extra regression tests directly
from my Bug Reproduction Log — one test per row — which turned a table I had written for the
assignment into something that actually guards the code; I checked each one against what I had
seen while playing rather than accepting them as written. For understanding, the more useful help
was having my own verification shown to be too weak: I was treating a clean page load as proof the
fix worked. The AppTest run is what drew the line between the app starting and the app working,
and both the broken fix and the -40 score were found on that side of the line. Neither would have
been caught by the three tests the project shipped with.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

The way I would put it: **Streamlit does not update your page, it re-runs your entire script from
line 1 every single time you touch anything.** Click a button, type in a box, change a dropdown —
the whole file executes again, top to bottom. So every normal Python variable you created is
thrown away and rebuilt from scratch. `st.session_state` is the one box that survives that
re-run; it is the only place a value can live if it needs to still be there after a click.

That single idea explains almost every bug in this project. The secret number has to be in
`session_state` or it would be re-rolled on every guess. `attempts` has to be in there or it could
never count past 1. And because the script re-runs *in order*, **where** a line sits in the file
is part of its behaviour, not just a style choice:

- The status line was written above the submit handler, so Streamlit drew "Attempts left: 8"
  *before* the guess was processed. The number was always one guess stale. Nothing was wrong with
  the arithmetic — it was drawn too early. I fixed it by reserving the spot with `st.empty()` and
  filling it at the bottom of the script.
- I tried to clear the guess box with `st.session_state.guess_input = ""` after handling a guess,
  and Streamlit raised `StreamlitAPIException: cannot be modified after the widget ... is
  instantiated`. Once a widget exists in this run, its state is locked for this run. The supported
  way is `st.form(clear_on_submit=True)`, which clears on the *next* run.
- The guess box was keyed `f"guess_input_{difficulty}"`. Changing the dropdown changed the key,
  which made it a *brand new widget* with empty state, silently wiping what the player had typed.
  A widget's identity is its key.

The mental shift was realising Streamlit is not an event-driven UI where a click runs one handler.
It is a script that runs again from scratch, and `session_state` is the only memory between runs.
Once I had that, the "secret number has commitment issues" symptom stopped being mysterious.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?

**Drive the thing, do not just start it.** My instinct the whole way through was to treat "the app
loaded with no errors" as proof a fix worked, and this project punished that twice. The
`st.session_state.guess_input = ""` fix rendered a perfect page, returned HTTP 200 and logged
nothing — and threw an exception the moment I pressed Submit. Running the app end to end with
`streamlit.testing.v1.AppTest` (set the box, click Submit, read `session_state` back) also turned
up a score of **-40** on a losing round, which I had never seen because I had never actually
played a game all the way to a loss. Starting and working are two different checks, and only the
second one is worth anything.

The version of this for tests is: **ask for the real output before writing any assertion.** When I
went to cover edge cases I assumed negatives, decimals and huge numbers were already handled.
Rather than writing tests from the function signatures, we ran those inputs against the real
functions and printed what came back. The three I assumed were fine *were* fine — but the probe
also turned up three I had never thought to look for, including `int()` quietly accepting
`"5_0"` as **50** and full-width `"１０"` as **10**. Tests written from a signature only confirm
what the code already does; running the inputs first is what finds things.

- What is one thing you would do differently next time you work with AI on a coding task?

**Commit much more granularly, with real messages.** My history for most of this is `phase 1 done`,
`phase 2, step 1 wip..`, `phase 2.4` — which tells a reader nothing, and told *me* nothing when I
wanted to check what had already been fixed. At one point I had to ask the AI to re-read the
working tree because neither of us was sure which repairs were committed and which were still
loose, and a commit message I had asked for described work that was already pushed. When an AI is
changing several files at once, the commit log is the only durable record of what actually
happened, and "wip" throws that away. Next time: one commit per fix, with a message that says what
was broken and why the change fixes it.

I would also **ask for the explanation before the fix, on purpose.** I did this by accident on the
first prompt — I asked it to explain the code rather than repair it, and it offered to start
fixing immediately. Saying no there was the best decision I made on this project. If I had let it
patch everything in the first message I would have had a working game and no idea why any of it
had been broken.

- In one or two sentences, describe how this project changed the way you think about AI generated code.

I used to read AI-written code the way I read a textbook — if it looked reasonable and ran, I
assumed it was right. This project was written by an AI that was confident enough to leave a
`try/except TypeError` in place whose only purpose was to hide the bug directly above it, and the
comment at the bottom of the file still claims the code is production-ready. Now I treat
AI-generated code as a *draft by a fast, confident author who never tested it*: worth having,
much faster than starting from nothing, but the burden of proof is on me, and "it looks fine and
it runs" is the weakest evidence there is.
