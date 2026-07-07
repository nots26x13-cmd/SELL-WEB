# Firestore schema

All writes to `users`, `orders`, and `used_binance_txids` happen only through
the backend (via the Admin SDK), never directly from the frontend - that's
what makes wallet balances trustworthy. The rules file in this folder locks
that down.

## `products/{productId}`
```
{
  "id": "prod_abc",
  "name": "FREE FIRE LIKES",
  "subtitle": "UID TOPUP",
  "image_url": "",
  "category": "likes",
  "requires_uid": true,
  "active": true,
  "packages": [
    { "id": "pkg_1", "label": "100 likes / day", "price_bdt": 5, "duration_days": 1, "quantity_per_day": 100, "in_stock": true },
    { "id": "pkg_2", "label": "220 likes / 30day", "price_bdt": 300, "duration_days": 30, "quantity_per_day": 220, "in_stock": false }
  ]
}
```

## `users/{userId}`
```
{ "wallet_balance": 12.5, "telegram_id": "123456", "created_at": "..." }
```
`userId` is whatever `getCurrentUserId()` in the frontend resolves to - by
default the Telegram user id prefixed with `tg-`, so it lines up with
Telegram Mini App auth automatically.

## `orders/{orderId}`
```
{
  "id": "order_xyz",
  "user_id": "tg-123456",
  "product_id": "prod_abc",
  "product_name": "FREE FIRE LIKES",
  "package_id": "pkg_1",
  "package_label": "100 likes / day",
  "player_uid": "746856188",
  "price_bdt": 5,
  "status": "pending_fulfillment",
  "created_at": "2026-07-07T12:00:00",
  "fulfillment_note": "Awaiting manual admin fulfillment.",
  "admin_note": null
}
```
Status flow: `created` → `pending_fulfillment` → `fulfilled` | `rejected`.
Rejecting an order automatically refunds the wallet (see `orders.py`).

## `used_binance_txids/{txId}`
```
{ "user_id": "tg-123456", "amount": 5.0 }
```
Prevents the same Binance Pay Order ID from being claimed twice - this
replaces the `used_txids1.json` file from the original CLI script so it
works safely with multiple server instances / restarts.

## `settings/global`
```
{
  "binance_pay_id": "881496930",
  "min_deposit_usdt": 0.01,
  "payment_methods": { "binance": true, "bkash": false, "nagad": false },
  "nickname_api_base_url": "https://ff-info-api-weld.vercel.app",
  "nickname_api_enabled": true
}
```

## `admins/{email}`
```
{ "email": "admin@example.com", "password_hash": "$2b$..." }
```
Password is bcrypt-hashed by the backend - never stored or transmitted in
plaintext. Change the bootstrap password from the admin panel on first login.
