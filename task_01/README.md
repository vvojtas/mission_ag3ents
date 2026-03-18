# Task 01

## Objective
Find people who are male, born in Grudziądz, aged 20–40, and work in transport. Return their details with industry tags.

## Approach
1. Filter CSV by gender, birth place, and age.
2. Ask the LLM to classify each person's job into industries (IT, transport, edukacja, etc.).
3. Keep only those tagged "transport" and submit.

## LLM usage
Single prompt with **structured output** (Pydantic schema). Batch classification of all people in one call. Optional reasoning field for interpretability (not required for correctness).

## Notes
| Model | Notes |
|---|---|
| `mistralai/mistral-nemo` | did not get the purpose of 'reasoning' output field. It just copied job description. The classification were iff-y. 'Inne' was not used often. But it correctly classified all 'transport', so passed the task |
| `google/gemini-2.5-flash-lite` | made better classification. Made correct use of 'reasonings' output field. But disabling the field and model reasoning returned similar results, showing those techniques were not required for this task and model. |


# Featured models cost

## google/gemini-2.5-flash-lite without reasoning; reasoning field

| Model                          | Total Cost   | Input Cost   | Output Cost   | Input Tokens | Output Tokens | Requests |
|--------------------------------|--------------|--------------|---------------|--------------|---------------|----------|
| google/gemini-2.5-flash-lite   | $0.000649    | $0.000286    | $0.000362     | 2865         | 906           | 1        |