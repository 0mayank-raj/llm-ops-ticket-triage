import json
import argparse
import time

from app.triage import process_ticket

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


def load_evaluation_dataset(dataset_path):

    with open(dataset_path, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    return dataset


def evaluate_model(dataset_path):

    dataset = load_evaluation_dataset(dataset_path)

    total_tickets = len(dataset)
    request_delay = 20

    print(f"Request delay: {request_delay} seconds")

    actual_categories = []
    predicted_categories = []

    actual_priorities = []
    predicted_priorities = []
    priority_misclassified = []

    print(f"Dataset: {dataset_path}")
    print(f"Total evaluation tickets: {total_tickets}")

    for index, item in enumerate(dataset, start=1):

        print(f"\nEvaluating Ticket {index}...")

        prediction = process_ticket(item["ticket"])

        if index < total_tickets:
            print(f"Waiting {request_delay} seconds before next request...")
            time.sleep(request_delay)

        expected_category = item["expected_category"]
        expected_priority = item["expected_priority"]

        actual_categories.append(expected_category)
        predicted_categories.append(prediction.category)

        actual_priorities.append(expected_priority)
        predicted_priorities.append(prediction.priority)

        if expected_priority != prediction.priority:
            priority_misclassified.append({
                "ticket_number": index,
                "ticket": item["ticket"],
                "expected": expected_priority,
                "predicted": prediction.priority
            })

        print(f"Expected Category: {expected_category}")
        print(f"Predicted Category: {prediction.category}")

        print(f"Expected Priority: {expected_priority}")
        print(f"Predicted Priority: {prediction.priority}")

    category_accuracy = accuracy_score(
        actual_categories,
        predicted_categories
    )

    priority_accuracy = accuracy_score(
        actual_priorities,
        predicted_priorities
    )

    category_precision = precision_score(
        actual_categories,
        predicted_categories,
        average="weighted",
        zero_division=0
    )

    category_recall = recall_score(
        actual_categories,
        predicted_categories,
        average="weighted",
        zero_division=0
    )

    category_f1 = f1_score(
        actual_categories,
        predicted_categories,
        average="weighted",
        zero_division=0
    )

    priority_precision = precision_score(
        actual_priorities,
        predicted_priorities,
        average="weighted",
        zero_division=0
    )

    priority_recall = recall_score(
        actual_priorities,
        predicted_priorities,
        average="weighted",
        zero_division=0
    )

    priority_f1 = f1_score(
        actual_priorities,
        predicted_priorities,
        average="weighted",
        zero_division=0
    )

    category_labels = sorted(set(actual_categories + predicted_categories))
    priority_labels = sorted(set(actual_priorities + predicted_priorities))

    category_cm = confusion_matrix(
        actual_categories,
        predicted_categories,
        labels=category_labels
    )

    priority_cm = confusion_matrix(
        actual_priorities,
        predicted_priorities,
        labels=priority_labels
    )

    print("\n========== EVALUATION RESULTS ==========")

    print("\nCATEGORY CLASSIFICATION")
    print(f"Accuracy:  {category_accuracy * 100:.2f}%")
    print(f"Precision: {category_precision * 100:.2f}%")
    print(f"Recall:    {category_recall * 100:.2f}%")
    print(f"F1-score:  {category_f1 * 100:.2f}%")

    print("\nPRIORITY CLASSIFICATION")
    print(f"Accuracy:  {priority_accuracy * 100:.2f}%")
    print(f"Precision: {priority_precision * 100:.2f}%")
    print(f"Recall:    {priority_recall * 100:.2f}%")
    print(f"F1-score:  {priority_f1 * 100:.2f}%")

    print("\nCATEGORY CONFUSION MATRIX")
    print("Labels:", category_labels)
    print(category_cm)

    print("\nCATEGORY CLASSIFICATION REPORT")

    print(classification_report(
        actual_categories,
        predicted_categories,
        labels=category_labels,
        zero_division=0
    ))

    print("\nPRIORITY CONFUSION MATRIX")
    print("Labels:", priority_labels)
    print(priority_cm)

    print("\nPRIORITY CLASSIFICATION REPORT")

    print(classification_report(
        actual_priorities,
        predicted_priorities,
        labels=priority_labels,
        zero_division=0
    ))

    print("\n========== PRIORITY MISCLASSIFICATIONS ==========")

    if priority_misclassified:
        for item in priority_misclassified:
            print(f"\nTicket Number: {item['ticket_number']}")
            print(f"Ticket: {item['ticket']}")
            print(f"Expected Priority: {item['expected']}")
            print(f"Predicted Priority: {item['predicted']}")
            print("-" * 60)
    else:
        print("No priority misclassifications found.")

    print("\n========================================")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Evaluate the LLM ticket triage model."
    )

    parser.add_argument(
        "--dataset",
        default="evals/evaluation_dataset.json",
        help="Path to the evaluation dataset"
    )

    args = parser.parse_args()

    evaluate_model(args.dataset)