import random
import streamlit as st

def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        # FIXME: Logic breaks here - "Hard" returns the NARROW 1-50 range while "Normal" returns 1-100, making Hard the easiest setting; it should return a range wider than Normal (e.g. 1, 200) so difficulty actually increases.
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess, secret):
    if guess == secret:
        return "Win", "🎉 Correct!"

    try:
        # FIXME: Logic breaks here - the two branches below are swapped, so a guess ABOVE the secret is told to go HIGHER and every hint points away from the answer; guess > secret must return ("Too High", "Go LOWER!") and the else must return ("Too Low", "Go HIGHER!").
        if guess > secret:
            return "Too High", "📈 Go HIGHER!"
        else:
            return "Too Low", "📉 Go LOWER!"
    # FIXME: Logic breaks here - this fallback hides the type error by re-comparing as strings, where "9" > "50" is True, so mismatched types produce confidently wrong hints; delete the fallback and guarantee check_guess always receives two ints (coerce or reject in parse_guess instead).
    except TypeError:
        g = str(guess)
        if g == secret:
            return "Win", "🎉 Correct!"
        if g > secret:
            return "Too High", "📈 Go HIGHER!"
        return "Too Low", "📉 Go LOWER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    if outcome == "Win":
        # FIXME: Logic breaks here - attempt_number is already 1-based, so the +1 overcharges by one attempt and a first-try win scores 80 instead of 100; it should be points = 100 - 10 * (attempt_number - 1).
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        # FIXME: Logic breaks here - a "Too High" guess ADDS +5 on even-numbered attempts, randomly rewarding wrong answers while "Too Low" always costs -5; drop this parity branch so both wrong outcomes apply the same penalty (return current_score - 5).
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score

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

# FIXME: Logic breaks here - the secret is generated once on the first run only, so switching difficulty later leaves a secret outside the new range and the game is unwinnable; also track the active difficulty in session_state and regenerate the secret whenever it changes.
if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

# FIXME: Logic breaks here - attempts starts at 1 while the New Game path resets it to 0, so the very first game shows and allows one fewer attempt than the limit; initialize it to 0 to match the reset path.
if "attempts" not in st.session_state:
    st.session_state.attempts = 1

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

st.subheader("Make a guess")

st.info(
    # FIXME: Logic breaks here - the range is hardcoded to 1-100 and ignores the low/high already computed from difficulty, contradicting the sidebar; interpolate them instead: f"Guess a number between {low} and {high}. ".
    f"Guess a number between 1 and 100. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

# FIXME: Logic breaks here - New Game resets only attempts and secret, leaving status/score/history from the last round, so after a win or loss the rerun hits the status guard below and st.stop()s forever; this block must also set status to "playing", score to 0 and history to [].
if new_game:
    st.session_state.attempts = 0
    # FIXME: Logic breaks here - hardcodes randint(1, 100) instead of the current difficulty's range, so a new Easy or Hard game can pick a secret outside the range shown to the player; use random.randint(low, high).
    st.session_state.secret = random.randint(1, 100)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    # FIXME: Logic breaks here - the attempt counter increments before parse_guess runs, so invalid input like "abc" or an empty box burns a turn; move this increment into the else branch that handles a successfully parsed guess.
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    else:
        st.session_state.history.append(guess_int)

        # FIXME: Logic breaks here - on even attempts the secret is cast to a str before comparison, forcing check_guess into its string-comparison fallback so the hints flip meaning every other turn; delete this whole if/else and pass st.session_state.secret straight to check_guess.
        if st.session_state.attempts % 2 == 0:
            secret = str(st.session_state.secret)
        else:
            secret = st.session_state.secret

        outcome, message = check_guess(guess_int, secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
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

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
