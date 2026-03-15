# Task 01

## Objective
<!-- Describe what this task asks you to do -->

## Approach
<!-- Outline your solution strategy -->

## Solution
<!-- Notes on the final solution, what worked, what didn't -->

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