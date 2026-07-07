"""
Wallet + deposits.

The Binance Pay verification logic here is adapted directly from the CLI
tool you already had (app.py): look up the order/tx id in Binance Pay's
history, confirm the currency and amount, then credit the wallet. The only
real changes are: (1) it runs as a web endpoint instead of an interactive
CLI, (2) "already used" tx ids are tracked in Firestore instead of a local
json file so it works across multiple server instances, (3) API keys are
read from environment variables instead of being hardcoded.

bKash and Nagad both require signing up for their merchant/PGW APIs and
getting real app keys - there's no way around that step since it's their
credential, not something that can be generated. The endpoints below are
wired up and ready; drop your credentials into .env and implement the two
TODOs once you have them.
"""
from fastapi import APIRouter, HTTPException, status
from binance.spot import Spot as BinanceClient
from binance.error import ClientError

from ..config import settings
from ..firebase_client import get_db
from ..schemas import BinanceDepositVerifyRequest, DepositIntentRequest

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


def _wallet_ref(user_id: str):
    return get_db().collection("users").document(user_id)


def _get_balance(user_id: str) -> float:
    doc = _wallet_ref(user_id).get()
    if not doc.exists:
        return 0.0
    return float(doc.to_dict().get("wallet_balance", 0.0))


def _credit_wallet(user_id: str, amount: float) -> float:
    ref = _wallet_ref(user_id)
    new_balance = _get_balance(user_id) + amount
    ref.set({"wallet_balance": new_balance}, merge=True)
    return new_balance


def _is_txid_used(tx_id: str) -> bool:
    doc = get_db().collection("used_binance_txids").document(tx_id).get()
    return doc.exists


def _mark_txid_used(tx_id: str, user_id: str, amount: float):
    get_db().collection("used_binance_txids").document(tx_id).set({
        "user_id": user_id,
        "amount": amount,
    })


def _verify_with_binance(tx_id: str):
    """Returns (is_valid, actual_amount, sender_name). Mirrors app.py's
    verify_pay_txid_with_binance, using env-var credentials."""
    if not settings.binance_api_key or not settings.binance_api_secret:
        raise HTTPException(status_code=500, detail="Binance API credentials are not configured")

    client = BinanceClient(settings.binance_api_key, settings.binance_api_secret)
    try:
        pay_history = client.pay_history(limit=100)
    except ClientError as e:
        raise HTTPException(status_code=502, detail=f"Binance API error: {e.error_message}")

    if not (pay_history.get("success") and "data" in pay_history):
        return False, 0.0, ""

    for tx in pay_history["data"]:
        if tx.get("orderId") == tx_id:
            actual_amount = float(tx.get("amount"))
            currency = tx.get("currency")
            payer_info = tx.get("payerInfo", {})
            sender_name = payer_info.get("name", "Unknown Sender")
            if currency == "USDT":
                return True, actual_amount, sender_name
            return False, 0.0, ""
    return False, 0.0, ""


@router.get("/balance/{user_id}")
def get_balance(user_id: str):
    return {"user_id": user_id, "wallet_balance": _get_balance(user_id)}


@router.post("/deposit/intent/{user_id}")
def create_deposit_intent(user_id: str, req: DepositIntentRequest):
    from .settings_router import _get_settings_doc
    cfg = _get_settings_doc()
    if req.amount_usdt < cfg["min_deposit_usdt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum deposit is {cfg['min_deposit_usdt']} USDT",
        )
    return {
        "binance_pay_id": cfg["binance_pay_id"],
        "amount_usdt": req.amount_usdt,
        "instructions": [
            "Open Binance App -> Pay -> Send -> Pay ID",
            f"Enter Pay ID {cfg['binance_pay_id']} and send the exact amount",
            "Copy the Order ID (TxID) after the transfer completes",
            "Paste it below to verify and credit your wallet",
        ],
    }


@router.post("/deposit/binance/verify/{user_id}")
def verify_binance_deposit(user_id: str, req: BinanceDepositVerifyRequest):
    if _is_txid_used(req.tx_id):
        raise HTTPException(status_code=409, detail="This transaction ID has already been claimed")

    is_valid, actual_amount, sender_name = _verify_with_binance(req.tx_id)
    if not is_valid:
        raise HTTPException(status_code=404, detail="Transaction not found in Binance Pay records")

    _mark_txid_used(req.tx_id, user_id, actual_amount)
    new_balance = _credit_wallet(user_id, actual_amount)

    return {
        "ok": True,
        "received_amount_usdt": actual_amount,
        "sender_name": sender_name,
        "new_balance": new_balance,
        "exact_match": actual_amount == req.expected_amount_usdt,
    }


@router.post("/deposit/bkash/verify/{user_id}")
def verify_bkash_deposit(user_id: str, payment_id: str):
    # TODO: call bKash's Execute Payment / Query Payment API using
    # BKASH_APP_KEY / BKASH_APP_SECRET / BKASH_USERNAME / BKASH_PASSWORD
    # from Settings, then credit the wallet the same way as Binance above.
    raise HTTPException(status_code=501, detail="bKash merchant credentials not configured yet")


@router.post("/deposit/nagad/verify/{user_id}")
def verify_nagad_deposit(user_id: str, payment_ref_id: str):
    # TODO: call Nagad's Verify Payment API using NAGAD_MERCHANT_ID /
    # NAGAD_MERCHANT_PRIVATE_KEY from Settings, then credit the wallet.
    raise HTTPException(status_code=501, detail="Nagad merchant credentials not configured yet")
