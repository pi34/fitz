
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

Make sure each question is challenging yet fair, and that the options include plausible distractors. If the topic requires any specific terminology, definitions, or examples, use them as appropriate to deepen understanding.
"""
