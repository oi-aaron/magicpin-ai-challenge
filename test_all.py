import json
import os

from bot import compose


BASE = "expanded"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_customer_file(customer_id):
    folder = os.path.join(BASE, "customers")

    for filename in os.listdir(folder):
        if customer_id.lower() in filename.lower():
            return os.path.join(folder, filename)

    return None


data = load_json(
    os.path.join(BASE, "test_pairs.json")
)

tests = data["pairs"]


for test in tests:
    test_id = test["test_id"]
    merchant_id = test["merchant_id"]
    trigger_id = test["trigger_id"]
    customer_id = test.get("customer_id")

    merchant_path = os.path.join(
        BASE,
        "merchants",
        f"{merchant_id}.json"
    )

    trigger_path = os.path.join(
        BASE,
        "triggers",
        f"{trigger_id}.json"
    )

    if not os.path.exists(merchant_path):
        print(f"{test_id} | ERROR | merchant file not found")
        continue

    if not os.path.exists(trigger_path):
        print(f"{test_id} | ERROR | trigger file not found")
        continue

    merchant = load_json(merchant_path)
    trigger = load_json(trigger_path)

    customer = None

    if customer_id:
        customer_path = find_customer_file(customer_id)

        if customer_path:
            customer = load_json(customer_path)
        else:
            print(
                f"{test_id} | WARNING | "
                f"customer file not found: {customer_id}"
            )

    try:
        result = compose(
            {},
            merchant,
            trigger,
            customer
        )

        print(
            f"{test_id} | "
            f"{trigger['kind']} | "
            f"{result['send_as']} | "
            f"{result['body']}"
        )

    except Exception as e:
        print(
            f"{test_id} | ERROR | "
            f"{type(e).__name__}: {e}"
        )