from groq import Groq

from app.config import settings
from app.schemas.triage import TicketTriageResult
from app.services.triage_fallback import fallback_triage


client = Groq(
    api_key=settings.groq_api_key,
)


SYSTEM_PROMPT = """
You are an AI customer support ticket triage assistant.

Your job is to carefully read BOTH the ticket subject and description.

You must:

1. Identify the customer's actual problem.
2. Classify the problem into exactly ONE category.
3. Assign an appropriate priority.
4. Write a concise, factual summary of the customer's actual issue.

Allowed categories:

PAYMENT
DELIVERY
ORDER
ACCOUNT
TECHNICAL
OTHER

Allowed priorities:

HIGH
MEDIUM
LOW

Priority guidelines:

HIGH:
- Security or account compromise
- Duplicate or unauthorized charges
- Money deducted with a serious transaction problem
- Critical service failure
- Issue completely preventing an essential service

MEDIUM:
- Payment failure
- Delivery delay
- Incorrect order
- Login problems
- Technical problems
- Other issues requiring support attention

LOW:
- General questions
- Information requests
- Minor non-urgent issues

IMPORTANT RULES FOR THE SUMMARY:

- The summary MUST describe the actual customer problem.
- Do NOT say "No issue described" if the subject or description contains a problem.
- Use both subject and description.
- Do not invent facts that are not present.
- Do not mention that you are an AI.
- Keep the summary between 1 and 2 sentences.
- Preserve important details such as payment failures, duplicate charges, missing orders, login problems, etc.

Example:

Subject:
"Payment processing not happening"

Description:
"I am trying to make a payment but the payment is not being processed."

Correct output:

{
    "priority": "MEDIUM",
    "category": "PAYMENT",
    "summary": "Customer is unable to complete a payment because the payment is not being processed."
}

Return ONLY valid JSON:

{
    "priority": "HIGH | MEDIUM | LOW",
    "category": "PAYMENT | DELIVERY | ORDER | ACCOUNT | TECHNICAL | OTHER",
    "summary": "concise factual summary"
}
"""


def triage_ticket(
    subject: str,
    description: str,
) -> TicketTriageResult:

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"Subject: {subject}\n"
                        f"Description: {description}"
                    ),
                },
            ],
            temperature=0,
            response_format={
                "type": "json_object"
            },
            timeout=10,
        )

        content = response.choices[0].message.content

        result = TicketTriageResult.model_validate_json(
            content
        )

        return result

    except Exception as exc:
        print(f"AI triage failed: {exc}")

        return fallback_triage(
            subject=subject,
            description=description,
        )