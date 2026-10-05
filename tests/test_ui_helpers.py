"""Challenge 4: tests for the presentation helpers.

These cover get_proximity() and build_session_table() from logic_utils.py.
Both are pure functions with no Streamlit imports, which is the reason the
Hot/Cold banding lives there instead of inline in app.py -- it can be checked
here rather than eyeballed in the browser.
"""

import pytest

from logic_utils import (
    OUTCOME_COLORS,
    OUTCOME_MESSAGES,
    build_session_table,
    get_proximity,
)

# ---------------------------------------------------------------------------
# get_proximity
# ---------------------------------------------------------------------------


def test_exact_hit_is_labelled_exact():
    assert get_proximity(57, 57, 1, 100) == "🎯 Exact"


def test_closer_guesses_are_never_colder():
    # Walking in toward the secret must move monotonically up the bands.
    order = ["🧊 Freezing", "❄️ Cold", "🌤️ Lukewarm", "☀️ Warm", "🌶️ Hot", "🔥 Blazing", "🎯 Exact"]
    secret = 50
    previous = -1
    for guess in range(1, secret + 1):
        rank = order.index(get_proximity(guess, secret, 1, 100))
        assert rank >= previous, f"guess {guess} went colder as it got closer"
        previous = rank


def test_proximity_is_symmetric_above_and_below():
    assert get_proximity(40, 50, 1, 100) == get_proximity(60, 50, 1, 100)


def test_banding_scales_with_the_difficulty_range():
    # Being 5 away is "hot" on Hard (1-200) but not on Easy (1-20), because
    # distance is scaled to the size of the range.
    easy = get_proximity(5, 10, 1, 20)
    hard = get_proximity(95, 100, 1, 200)
    assert easy != hard


@pytest.mark.parametrize("low,high", [(1, 20), (1, 100), (1, 200)])
def test_every_guess_in_range_gets_a_label(low, high):
    for guess in range(low, high + 1):
        assert get_proximity(guess, (low + high) // 2, low, high)


def test_degenerate_range_does_not_divide_by_zero():
    # low == high would make the span 0; the helper clamps it to 1.
    assert get_proximity(5, 5, 7, 7) == "🎯 Exact"
    assert get_proximity(4, 5, 7, 7)


def test_proximity_accepts_numeric_strings():
    assert get_proximity("57", "57", 1, 100) == "🎯 Exact"


# ---------------------------------------------------------------------------
# build_session_table
# ---------------------------------------------------------------------------

def _entry(attempt, guess, outcome, proximity, score):
    return {
        "attempt": attempt,
        "guess": guess,
        "outcome": outcome,
        "proximity": proximity,
        "score": score,
    }


def test_empty_log_produces_no_rows():
    assert build_session_table([]) == []


def test_each_log_entry_becomes_one_row():
    log = [
        _entry(1, 20, "Too Low", "❄️ Cold", 0),
        _entry(2, 75, "Too High", "🌤️ Lukewarm", 0),
        _entry(3, 57, "Win", "🎯 Exact", 70),
    ]
    rows = build_session_table(log)

    assert len(rows) == 3
    assert [r["#"] for r in rows] == [1, 2, 3]
    assert [r["Guess"] for r in rows] == [20, 75, 57]
    assert rows[-1]["Result"] == OUTCOME_MESSAGES["Win"]
    assert rows[-1]["Score"] == 70


def test_rows_use_display_ready_column_names():
    rows = build_session_table([_entry(1, 20, "Too Low", "❄️ Cold", 0)])
    assert set(rows[0]) == {"#", "Guess", "Result", "Proximity", "Score"}


def test_outcome_is_rendered_as_its_message_not_its_key():
    rows = build_session_table([_entry(1, 20, "Too Low", "❄️ Cold", 0)])
    assert rows[0]["Result"] == "📈 Go HIGHER!"
    assert "Too Low" not in rows[0]["Result"]


# ---------------------------------------------------------------------------
# colour map
# ---------------------------------------------------------------------------

def test_every_outcome_has_a_colour_and_a_message():
    for outcome in ("Win", "Too High", "Too Low"):
        assert outcome in OUTCOME_COLORS
        assert outcome in OUTCOME_MESSAGES


def test_directions_are_visually_distinct():
    assert OUTCOME_COLORS["Too High"] != OUTCOME_COLORS["Too Low"]
