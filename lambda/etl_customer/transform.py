"""Pure transformation logic — unit-testable without AWS."""


def clean_email(email: str) -> str:
    return email.strip().lower()


def row_to_item(row: dict, source_key: str) -> dict:
    return {
        "customer_id": row["customer_id"],
        "name": row["name"].strip(),
        "email": clean_email(row["email"]),
        "city": row["city"].strip(),
        "source_key": source_key,
    }
