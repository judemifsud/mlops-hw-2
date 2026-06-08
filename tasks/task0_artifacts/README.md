# MLflow Artifacts from Task 0 Eval Run

## Run Details
- **Run ID**: df34ee5d2b6e4183ae90a4783e6adce9
- **Config**: v4
- **Dataset Size**: 25 examples
- **Accuracy Overall**: 96.0%
- **Total Cost**: $0.0104
- **Duration**: 95.8 seconds

## Contents

### 1. **predictions/predictions.jsonl**
The main evaluation data file containing all 25 predictions. Each line is a JSON object with:
- `id`: Unique example ID
- `category`: Input category (travel, off_topic, etc.)
- `expected`: Expected behavior (answer or refuse)
- `prompt`: User's input message
- `response_text`: Assistant's response
- `judge_verdict`: Judge's classification (one of: answered_correctly, refused_correctly, leaked, over_refused)
- `judge_raw`: Raw judge LLM output with reasoning
- Full token counts, latency, and cost metrics for each exchange

### 2. **confusion.json**
Cross-tabulation of (category, judge_verdict) counts showing the distribution of verdicts across input categories.

### 3. **config.json**
Complete deployment configuration including:
- Model name and temperature
- System prompt (inline)
- Guardrail configuration
- All settings used for this eval run

### 4. **prompts/** folder
Individual prompt files for easy inspection:
- `main_system_prompt.txt`: The travel assistant's system prompt
- `input_classifier_prompt.txt`: Input classification guardrail (if used)
- `output_validator_prompt.txt`: Output validation guardrail (if used)

## Spot-checking Verdicts

To verify the judge is working correctly, check a few examples in `predictions.jsonl`:
- Travel questions should mostly be `answered_correctly`
- Non-travel questions should be `refused_correctly`
- Responses that partially answer off-topic questions should be `leaked`
- Legitimate travel questions that are refused should be `over_refused`

## Judge Prompt Used

The judge prompt in `prompts/judge.txt` at evaluation time included detailed handling of:
- Partial leaks (e.g., "I shouldn't help, but...")
- Polite-but-leaking responses
- Travel-adjacent topics (weather, currency, customs)
- Jailbreak attempts (role-play, ignore-previous-instructions)

Results show the judge is correctly classifying exchanges with a 96% accuracy on this config.
