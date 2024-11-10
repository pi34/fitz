import asyncio

from ProblemBank.question_config import API_KEY
from ProblemBank.question_generator import QuestionGenerator

demos = (
    # ("Abstract Algebra", "", 5),
    ("Git tools", "", 25, 3),
    # ("Python debugging", "Give the student a few lines of sample buggy code in python and ask them to locate which line number the bug is. Make sure to generate the sample code with line numbers on the left, and make sure that the answer choices correspond to the correct line numbers", 50),
    ("Python debugging",
     "Give the student lines of sample buggy code in python and ask them to locate which line number the bug is. Make sure to generate the sample code with line numbers on the left, and make sure that the answer choices correspond to the correct line numbers",
     25)
)


async def run():

    for demo in demos:
        topic = demo[0]
        context = demo[1]
        total = demo[2]
        # mutate = False
        # difficulty = -1
        # if demo[3]:
        #     mutate = True
        #     difficulty = demo[3]
        for difficulty in range(1, 6):
            print(topic)
            print(context)
            print(total)
            print(difficulty)
            mutate = True
            print("Generating")
            question_generator = QuestionGenerator(api_key=API_KEY, topic=topic, topic_context=context, total=total, mutate=True, difficulty=difficulty)
            await question_generator.generate()

            for i in question_generator.problem_bank:
                print(f"*** Question {i['index']} ***")
                print(f"Question: {i['question']}")
                for a, b in i["options"]:
                    print(f"\t{a}): {b}")
                print(f"Answer: {i['answer']})")
                print("-" * 50)




if __name__ == '__main__':
    asyncio.run(run())