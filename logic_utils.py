"""Pure game logic for the Game Glitch Investigator guessing game.

This module deliberately contains no Streamlit imports. Keeping the rules
separate from the presentation layer in ``app.py`` means every function here
can be exercised by ``pytest`` without starting a server or simulating a
browser session, which is what made the bugs in this project testable.

Public API
----------
``get_range_for_difficulty``
    Map a difficulty name to the inclusive range of possible secrets.
``parse_guess``
    Validate and convert raw player input into an ``int``.
``check_guess``
    Compare a guess against the secret.
``update_score``
    Apply the scoring rules for one guess.
``get_proximity``
    Describe how close a guess landed, as a Hot/Cold label.
``build_session_table``
    Convert the round log into display-ready summary rows.

Module constants
----------------
``OUTCOME_MESSAGES``
    Player-facing message for each outcome returned by :func:`check_guess`.
``OUTCOME_COLORS``
    Streamlit colour name for each outcome, used for ``:color[...]`` markdown.
``PROXIMITY_BANDS``
    Distance thresholds backing :func:`get_proximity`.
"""

import re

# A guess is an optional sign followed by ASCII digits and nothing else.
# EDGE CASE [4]: this deliberately rejects what int() would otherwise accept --
# PEP 515 underscores ("5_0" -> 50) and non-ASCII decimal digits such as
# full-width "１０" or Arabic-Indic "١٠", both of which int() happily parses as
# 10. A player typing those did not mean to guess 50 or 10, so silently
# accepting them scores a number nobody entered.
_INTEGER_RE = re.compile(r"^[+-]?[0-9]+$")

# Message shown to the player for each outcome returned by check_guess().
OUTCOME_MESSAGES = {
    "Win": "🎉 Correct!",
    "Too High": "📉 Go LOWER!",
    "Too Low": "📈 Go HIGHER!",
}


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    """Return the inclusive range of possible secrets for a difficulty.

    Args:
        difficulty: One of ``"Easy"``, ``"Normal"`` or ``"Hard"``. Any
            unrecognised value falls back to the ``"Normal"`` range rather
            than raising, so a typo in the UI cannot crash the game.

    Returns:
        A ``(low, high)`` tuple of inclusive bounds.

    Examples:
        >>> get_range_for_difficulty("Easy")
        (1, 20)
        >>> get_range_for_difficulty("Hard")
        (1, 200)
        >>> get_range_for_difficulty("Nonsense")
        (1, 100)

    Note:
        ``"Hard"`` originally returned ``(1, 50)`` -- a *narrower* range than
        Normal, which made Hard the easiest setting. It now returns the widest
        range, so difficulty increases monotonically.
    """
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 200
    return 1, 100


def parse_guess(
    raw: str,
    low: int | None = None,
    high: int | None = None,
) -> tuple[bool, int | None, str | None]:
    """Validate raw player input and convert it into an integer guess.

    Input is rejected rather than coerced wherever coercion would score the
    player on a number they did not type. Surrounding whitespace is stripped,
    but decimals, non-ASCII digits and underscore separators are all refused.

    Args:
        raw: The text the player submitted. ``None`` and non-``str`` values
            are handled without raising.
        low: Lower inclusive bound, or ``None`` to skip the range check.
        high: Upper inclusive bound, or ``None`` to skip the range check.

    Returns:
        A ``(ok, guess, error)`` tuple. On success, ``ok`` is ``True``,
        ``guess`` is the parsed ``int`` and ``error`` is ``None``. On failure,
        ``ok`` is ``False``, ``guess`` is ``None`` and ``error`` is a
        player-facing message. Exactly one of ``guess`` / ``error`` is ever
        non-``None``, so callers never have to guess which to trust.

    Examples:
        >>> parse_guess(" 50 ", 1, 100)
        (True, 50, None)
        >>> parse_guess("3.9", 1, 100)
        (False, None, 'Whole numbers only - no decimals.')
        >>> parse_guess("150", 1, 100)
        (False, None, 'Guess must be between 1 and 100.')
        >>> parse_guess("", 1, 100)
        (False, None, 'Enter a guess.')

    Note:
        Both bounds must be supplied for the range check to run. Passing only
        one is treated as "no bounds", which is why the Streamlit caller always
        passes the pair returned by :func:`get_range_for_difficulty`.
    """
    # FIX [7]: input is stripped before parsing, so " 50 " is accepted on
    # purpose rather than by luck of int()'s own whitespace handling.
    if raw is None:
        return False, None, "Enter a guess."

    # EDGE CASE [5]: accept any type without crashing. Streamlit always hands
    # this function a str, but passing an int or a float used to raise
    # AttributeError ('int' object has no attribute 'strip') rather than
    # returning the (ok, value, error) contract every caller expects.
    if not isinstance(raw, str):
        raw = str(raw)

    raw = raw.strip()

    if raw == "":
        return False, None, "Enter a guess."

    # FIX [6]: decimals are REJECTED instead of silently truncated. "3.9" used
    # to become 3, scoring the player on a number they never typed.
    # COLLAB: Claude Code suggested rounding instead; I chose rejection because
    # a guessing game should never score a number the player did not enter.
    if "." in raw:
        return False, None, "Whole numbers only - no decimals."

    if not _INTEGER_RE.match(raw):
        return False, None, "That is not a number."

    try:
        value = int(raw)
    except ValueError:  # unreachable given the regex, kept as a safety net
        return False, None, "That is not a number."

    # FIX [5]: range validation. Any integer used to be legal, which is how a
    # guess of 12390921309213 got accepted in a 1-100 game.
    # COLLAB: Claude Code found this from my bug table entry (the 12-trillion
    # guess) and noted parse_guess had no access to low/high at all, so the
    # signature needed the bounds passed in. Verified with the unit tests in
    # tests/test_game_logic.py.
    if low is not None and high is not None and not (low <= value <= high):
        return False, None, f"Guess must be between {low} and {high}."

    return True, value, None


def check_guess(guess: int | str, secret: int | str) -> str:
    """Compare a guess against the secret and return the outcome.

    Args:
        guess: The player's guess. Numeric strings are accepted and coerced.
        secret: The number to beat. Numeric strings are accepted and coerced.

    Returns:
        One of ``"Win"``, ``"Too High"`` or ``"Too Low"``. Use
        :data:`OUTCOME_MESSAGES` to turn the outcome into player-facing text
        and :data:`OUTCOME_COLORS` to colour it.

    Raises:
        ValueError: If either argument cannot be converted to an ``int``.

    Examples:
        >>> check_guess(50, 50)
        'Win'
        >>> check_guess(60, 50)
        'Too High'
        >>> check_guess(12390921309213, 60)
        'Too High'

    Note:
        Both arguments are coerced with ``int()`` on purpose. The original
        version compared them as-is inside a ``try/except TypeError`` whose
        fallback compared them as *text*, so ``"12390921309213" < "60"`` --
        character by character, ``"1" < "6"`` -- and a twelve-trillion guess
        was reported as too low. Coercing first makes that fallback impossible
        rather than merely unlikely.
    """
    guess = int(guess)
    secret = int(secret)

    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """Apply the scoring rules for a single guess and return the new score.

    Winning sooner is worth more: the bonus starts at 100 and loses 10 points
    per attempt already spent. A wrong guess in either direction costs 5.

    Args:
        current_score: The score before this guess.
        outcome: An outcome from :func:`check_guess`. Unrecognised values
            leave the score unchanged rather than raising.
        attempt_number: Which attempt this was, 1-based.

    Returns:
        The updated score, clamped to ``0`` or above. A winning bonus is
        clamped to the range ``10..100``.

    Examples:
        >>> update_score(0, "Win", 1)
        100
        >>> update_score(0, "Win", 4)
        70
        >>> update_score(0, "Too Low", 1)
        0
        >>> update_score(42, "Sideways", 1)
        42

    Note:
        Two bugs lived here. ``"Too High"`` used to *award* +5 points on
        even-numbered attempts while ``"Too Low"`` always cost 5, so wrong
        guesses were sometimes rewarded; and neither the running score nor the
        win bonus had an upper or lower clamp, so a losing round could finish
        at -40 and ``update_score(0, "Win", 0)`` returned 110.
    """
    if outcome == "Win":
        # EDGE CASE [6]: the bonus is clamped at BOTH ends. Only the lower
        # bound existed, so a non-positive attempt_number scored above the
        # intended 100 maximum -- update_score(0, "Win", 0) returned 110.
        points = 100 - 10 * (attempt_number - 1)
        points = max(10, min(100, points))
        return current_score + points

    # FIX [11]: the score is floored at 0. A wrong guess used to subtract 5 with
    # no lower bound, so losing a round could end at -40. (The earlier half of
    # this fix removed the branch that AWARDED +5 for a "Too High" guess on even
    # attempts and made the penalty symmetric for both wrong directions.)
    # COLLAB: Claude Code found the -40 by simulating a full losing round with
    # streamlit.testing AppTest -- I had not played a losing game all the way
    # through, so I never saw a negative score.
    if outcome in ("Too High", "Too Low"):
        return max(0, current_score - 5)

    return current_score


# ---------------------------------------------------------------------------
# Challenge 4: presentation helpers.
#
# These are additive. check_guess(), parse_guess() and update_score() are
# untouched, so the core game logic and all 64 existing tests are unaffected.
# Keeping these as pure functions here (rather than inline in app.py) means the
# Hot/Cold banding is unit-tested instead of eyeballed in the browser.
# ---------------------------------------------------------------------------

# Streamlit colour name used for each outcome, for :color[...] markdown.
OUTCOME_COLORS = {
    "Win": "green",
    "Too High": "red",
    "Too Low": "blue",
}

# (max distance as a fraction of the range, label). First match wins.
PROXIMITY_BANDS = [
    (0.02, "🔥 Blazing"),
    (0.05, "🌶️ Hot"),
    (0.12, "☀️ Warm"),
    (0.25, "🌤️ Lukewarm"),
    (0.50, "❄️ Cold"),
    (1.00, "🧊 Freezing"),
]


def get_proximity(guess: int | str, secret: int | str, low: int, high: int) -> str:
    """Describe how close a guess landed, as a Hot/Cold label.

    Distance is expressed as a fraction of the range rather than in absolute
    units, so "hot" means the same thing on Easy (1-20) as it does on Hard
    (1-200). The thresholds live in :data:`PROXIMITY_BANDS`.

    Args:
        guess: The player's guess. Numeric strings are accepted.
        secret: The number to beat. Numeric strings are accepted.
        low: Lower inclusive bound of the current difficulty's range.
        high: Upper inclusive bound of the current difficulty's range.

    Returns:
        A label such as ``"🎯 Exact"``, ``"🔥 Blazing"`` or ``"🧊 Freezing"``.
        The label is purely cosmetic and never affects scoring.

    Examples:
        >>> get_proximity(57, 57, 1, 100)
        '🎯 Exact'
        >>> get_proximity(60, 57, 1, 100)
        '🌶️ Hot'
        >>> get_proximity(1, 57, 1, 100)
        '🧊 Freezing'

    Note:
        The span is clamped to a minimum of 1 so a degenerate range where
        ``low == high`` cannot raise ``ZeroDivisionError``.
    """
    guess, secret = int(guess), int(secret)

    if guess == secret:
        return "🎯 Exact"

    span = max(1, int(high) - int(low))
    ratio = abs(guess - secret) / span

    for limit, label in PROXIMITY_BANDS:
        if ratio <= limit:
            return label

    return PROXIMITY_BANDS[-1][1]


def build_session_table(log: list[dict]) -> list[dict]:
    """Convert the round log into display-ready rows for the summary table.

    Args:
        log: The per-guess records collected in ``st.session_state.log``, one
            dict per valid guess, each with ``attempt``, ``guess``,
            ``outcome``, ``proximity`` and ``score`` keys.

    Returns:
        A list of dicts keyed by column heading -- ``"#"``, ``"Guess"``,
        ``"Result"``, ``"Proximity"`` and ``"Score"`` -- ready to hand to
        ``st.dataframe``. An empty log returns an empty list.

    Examples:
        >>> entry = {"attempt": 1, "guess": 20, "outcome": "Too Low",
        ...          "proximity": "❄️ Cold", "score": 0}
        >>> build_session_table([entry])[0]["Result"]
        '📈 Go HIGHER!'
        >>> build_session_table([])
        []

    Note:
        Each outcome is rendered through :data:`OUTCOME_MESSAGES`, so the table
        shows the player-facing message rather than the internal key.
    """
    return [
        {
            "#": entry["attempt"],
            "Guess": entry["guess"],
            "Result": OUTCOME_MESSAGES[entry["outcome"]],
            "Proximity": entry["proximity"],
            "Score": entry["score"],
        }
        for entry in log
    ]
