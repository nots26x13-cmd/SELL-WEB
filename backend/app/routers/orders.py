import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException

from ..firebase_client import get_db
from ..fulfillment import request_fulfillment
from ..schemas import OrderCreateRequest, OrderStatusUpdateRequest
from ..security import require_admin
from .wallet import _credit_wallet, _get_balance

router = APIRouter(tags=["orders"])


@router.post("/api/orders/{user_id}")
def create_order(user_id: str, req: OrderCreateRequest):
    db = get_db()
    product_doc = db.collection("products").document(req.product_id).get()
    if not product_doc.exists:
        raise HTTPException(status_code=404, detail="Product not found")

    product = product_doc.to_dict()
    package = next((p for p in product.get("packages", []) if p["id"] == req.package_id), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    if not package.get("in_stock", True):
        raise HTTPException(status_code=409, detail="This package is out of stock")

    price = float(package["price_bdt"])
    balance = _get_balance(user_id)
    if balance < price:
        raise HTTPException(status_code=402, detail="Insufficient wallet balance")

    # Deduct up front, refund on failure - keeps the ledger simple and honest.
    _credit_wallet(user_id, -price)

    order_id = str(uuid.uuid4())
    order = {
        "id": order_id,
        "user_id": user_id,
        "product_id": req.product_id,
        "product_name": product["name"],
        "package_id": req.package_id,
        "package_label": package["label"],
        "player_uid": req.player_uid,
        "price_bdt": price,
        "status": "created",
        "created_at": dt.datetime.utcnow().isoformat(),
    }
    db.collection("orders").document(order_id).set(order)

    try:
        request_fulfillment(order_id)
    except Exception:
        # Refund automatically if we couldn't even queue it for fulfillment.
        _credit_wallet(user_id, price)
        db.collection("orders").document(order_id).update({"status": "failed_to_queue"})
        raise HTTPException(status_code=500, detail="Could not queue order, wallet refunded")

    return order


@router.get("/api/orders/user/{user_id}")
def list_user_orders(user_id: str):
    db = get_db()
    docs = db.collection("orders").where("user_id", "==", user_id).stream()
    return [d.to_dict() for d in docs]


@router.get("/api/admin/orders", dependencies=[Depends(require_admin)])
def list_all_orders(status_filter: str | None = None):
    db = get_db()
    query = db.collection("orders")
    if status_filter:
        query = query.where("status", "==", status_filter)
    return [d.to_dict() for d in query.stream()]


@router.put("/api/admin/orders/{order_id}/status", dependencies=[Depends(require_admin)])
def update_order_status(order_id: str, req: OrderStatusUpdateRequest):
    db = get_db()
    ref = db.collection("orders").document(order_id)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Order not found")

    updates = {"status": req.status}
    if req.admin_note:
        updates["admin_note"] = req.admin_note

    if req.status == "rejected" and doc.to_dict().get("status") != "rejected":
        # Refund the customer if an admin rejects/cancels the order.
        order = doc.to_dict()
        _credit_wallet(order["user_id"], order["price_bdt"])

    ref.update(updates)
    return {"ok": True}
