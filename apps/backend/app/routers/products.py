from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/products", tags=["Product Catalog"])


class Product(BaseModel):
    id: str
    title: str
    category: str
    price: float
    stock_quantity: int
    image_url: str


PRODUCT_CATALOG: List[Product] = [
    Product(
        id="prod-101",
        title="Azure AKS Cloud Architecture Guide",
        category="Cloud & DevOps",
        price=49.99,
        stock_quantity=150,
        image_url="https://kubeopsaegisstprd.blob.core.windows.net/user-media/products/aks-guide.png"
    ),
    Product(
        id="prod-102",
        title="Terraform Enterprise IaC Guide",
        category="Cloud & DevOps",
        price=59.99,
        stock_quantity=200,
        image_url="https://kubeopsaegisstprd.blob.core.windows.net/user-media/products/terraform-guide.png"
    ),
    Product(
        id="prod-103",
        title="Autonomous SRE AI Agent Toolkit",
        category="Cloud & DevOps",
        price=89.99,
        stock_quantity=75,
        image_url="https://kubeopsaegisstprd.blob.core.windows.net/user-media/products/sre-agent.png"
    ),
    Product(
        id="prod-104",
        title="Mechanical Kubernetes Keycaps",
        category="Developer Gear",
        price=29.99,
        stock_quantity=500,
        image_url="https://kubeopsaegisstprd.blob.core.windows.net/user-media/products/keycaps.png"
    )
]


@router.get("", response_model=List[Product])
async def list_products(
    category: Optional[str] = Query(None, description="Filter products by category"),
    search: Optional[str] = Query(None, description="Search products by title")
):
    results = PRODUCT_CATALOG
    if category:
        results = [p for p in results if p.category.lower() == category.lower()]
    if search:
        results = [p for p in results if search.lower() in p.title.lower()]
    return results


@router.get("/{product_id}", response_model=Product)
async def get_product_details(product_id: str):
    for p in PRODUCT_CATALOG:
        if p.id == product_id:
            return p
    return PRODUCT_CATALOG[0]
