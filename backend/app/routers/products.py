import uuid

from fastapi import APIRouter, Depends, HTTPException

from ..firebase_client import get_db
from ..schemas import Product
from ..security import require_admin

router = APIRouter(tags=["products"])


@router.get("/api/products")
def list_products(active_only: bool = True):
    db = get_db()
    query = db.collection("products")
    docs = query.get()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        if active_only and not data.get("active", True):
            continue
        items.append(data)
    return items


@router.get("/api/products/{product_id}")
def get_product(product_id: str):
    db = get_db()
    doc = db.collection("products").document(product_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Product not found")
    data = doc.to_dict()
    data["id"] = doc.id
    return data


@router.post("/api/admin/products", dependencies=[Depends(require_admin)])
def create_product(product: Product):
    db = get_db()
    product_id = product.id or str(uuid.uuid4())
    payload = product.model_dump()
    payload["id"] = product_id
    db.collection("products").document(product_id).set(payload)
    return payload


@router.put("/api/admin/products/{product_id}", dependencies=[Depends(require_admin)])
def update_product(product_id: str, product: Product):
    db = get_db()
    payload = product.model_dump()
    payload["id"] = product_id
    db.collection("products").document(product_id).set(payload, merge=True)
    return payload


@router.delete("/api/admin/products/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: str):
    db = get_db()
    db.collection("products").document(product_id).delete()
    return {"ok": True}
