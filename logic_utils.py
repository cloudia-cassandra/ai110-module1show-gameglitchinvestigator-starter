"""Pure game logic for the number guessing game (no Streamlit imports)."""

# Message shown to the player for each outcome returned by check_guess().
OUTCOME_MESSAGES = {
    "Win": "🎉 Correct!",
    "Too High": "📉 Go LOWER!",
    "Too Low": "📈 Go HIGHER!",
}


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 200
    return 1, 100


def parse_guess(raw: str, low: int = None, high: int = None):
    """
    Parse user input into an int guess, optionally bounded by low/high.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    # FIX [7]: input is stripped before parsing, so " 50 " is accepted on
    # purpose rather than by luck of int()'s own whitespace handling.
    if raw is None:
        return False, None, "Enter a guess."

    raw = raw.strip()

    if raw == "":
        return False, None, "Enter a guess."

    # FIX [6]: decimals are REJECTED instead of silently truncated. "3.9" used
    # to become 3, scoring the player on a number they never typed.
    # COLLAB: Claude Code suggested rounding instead; I chose rejection because
    # a guessing game should never score a number the player did not enter.
    if "." in raw:
        return False, None, "Whole numbers only - no decimals."

    try:
        value = int(raw)
    except ValueError:
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


def check_guess(guess, secret):
    """
    Compare guess to secret and return the outcome as a string.

    Returns one of: "Win", "Too High", "Too Low"
    Both arguments are coerced to int, so a TypeError can never push this
    into a string comparison where "9" > "50".
    """
    guess = int(guess)
    secret = int(secret)

    if guess == secret:
        return "Win"
    if guess > secret:
        return "Too High"
    return "Too Low"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number (1-based)."""
    if outcome == "Win":
        points = 100 - 10 * (attempt_number - 1)
        if points < 10:
            points = 10
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
