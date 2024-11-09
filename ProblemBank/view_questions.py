import json

FILE = "Problem_bank_Debugging-python-code_25_gpt-4o-mini_T=0.8_20241109_160937.json"

if __name__ == '__main__':
    with open(FILE) as f:
        data = json.load(f)

    for i in data:
        print(f"*** Question {i['index']} ***")
        print(f"Question: {i['question']}")
        for a, b in i["options"]:
            print(f"\t{a}): {b}")
        print(f"Answer: {i['answer']})")
        print("-"*50)