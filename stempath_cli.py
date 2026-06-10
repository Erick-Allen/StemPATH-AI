from src.core import StemPathCore


def main():
    core = StemPathCore()
    core.ensure_ready()

    print("\nStemPATH-AI Career Research Assistant")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        user_input = input("Question: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break

        if not user_input:
            continue

        print("\nSearching career documents and graph context...\n")
        answer, results = core.query(user_input)

        if not answer:
            print("No relevant career data found.\n")
            continue

        print(f"Top {len(results)} career matches:")
        for result in results:
            print(f"  [{result['score']:.4f}] {result['title']}")

        print(f"\n Answer:\n{answer}\n")

if __name__ == "__main__":
    main()