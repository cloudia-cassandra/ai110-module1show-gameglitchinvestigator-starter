from logic_utils import check_guess

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    result = check_guess(50, 50)
    assert result == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    result = check_guess(60, 50)
    assert result == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    result = check_guess(40, 50)
    assert result == "Too Low"


# --- Tests added while fixing the bugs found in the bug reproduction log. ---
# COLLAB: Claude Code drafted these from the bug table in reflection.md, one
# test per row, so each documented bug has a test that would have caught it.
# I reviewed each one against what I actually saw while playing.

from logic_utils import parse_guess, update_score, get_range_for_difficulty


def test_huge_guess_is_not_judged_as_low():
    # The original bug: "12390921309213" compared as a STRING against "60",
    # so "1" < "6" made 12 trillion look smaller than 60.
    assert check_guess(12390921309213, 60) == "Too High"


def test_guess_outside_range_is_rejected():
    # The game accepted any integer, so 12 trillion was a legal 1-100 guess.
    ok, value, err = parse_guess("12390921309213", 1, 100)
    assert ok is False
    assert value is None
    assert "between 1 and 100" in err


def test_decimals_are_rejected_not_truncated():
    # "3.9" used to silently become 3.
    ok, value, _ = parse_guess("3.9", 1, 100)
    assert ok is False
    assert value is None


def test_surrounding_whitespace_is_accepted():
    assert parse_guess(" 50 ", 1, 100) == (True, 50, None)


def test_empty_input_is_rejected():
    assert parse_guess("", 1, 100)[0] is False
    assert parse_guess(None, 1, 100)[0] is False


def test_wrong_guess_never_increases_score():
    # "Too High" used to AWARD +5 points on even-numbered attempts.
    for attempt in range(1, 9):
        assert update_score(100, "Too High", attempt) <= 100
        assert update_score(100, "Too Low", attempt) <= 100


def test_score_never_goes_negative():
    # A full losing round used to finish at -40.
    assert update_score(0, "Too Low", 1) == 0


def test_winning_sooner_scores_higher():
    assert update_score(0, "Win", 1) > update_score(0, "Win", 5)


def test_hard_range_is_wider_than_normal():
    # "Hard" used to return 1-50, a NARROWER range than Normal's 1-100.
    _, normal_high = get_range_for_difficulty("Normal")
    _, hard_high = get_range_for_difficulty("Hard")
    assert hard_high > normal_high
