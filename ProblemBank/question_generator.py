import asyncio
import json
import re
from datetime import datetime
from openai import AsyncOpenAI
from question_config import API_KEY, MCQ_PROMPT, MUTATION_PROMPT

MAX_QUESTIONS_PER_PROMPT = 5
TOTAL = 25
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.8
INCLUDE_QUESTION_HISTORY = True
# TOP_P = 0.9

class QuestionGenerator:

    def __init__(self, api_key=None, topic="", topic_context="", question_type="MCQ", total=5, mutate=False, difficulty=5):

        self.client = AsyncOpenAI(
            api_key=api_key,
        )
        self.topic = topic
        self.topic_context = topic_context
        self.total = total
        self.question_type = question_type
        self.mutate = mutate
        self.difficulty = difficulty
        self.save_file = f"Problem_bank_{topic.replace(' ', '-')}_{total}_{MODEL}_T={TEMPERATURE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        self.problem_bank = []

        with open(self.save_file, "w", encoding="utf8") as f:
            print(f"Created file {self.save_file}")
            f.write("[]") # init empty list

    async def generate_prompt(self, n=10) -> str:
        topic = self.topic
        prompt = ""
        if self.question_type == "MCQ":
            topic_context = ". " + self.topic_context if self.topic_context else "" # adds topic context or nothing
            prompt = MCQ_PROMPT.format(topic=topic, n=n, topic_context=topic_context)
        if self.mutate:
            prompt = await self.mutate_prompt(prompt)
            print(prompt)
        if INCLUDE_QUESTION_HISTORY:
            question_history = "- \n".join([i["question"] for i in self.problem_bank])
            question_history = "\n\n**Question history** (do not repeat the same questions): \n" + question_history
            prompt += question_history

        return prompt

    async def mutate_prompt(self, prompt):
        print(f"Mutating prompt with difficulty level {self.difficulty}")
        mutate_prompt = MUTATION_PROMPT.format(difficulty_level=self.difficulty, original_prompt=prompt)
        response = await self.generate_response(mutate_prompt)
        return response

    async def generate_response(self, prompt: str) -> str:
        try:
            chat_completion = await self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    temperature=TEMPERATURE,
                    # top_p=TOP_P
                )
            response = chat_completion.choices[0].message.content
        except Exception as e:
            print("Error generating response:", e)
            response = None

        return response

    async def generate(self) -> None:
        total = self.total
        while total > 0:
            print(f"{total} questions remaining...")
            n = min(total, MAX_QUESTIONS_PER_PROMPT)
            prompt = await self.generate_prompt(n)
            total -= MAX_QUESTIONS_PER_PROMPT
            response = await self.generate_response(prompt)
            self.parse_response(response)

    def parse_response(self, response: str) -> None:
        full_question_pattern = "(question.*?answer.+?[ABCD])"
        question_pattern = "question.*?:(.+)\n.*options"
        options_pattern = "([ABCD])\)(.+?)\n"
        answer_pattern = "correct answer.*?:.*?([ABCD])"
        questions = re.findall(full_question_pattern, response, flags=re.DOTALL | re.IGNORECASE)
        parsed_questions = []
        for question in questions:
            try:
                q = re.search(question_pattern, question, flags=re.DOTALL | re.IGNORECASE).group(1).strip()
                options = re.findall(options_pattern, question, flags=re.DOTALL | re.IGNORECASE)
                options = [(a, b.strip()) for a, b in options]
                answer = re.search(answer_pattern, question, flags=re.IGNORECASE).group(1).strip()
                parsed_questions.append({
                    "question": q,
                    "options": options,
                    "answer": answer
                })
            except Exception as e:
                print("Failed to parse response:", e, question)

        print(f"Parsed {len(parsed_questions)} questions")
        # print(response)
        self.problem_bank.extend(parsed_questions)
        self.append_to_file(parsed_questions)


    def append_to_file(self, new_data: [dict]) -> None:
        with open(self.save_file, 'r', encoding="utf8") as f:
            data = json.load(f)

        for i in range(len(new_data)):
            new_data[i]["index"] = len(data) + i + 1

        data.extend(new_data)

        with open(self.save_file, 'w') as file:
            json.dump(data, file, indent=4)


async def run():
    question_generator = QuestionGenerator(API_KEY, TOPIC, topic_context=TOPIC_CONTEXT, total=TOTAL)
    await question_generator.generate()


if __name__ == '__main__':
    TOPIC = "Debugging in Python"
    TOPIC_CONTEXT = "Give the student a few lines of sample buggy code in python and ask them to locate where the bug is"

    asyncio.run(run())