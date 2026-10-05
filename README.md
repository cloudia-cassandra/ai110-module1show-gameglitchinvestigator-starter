# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [ ] Describe the game's purpose.
- [ ] Detail which bugs you found.
- [ ] Explain what fixes you applied.

## 📸 Demo Walkthrough

A sample game on **Normal** difficulty (range 1-100, 8 attempts). The secret for this
walkthrough is **57** — visible in the Developer Debug Info panel. Every message below is the
real output from the app, not a paraphrase.

1. **Start the app.** The status line reads
   `Guess a number between 1 and 100. Attempts left: 8 | Score: 0`.
   The range comes from the difficulty selected in the sidebar, so choosing Easy changes it to
   1 to 20 and starts a fresh round.

2. **Enter `abc` and submit.** The game rejects it with **"That is not a number."**
   Attempts left stays at **8** — invalid input does not cost a turn.

3. **Enter `150` and submit.** The game rejects it with
   **"Guess must be between 1 and 100."** Attempts left is still **8**. Out-of-range guesses are
   refused instead of being scored.

4. **Guess `40`.** The hint reads **"📈 Go HIGHER!"** because 40 is below the secret.
   Attempts left drops to **7**.

5. **Guess `70`.** The hint reads **"📉 Go LOWER!"** because 70 is above the secret.
   Attempts left drops to **6**. The two hints point toward each other, narrowing the range to
   41-69.

6. **Guess `60`.** Still **"📉 Go LOWER!"** — closer, but high. Attempts left drops to **5**.

7. **Guess `57`.** The hint reads **"🎉 Correct!"**, balloons animate, and the game shows
   **"You won! The secret was 57. Final score: 70"**. The score is 70 because winning on the
   4th valid attempt scores `100 - 10 × (4 - 1)`.

8. **The round is over.** The guess box disappears and the app shows
   *"You already won. Start a new game to play again."* No further guesses are accepted.

9. **Click "New Game 🔁".** Attempts, score, history and status all reset, and a new secret is
   drawn from the current difficulty's range. The board is immediately playable again — this is
   the bug that originally made the game unusable after a single round.

**Losing a round:** submit 8 valid wrong guesses and the game ends with
*"Out of attempts! The secret was N. Score: 0"*, then stops accepting input until New Game is
clicked.

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
$ python -m pytest tests/ -q
............                                                             [100%]
12 passed in 0.01s
```

The suite covers the three original `check_guess()` cases plus one regression test per row of the
bug reproduction log in `reflection.md`, so every documented bug has a test that would have caught
it — including `test_huge_guess_is_not_judged_as_low()` for the string-comparison bug and
`test_score_never_goes_negative()` for the scoring bug.

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
