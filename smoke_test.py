
from rag_graph import ask_question

questions = [
    "Within how many days must expense claims be submitted?",
    "What documents are required for reimbursement?",
    "Who approves an expense claim?",
    "What is the company's Mars travel allowance?",
]

for question in questions:
    print("\n" + "=" * 60)
    print("QUESTION:", question)

    result = ask_question(question)

    print("\nANSWER:")
    print(result["answer"])

    print("\nSOURCES:")
    for source in result.get("sources", []):
        print(
            f"[{source['citation']}] {source['source']}"
            f" | page={source['page']}"
        )
