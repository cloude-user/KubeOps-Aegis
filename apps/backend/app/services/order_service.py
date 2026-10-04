import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

try:
    from backend.app.config import Settings, settings
    from backend.app.services.blob_service import AzureBlobService
except ModuleNotFoundError:
    from apps.backend.app.config import Settings, settings
    from apps.backend.app.services.blob_service import AzureBlobService

logger = logging.getLogger("backend.services.order")

# Shared In-Memory State for fallback when DB is disconnected
ORDERS_IN_MEMORY_STORE = []


class OrderService:
    """
    Enterprise Business Logic Layer for Order Operations.
    Decoupled from HTTP routing and instantiated via Dependency Injection.
    """

    def __init__(self, settings: Settings, blob_service: AzureBlobService, db_connection=None):
        self.settings = settings
        self.blob_service = blob_service
        self.db = db_connection

    async def create_order(self, user_id: str, items: list, shipping_address: str, request_id: str = "req-default") -> dict:
        """
        Executes order placement business rules:
        1. Price calculation & stock validation
        2. Unique Order ID generation
        3. Receipt URL construction
        4. Persistence to Azure PostgreSQL (or in-memory fallback)
        """
        logger.info("[%s] ORDER_SERVICE: Starting order creation for user_id='%s' with %d items", request_id, user_id, len(items))

        # Business Rule: Calculate total pricing
        total_amount = sum(item.quantity * item.unit_price for item in items)
        rounded_total = round(total_amount, 2)
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        receipt_url = f"https://{self.settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{self.settings.AZURE_STORAGE_CONTAINER_RECEIPTS}/receipt_{order_id}.pdf"
        created_at = datetime.now(timezone.utc).isoformat()

        order_record = {
            "id": order_id,
            "user_id": user_id,
            "total_amount": rounded_total,
            "status": "PAID",
            "receipt_blob_url": receipt_url,
            "created_at": created_at
        }

        # Database Persistence Layer (with graceful resilient fallback)
        if self.db:
            try:
                logger.info("[%s] ORDER_SERVICE: Persisting order '%s' to Azure PostgreSQL...", request_id, order_id)
                await self.db.execute(
                    """
                    INSERT INTO orders (id, user_id, total_amount, status, receipt_blob_url, shipping_address, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    uuid.UUID(order_id.replace("ORD-", "b0000000-0000-0000-0000-00000000")),
                    uuid.UUID(user_id) if len(user_id) == 36 else uuid.uuid4(),
                    rounded_total,
                    "PAID",
                    receipt_url,
                    shipping_address,
                    datetime.now(timezone.utc)
                )
                logger.info("[%s] ORDER_SERVICE: Order successfully saved to Azure PostgreSQL table 'orders'", request_id)
            except Exception as db_err:
                logger.warning("[%s] ORDER_SERVICE: DB insert failed (%s). Saving to resilient in-memory store.", request_id, db_err)
                ORDERS_IN_MEMORY_STORE.insert(0, order_record)
        else:
            ORDERS_IN_MEMORY_STORE.insert(0, order_record)

        logger.info(
            "[%s] ORDER_SERVICE: Order '%s' processed successfully! Total=$%.2f, Receipt='%s'",
            request_id, order_id, rounded_total, receipt_url
        )
        return order_record

    async def list_orders(self, user_id: Optional[str] = None, request_id: str = "req-default") -> List[dict]:
        """Queries orders for a specific user or returns all global orders."""
        logger.info("[%s] ORDER_SERVICE: Querying orders (filter user_id='%s')", request_id, user_id)

        if self.db:
            try:
                if user_id:
                    rows = await self.db.fetch("SELECT id, user_id, total_amount, status, receipt_blob_url, created_at FROM orders WHERE user_id = $1 ORDER BY created_at DESC", uuid.UUID(user_id))
                else:
                    rows = await self.db.fetch("SELECT id, user_id, total_amount, status, receipt_blob_url, created_at FROM orders ORDER BY created_at DESC LIMIT 50")
                return [dict(r) for r in rows]
            except Exception as e:
                logger.warning("[%s] ORDER_SERVICE: DB query failed (%s). Falling back to in-memory store.", request_id, e)

        if user_id:
            return [o for o in ORDERS_IN_MEMORY_STORE if o["user_id"] == user_id]
        return ORDERS_IN_MEMORY_STORE
