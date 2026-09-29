def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    # FIXME: Logic breaks here - every function in this module is still an unimplemented stub, so all three tests in tests/test_game_logic.py fail with NotImplementedError; move the real (bug-fixed) bodies over from app.py and have app.py import them instead of defining its own copies.
    # FIXME: Logic breaks here - contract mismatch: this docstring and app.py return an (outcome, message) TUPLE, but the tests assert `result == "Win"`, a bare string; pick one shape - simplest is to return just the outcome string here and build the emoji message in app.py.
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    raise NotImplementedError("Refactor this function from app.py into logic_utils.py")
