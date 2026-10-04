import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

try:
    from backend.app.dependencies import get_order_service, get_current_user, get_request_id
    from backend.app.services.order_service import OrderService
except ModuleNotFoundError:
    from apps.backend.app.dependencies import get_order_service, get_current_user, get_request_id
    from apps.backend.app.services.order_service import OrderService

logger = logging.getLogger("backend.routers.orders")

router = APIRouter(prefix="/orders", tags=["Order Checkout"])


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float


class CreateOrderRequest(BaseModel):
    items: List[OrderItem]
    shipping_address: str
    user_id: Optional[str] = None


class Order(BaseModel):
    id: str
    user_id: str
    total_amount: float
    status: str
    receipt_blob_url: Optional[str] = None
    created_at: str


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
    request_id: str = Depends(get_request_id)
):
    """
    HTTP Controller for Order Creation (Inversion of Control & Dependency Injection):
    FastAPI injects OrderService, Auth Context, and Correlation Request-ID.
    """
    logger.info("[%s] HTTP POST /api/v1/orders - User: '%s'", request_id, current_user["id"])

    if not request.items:
        logger.warning("[%s] HTTP 400 - Order rejected (empty items array)", request_id)
        raise HTTPException(status_code=400, detail="Order must contain at least one item.")

    effective_user_id = request.user_id or current_user["id"]

    order = await order_service.create_order(
        user_id=effective_user_id,
        items=request.items,
        shipping_address=request.shipping_address,
        request_id=request_id
    )
    return order


@router.get("", response_model=List[Order])
async def list_user_orders(
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
    request_id: str = Depends(get_request_id)
):
    """
    HTTP Controller for Order History:
    Delegates to injected OrderService.
    """
    filter_user_id = user_id or (current_user["id"] if current_user["role"] != "sre_admin" else None)
    logger.info("[%s] HTTP GET /api/v1/orders - Filter user: '%s'", request_id, filter_user_id)

    orders = await order_service.list_orders(user_id=filter_user_id, request_id=request_id)
    return orders
