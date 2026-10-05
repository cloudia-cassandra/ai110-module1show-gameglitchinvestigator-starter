"""Streamlit front end for the Game Glitch Investigator guessing game.

This module is the presentation layer only: it owns widgets, ``session_state``
and rendering. Every game rule lives in :mod:`logic_utils`, which has no
Streamlit imports and is unit-tested directly.

Comment markers used throughout:

``# FIX [n]``
    A repair to one of the bugs documented in ``reflection.md``.
``# EDGE CASE [n]``
    Hardening added for Challenge 1 (edge-case testing).
``# UI [n]``
    A Challenge 4 presentation enhancement.
``# COLLAB``
    How a bug was found and verified while pairing with an AI assistant.
"""

import random

import streamlit as st

from logic_utils import (
    OUTCOME_COLORS,
    OUTCOME_MESSAGES,
    build_session_table,
    check_guess,
    get_proximity,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# FIX [8]: the active difficulty is tracked in session_state so the secret can
# be regenerated whenever it changes. Before, the secret was drawn once per
# session, so switching to Easy left a 1-100 secret behind a sidebar promising
# "Range: 1 to 20" -- often literally unguessable.
# Changing difficulty starts a new round, so the rest of the round state resets
# with it; otherwise you would carry a half-used attempt counter into a game
# with a different limit.
# COLLAB: Claude Code found this one by reading the code, not from my bug
# report -- I had only noticed the stale "1 and 100" prompt text. I verified by
# switching difficulty with the debug panel open and watching the secret change.
if "difficulty" not in st.session_state:
    st.session_state.difficulty = difficulty

if "secret" not in st.session_state or st.session_state.difficulty != difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.status = "playing"
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.log = []

# FIX [2a]: attempts now starts at 0, matching the New Game reset path. It has
# ONE meaning everywhere: "valid guesses made so far". It used to start at 1
# here but 0 after New Game, so the same game had two different starting states.
# COLLAB: Claude Code pointed out that the same variable was being read as
# "guesses used", "guesses used + 1" and "submit clicks" on different lines, so
# we picked one definition and changed all four sites in a single pass instead
# of patching them one at a time.
if "attempts" not in st.session_state:
    st.session_state.attempts = 0

# These stay as first-run defaults; the difficulty-change block above owns
# resetting them mid-session.
if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

# UI [3]: a richer per-guess log that backs the session summary table.
# This is ADDITIVE -- `history` keeps its original shape (a list of ints) so
# nothing that reads it, including the debug panel, changes behaviour.
if "log" not in st.session_state:
    st.session_state.log = []

st.subheader("Make a guess")

# FIX [9]: the range is interpolated from the difficulty instead of hardcoded
# to "1 and 100", so the prompt and the sidebar can no longer disagree.
# FIX [2d]: "Attempts left" is correct now purely because attempts starts at 0
# (see 2a) -- the arithmetic here never changed. A fresh game said "7 left" out
# of 8 before.
# FIX [12]: the running score is shown during play. It used to appear only in
# the debug expander and in the final win/lose message.
# COLLAB: Claude Code flagged 2d as already-fixed-by-2a rather than a separate
# edit, which is why there is no new arithmetic in this block.
# FIX [15]: the status line is reserved with st.empty() here and filled in at
# the BOTTOM of the script, after the guess has been handled. Written inline,
# it rendered before the submit handler ran, so "Attempts left" and "Score"
# were always one guess stale -- guess once and it still read "8 left".
# COLLAB: this one is not from my original bug table. It turned up when Claude
# Code ran a scripted demo game to collect real numbers for the README
# walkthrough, and the captured output showed the counter not moving.
status_box = st.empty()


def render_status():
    """Render the metrics row and attempts progress bar.

    UI [1]: the plain ``st.info()`` status line is now three metric tiles plus
    a progress bar, drawn into the reserved ``st.empty()`` placeholder. Same
    numbers, scannable at a glance instead of buried in a sentence.
    """
    with status_box.container():
        used = st.session_state.attempts
        left = attempt_limit - used

        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 Range", f"{low} – {high}")
        m2.metric("🎲 Attempts left", left, delta=f"-{used}" if used else None)
        m3.metric("⭐ Score", st.session_state.score)

        # The bar drains as attempts are used, and turns the caption red once
        # the player is down to the last two guesses.
        st.progress(max(0.0, left / attempt_limit))
        if 0 < left <= 2:
            st.caption(f":red[⚠️ Only {left} attempt(s) left!]")


render_status()


def render_session_table():
    """Render the session summary table for the current round.

    UI [3]: shows every guess with its result, Hot/Cold proximity and the
    running score. Previously the only record of past guesses was a raw Python
    list inside the debug expander. Renders nothing if no guesses were made.
    """
    if not st.session_state.log:
        return

    st.markdown("#### 📋 Session summary")
    st.dataframe(
        build_session_table(st.session_state.log),
        hide_index=True,
        width="stretch",
    )

    guesses = [e["guess"] for e in st.session_state.log]
    best = min(guesses, key=lambda g: abs(g - st.session_state.secret))
    st.caption(
        f"Guesses: {len(guesses)}  |  "
        f"Closest: {best}  |  "
        f"Range tried: {min(guesses)} – {max(guesses)}"
    )


with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

col1, col2 = st.columns(2)
with col1:
    new_game = st.button("New Game 🔁")
with col2:
    show_hint = st.checkbox("Show hint", value=True)

# FIX [1]: New Game now resets EVERY piece of round state, not just attempts and
# secret. Leaving status as "lost" was what made the game unplayable after the
# first loss -- the status guard below st.stop()ed on every rerun forever.
# The secret also uses the current difficulty's range instead of a hardcoded
# 1-100, so an Easy game can no longer pick a secret outside the stated 1-20.
# COLLAB: I hit this while playing (clicked New Game after "Game over" and the
# board stayed dead); Claude Code in agent mode traced it to the missing status
# reset and the st.stop() guard. I verified by losing a round on purpose and
# confirming New Game gives a fresh, playable board.
if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.status = "playing"
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.log = []
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    # UI [3]: the finished round's table stays on screen instead of the board
    # going blank, so the player can review how they narrowed it down.
    render_session_table()
    st.stop()

# FIX [14]: the guess box lives in a form with clear_on_submit instead of a
# bare text_input keyed to difficulty. The old key f"guess_input_{difficulty}"
# meant changing difficulty built a brand new widget and silently wiped what
# the player had typed; the box also kept the previous guess after submitting.
# The form clears itself and makes Enter submit the guess.
# COLLAB: my first attempt (with Claude Code) was to assign
# st.session_state.guess_input = "" after handling the guess. Streamlit threw
# StreamlitAPIException: a widget's state cannot be modified after the widget
# is instantiated. I only caught it because we simulated a full round with
# streamlit.testing AppTest rather than trusting the page to load -- the app
# rendered fine and only broke on submit. st.form(clear_on_submit=True) is the
# supported way to do this.
with st.form("guess_form", clear_on_submit=True):
    raw_guess = st.text_input("Enter your guess:")
    submit = st.form_submit_button("Submit Guess 🚀")

if submit:
    # FIX [5]: the difficulty's bounds are passed in so out-of-range guesses
    # are rejected rather than scored.
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        # FIX [13]: rejected input is no longer appended to history. It used to
        # push the raw STRING while valid guesses pushed ints, leaving a mixed
        # list like ["abc", 50, "", 70]. A rejected entry was never a guess.
        # COLLAB: Claude Code caught the type mismatch while listing remaining
        # bugs; it never showed up in play because history only renders in the
        # debug expander.
        st.error(err)
    else:
        # FIX [2b]: the increment moved here, AFTER validation. It used to run
        # before parse_guess, so a typo or an empty box cost the player a turn.
        # FIX [2c]: this also repairs the out-of-attempts check below. That
        # check lives in this valid-guess branch, but the counter used to climb
        # on invalid input too, so a round ending in typos could sail past
        # attempt_limit and never end. Counting only valid guesses makes the
        # check correct where it already sits -- no second fix needed.
        # COLLAB: Claude Code spotted that 2b and 2c were the same root cause;
        # I had logged them separately in my bug table as two bugs.
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        outcome = check_guess(guess_int, st.session_state.secret)
        proximity = get_proximity(guess_int, st.session_state.secret, low, high)

        # UI [4]: colour-coded hint with a Hot/Cold proximity badge. The hint
        # used to be a single amber st.warning() for every outcome, so "too
        # high" and "too low" looked identical at a glance and gave no sense of
        # whether the player was closing in. Direction now has its own colour
        # (red = too high, blue = too low, green = win) via :color[...] markdown,
        # and the badge says how close the guess landed.
        if show_hint:
            color = OUTCOME_COLORS[outcome]
            st.markdown(
                f"### :{color}[{OUTCOME_MESSAGES[outcome]}]  &nbsp; {proximity}"
            )

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        # UI [3]: record the guess for the session summary table.
        st.session_state.log.append(
            {
                "attempt": st.session_state.attempts,
                "guess": guess_int,
                "outcome": outcome,
                "proximity": proximity,
                "score": st.session_state.score,
            }
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

# FIX [15]: redraw the status line now that the guess has been processed.
render_status()

render_session_table()

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
