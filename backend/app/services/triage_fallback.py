from app.schemas.triage import (
    TicketTriageResult,
    TriageCategory,
    TriagePriority,
)


def fallback_triage(
    subject: str,
    description: str,
) -> TicketTriageResult:

    text = f"{subject} {description}".lower()

    # -------------------------
    # Category detection
    # -------------------------

    if any(
        word in text
        for word in [
            "payment",
            "paid",
            "payment failed",
            "charged",
            "charge",
            "refund",
            "money",
            "transaction",
        ]
    ):
        category = TriageCategory.PAYMENT

    elif any(
        word in text
        for word in [
            "delivery",
            "delivered",
            "courier",
            "shipping",
            "late delivery",
            "not received",
        ]
    ):
        category = TriageCategory.DELIVERY

    elif any(
        word in text
        for word in [
            "order",
            "cancel order",
            "cancel my order",
            "wrong item",
            "missing item",
        ]
    ):
        category = TriageCategory.ORDER

    elif any(
        word in text
        for word in [
            "login",
            "log in",
            "account",
            "password",
            "sign in",
            "profile",
        ]
    ):
        category = TriageCategory.ACCOUNT

    elif any(
        word in text
        for word in [
            "error",
            "bug",
            "crash",
            "not working",
            "website",
            "app",
            "technical",
        ]
    ):
        category = TriageCategory.TECHNICAL

    else:
        category = TriageCategory.OTHER
    
    if category == TriageCategory.PAYMENT:
        summary = "Customer is reporting a payment-related issue."

    elif category == TriageCategory.DELIVERY:
        summary = "Customer is reporting a delivery-related issue."

    elif category == TriageCategory.ORDER:
        summary = "Customer is reporting an issue with an order."

    elif category == TriageCategory.ACCOUNT:
        summary = "Customer is reporting an account-related issue."

    elif category == TriageCategory.TECHNICAL:
        summary = "Customer is reporting a technical issue."

    else:
        summary = "Customer is reporting an issue that requires support attention."

    # -------------------------
    # Priority detection
    # -------------------------

    if any(
        phrase in text
        for phrase in [
            "charged twice",
            "money deducted",
            "account hacked",
            "cannot access",
            "can't access",
            "urgent",
            "immediately",
            "critical",
        ]
    ):
        priority = TriagePriority.HIGH

    elif any(
        word in text
        for word in [
            "failed",
            "late",
            "problem",
            "issue",
            "error",
            "wrong",
        ]
    ):
        priority = TriagePriority.MEDIUM

    else:
        priority = TriagePriority.LOW

    # -------------------------
    # Summary
    # -------------------------

    summary = f"Customer issue regarding {category.value.lower()}."

    return TicketTriageResult(
        priority=priority,
        category=category,
        summary=summary,
    )