# Task 02

## Objective
Find the person (from the transport list) whose location is closest to any power plant. Return their name, surname, access level, and the code of the closest power plant.

## Approach
1. Load people and power plant locations.
2. Use web search to get coordinates for power plants.
3. For each person: get location via tool, compute distances to power plants via tool.
4. Find the minimum-distance person–power-plant pair.
5. Fetch that person's access level via tool and return the answer.

## LLM usage
**Agentic loop** with tools: get_location, find_shortest_distance, get_access_level. Web search enabled for geocoding. LLM orchestrates tool calls and iterates over people. Structured output for the final answer.

## Notes
<!-- Any additional observations, edge cases, or learnings -->

# Featured models cost

## openai/gpt-5.4-nano; structured_output; tools (finding min in list vs list); web_search

| Model                          | Total Cost   | Input Cost   | Output Cost   | Input Tokens | Output Tokens | Requests |
|--------------------------------|--------------|--------------|---------------|--------------|---------------|----------|
| openai/gpt-5.4-nano            | $0.024308    | $0.020214    | $0.004094     | 101070       | 3275          | 12       |