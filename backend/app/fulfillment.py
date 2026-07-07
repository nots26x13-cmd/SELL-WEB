"""
Fulfillment hook.

What this deliberately does NOT do: send automated "likes" to Free Fire
profiles. Doing that means scripting a large number of accounts (or an
undocumented Garena endpoint) to fake a social metric on someone's behalf -
that's account automation / platform manipulation against Garena's terms,
not something this project implements.

What this DOES do: give you one clean place to plug in whatever fulfillment
process you actually run. When an order is paid, `request_fulfillment()`
marks it for action and notifies the admin panel. From there you can:
  - fulfill it by hand and click "Mark fulfilled" in /admin, or
  - call your own existing fulfillment service from here, if you have one
    that you already operate in a way that's compliant with Garena's terms
    (e.g. an official reseller / top-up API you have a real agreement for).

This keeps order-taking, payment, and wallet logic (which are the parts of
the system that are just normal e-commerce plumbing) fully separate from
however delivery actually happens.
"""
from .firebase_client import get_db


def request_fulfillment(order_id: str) -> None:
    db = get_db()
    order_ref = db.collection("orders").document(order_id)
    order_ref.update({
        "status": "pending_fulfillment",
        "fulfillment_note": "Awaiting manual admin fulfillment.",
    })
    # Optional: push a notification to your admin Telegram bot / Slack here
    # so a human sees it immediately instead of polling the admin panel.
