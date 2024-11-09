import asyncio
import json
import re
from datetime import datetime
from openai import AsyncOpenAI
from question_config import API_KEY, MCQ_PROMPT



MAX_QUESTIONS_PER_PROMPT = 5
TOPIC = "Debugging python code"
TOTAL = 25
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.8
INCLUDE_QUESTION_HISTORY = True
# TOP_P = 0.9
SAVE_FILE = f"Problem_bank_{TOPIC.replace(' ', '-')}_{TOTAL}_{MODEL}_T={TEMPERATURE}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

class QuestionGenerator:

    def __init__(self, api_key):
        self.client = AsyncOpenAI(
            api_key=api_key,
        )
        self.save_file = SAVE_FILE
        self.problem_bank = []

        with open(self.save_file, "w", encoding="utf8") as f:
            print(f"Created file {self.save_file}")
            f.write("[]") # init empty list

    def generate_prompt(self, topic: str, question_type="MCQ", n=10) -> str:
        prompt = ""
        if question_type == "MCQ":
            prompt = MCQ_PROMPT.format(topic=topic, n=n)
        if INCLUDE_QUESTION_HISTORY:
            question_history = "- \n".join([i["question"] for i in self.problem_bank])
            question_history = "\n\n**Question history** (do not repeat the same questions): \n" + question_history
            prompt += question_history

        return prompt

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

    async def generate(self, topic: str, question_type="MCQ", total=10) -> None:
        while total > 0:
            print(f"{total} questions remaining...")
            n = min(total, MAX_QUESTIONS_PER_PROMPT)
            prompt = self.generate_prompt(topic, question_type, n)
            total -= MAX_QUESTIONS_PER_PROMPT
            response = await self.generate_response(prompt)
            self.parse_response(response)

    def parse_response(self, response: str) -> None:
        full_question_pattern = "(question.*?answer.+?[ABCD])"
        question_pattern = "question.*?:(.+)"
        options_pattern = "([ABCD])\)(.+?)\n"
        answer_pattern = "correct answer.*?:.*?([ABCD])"
        questions = re.findall(full_question_pattern, response, flags=re.DOTALL | re.IGNORECASE)
        parsed_questions = []
        for question in questions:
            try:
                q = re.search(question_pattern, question, flags=re.IGNORECASE).group(1).strip()
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
    question_generator = QuestionGenerator(API_KEY)
    await question_generator.generate(TOPIC, total=TOTAL)


if __name__ == '__main__':
    asyncio.run(run())