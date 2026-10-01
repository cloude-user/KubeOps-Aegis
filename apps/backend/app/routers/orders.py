import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/orders", tags=["Order Checkout"])


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float


class CreateOrderRequest(BaseModel):
    user_id: str
    items: List[OrderItem]
    shipping_address: str


class Order(BaseModel):
    id: str
    user_id: str
    total_amount: float
    status: str
    receipt_blob_url: Optional[str] = None
    created_at: str


ORDERS_DB: List[Order] = []


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(request: CreateOrderRequest):
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item.")
    
    total = sum(item.quantity * item.unit_price for item in request.items)
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    order = Order(
        id=order_id,
        user_id=request.user_id,
        total_amount=round(total, 2),
        status="PAID",
        receipt_blob_url=f"https://kubeopsaegisstprd.blob.core.windows.net/order-receipts/receipt_{order_id}.pdf",
        created_at=datetime.now(timezone.utc).isoformat()
    )
    ORDERS_DB.insert(0, order)
    return order


@router.get("", response_model=List[Order])
async def list_user_orders(user_id: Optional[str] = None):
    if user_id:
        return [o for o in ORDERS_DB if o.user_id == user_id]
    return ORDERS_DB
