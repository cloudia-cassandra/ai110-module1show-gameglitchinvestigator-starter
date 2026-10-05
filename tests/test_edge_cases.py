"""Challenge 1: Advanced Edge-Case Testing.

Three edge cases were chosen because each one is a DIFFERENT way for input to
look valid and still be wrong:

  1. Negative numbers      -- parse as perfectly good ints, but fall outside
                              every difficulty range, so the range check is the
                              only thing standing between them and the board.
  2. Decimals              -- "3.9" used to be truncated to 3, scoring the
                              player on a number they never typed.
  3. Extremely large values -- the original string-comparison bug judged
                              12390921309213 as LOWER than 60, and nothing
                              capped the magnitude of a guess.

Probing those three turned up three more that were still live, grouped at the
bottom: int()-permissive formats, non-string input, and an uncapped win bonus.
"""

import pytest

from logic_utils import check_guess, parse_guess, update_score

LOW, HIGH = 1, 100


# ---------------------------------------------------------------------------
# Edge case 1: negative numbers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["-1", "-5", "-100", "-999999"])
def test_negative_guesses_are_rejected(raw):
    ok, value, err = parse_guess(raw, LOW, HIGH)
    assert ok is False
    assert value is None
    assert err == f"Guess must be between {LOW} and {HIGH}."


def test_negative_zero_is_rejected_like_zero():
    # "-0" parses to 0, which is below the range -- it must not sneak through.
    assert parse_guess("-0", LOW, HIGH)[0] is False
    assert parse_guess("0", LOW, HIGH)[0] is False


def test_check_guess_still_orders_negatives_correctly():
    # Even if a negative reached check_guess, the comparison must stay numeric.
    assert check_guess(-10, 50) == "Too Low"
    assert check_guess(-10, -50) == "Too High"


# ---------------------------------------------------------------------------
# Edge case 2: decimals
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["3.9", "50.0", "0.5", ".5", "50.", "-2.5"])
def test_decimals_are_rejected_never_truncated(raw):
    ok, value, err = parse_guess(raw, LOW, HIGH)
    assert ok is False
    assert value is None
    assert err == "Whole numbers only - no decimals."


def test_decimal_is_not_silently_rounded_to_a_valid_guess():
    # The original bug: int(float("3.9")) == 3, a legal guess the player
    # never made. Nothing may come back as a usable value.
    assert parse_guess("3.9", LOW, HIGH)[1] is None


# ---------------------------------------------------------------------------
# Edge case 3: extremely large values
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    ["101", "12390921309213", "9" * 100, str(2**64), str(10**1000)],
)
def test_oversized_guesses_are_rejected(raw):
    ok, value, err = parse_guess(raw, LOW, HIGH)
    assert ok is False
    assert value is None
    assert err == f"Guess must be between {LOW} and {HIGH}."


def test_huge_values_compare_numerically_not_as_text():
    # The original bug compared "12390921309213" to "60" character by
    # character, and "1" < "6" made 12 trillion look smaller than 60.
    assert check_guess(12390921309213, 60) == "Too High"
    assert check_guess(10**1000, 50) == "Too High"
    assert check_guess(9, 60) == "Too Low"


def test_huge_values_do_not_raise():
    # Python ints are arbitrary precision, so this must not overflow or hang.
    assert check_guess(10**5000, 10**5000) == "Win"


# ---------------------------------------------------------------------------
# Edge case 4: formats int() accepts but a player never means
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw",
    [
        "5_0",      # PEP 515 underscore -> int() reads 50
        "1_0",      # -> 10
        "１０",  # full-width digits -> int() reads 10
        "١٠",  # Arabic-Indic digits -> int() reads 10
    ],
)
def test_intish_strings_are_rejected(raw):
    ok, value, err = parse_guess(raw, LOW, HIGH)
    assert ok is False
    assert value is None
    assert err == "That is not a number."


@pytest.mark.parametrize("raw", ["+50", "00050", " 50 ", "\t50\n"])
def test_harmless_formatting_is_still_accepted(raw):
    # Rejecting the exotic formats above must not break ordinary typing.
    assert parse_guess(raw, LOW, HIGH) == (True, 50, None)


@pytest.mark.parametrize("raw", ["1e3", "0x32", "inf", "nan", "abc", "50 50", ""])
def test_non_numeric_input_is_rejected_gracefully(raw):
    ok, value, err = parse_guess(raw, LOW, HIGH)
    assert ok is False
    assert value is None
    assert isinstance(err, str) and err  # always a message, never a crash


@pytest.mark.parametrize("raw", ["", "   ", "\t", "\n", None])
def test_blank_input_asks_for_a_guess(raw):
    ok, value, err = parse_guess(raw, LOW, HIGH)
    assert ok is False
    assert value is None
    assert err == "Enter a guess."


# ---------------------------------------------------------------------------
# Edge case 5: non-string input
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", [50, 50.0, True])
def test_non_string_input_does_not_raise(raw):
    # Streamlit always passes a str, but the contract should hold regardless.
    # This used to raise AttributeError: 'int' object has no attribute 'strip'.
    ok, value, err = parse_guess(raw, LOW, HIGH)
    assert isinstance(ok, bool)
    assert err is None or isinstance(err, str)


def test_parse_guess_without_bounds_skips_range_check():
    # low/high are optional; omitting them must not crash or invent a range.
    assert parse_guess("12390921309213") == (True, 12390921309213, None)


# ---------------------------------------------------------------------------
# Edge case 6: scoring at the boundaries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("attempt", [0, -1, -100])
def test_win_bonus_is_capped_at_100(attempt):
    # update_score(0, "Win", 0) used to return 110, above the intended max.
    assert update_score(0, "Win", attempt) <= 100


@pytest.mark.parametrize("attempt", [10, 50, 1000])
def test_win_bonus_never_falls_below_10(attempt):
    assert update_score(0, "Win", attempt) == 10


def test_score_floor_holds_across_a_whole_losing_round():
    score = 0
    for attempt in range(1, 9):
        score = update_score(score, "Too Low", attempt)
    assert score == 0


def test_unknown_outcome_leaves_score_untouched():
    assert update_score(42, "Sideways", 1) == 42
