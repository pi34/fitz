
with open("api_key", "r") as f:
    API_KEY = f.read()

MCQ_PROMPT = """**Prompt:**

Create a list of {n} advanced and unique multiple-choice quiz questions to help a student study the topic {topic}{topic_context}. Each question should include 4 answer options (A, B, C, D) and clearly indicate the correct answer. You will be asked to create quiz problems multiple times, so please create more creative, specific, and challenging problems to avoid recreating the same questions!

Follow this exact format for each question to ensure it's easy to parse:

**Format:**

- **Question**: [Question text]
- **Options**:
  - A) [Option A]
  - B) [Option B]
  - C) [Option C]
  - D) [Option D]
- **Correct Answer**: [Correct option letter, e.g., "A"]

"""


MUTATION_PROMPT = """Rewrite the following prompt to make it more creative and diverse while maintaining its original purpose of creating quiz problems for students. Additionally, incorporate the given difficulty level parameter ranging from 1 to 5, where:

- **1**: Simple questions that test basic understanding.
- **3**: Moderately difficult questions that introduce harder problems and test knowledge of common Python libraries.
- **5**: Extremely difficult questions that are challenging (near impossible) to answer correctly and test knowledge of less common or specialized Python libraries.

Ensure that the mutated prompt preserves the proper formatting and structure, encourages the creation of unique, varied questions, and creative scenarios, and adjusts the complexity and library usage based on the difficulty level. Introduce variations in language and add elements that enhance creativity without deviating from the goal.

**Difficulty Level**
Difficult level {difficulty_level}. Make sure to directly incorporate the difficult level into the original prompt. 

**Original Prompt:**

{original_prompt}
"""