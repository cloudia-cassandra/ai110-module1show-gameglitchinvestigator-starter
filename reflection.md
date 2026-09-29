# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?


- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").
1. would input "12390921309213" and it said to go lower, tried "1239092130921" and said go higher, tried "12390921309210" and said higher i think, all for it to take 15 attemps, and tell me the number was 60
2. after 15 attempts, game is done, says "game over. start a new game to try again" -> click new game, and won't let me play again
3. "new game" ignores selected difficulty
4. "
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
Claude and GitHub Copilot

- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
1. "Hint direction is inverted"
When guess is too high, it tells user to go higher; when too low, it tells user to go lower
2. "Hints become inconsistent on alternating attempts" (str vs int compare)
Hints feel random/wrong even for obvious guesses
3. "New game ignores selected difficulty range"
Sidebar may say Easy range 1-20, but secret can be outside that range
4. "New game doesn't reset game status"
After winning/losing, clicking New Game still leaves user stuck in already won/game over.


- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.
1. Wanted to start running the app and create the corrections itself, from the first prompt 
"read through the code, and help me understand what's going on
identify at least 3 bugs or issues, and note the relevant code location or function"
2. 


---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
