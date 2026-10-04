import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

try:
    from backend.app.dependencies import get_db_connection, get_request_id
except ModuleNotFoundError:
    from apps.backend.app.dependencies import get_db_connection, get_request_id

logger = logging.getLogger("backend.routers.products")

router = APIRouter(prefix="/products", tags=["Product Catalog"])


class Product(BaseModel):
    id: str
    title: str
    category: str
    price: float
    stock_quantity: int
    image_url: str


# In-Memory Fallback Catalog (Used when running offline or if DB is momentarily unreachable)
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
    search: Optional[str] = Query(None, description="Search products by title"),
    db=Depends(get_db_connection),
    request_id: str = Depends(get_request_id)
):
    """
    Retrieves the product catalog using Pure SQL via asyncpg.
    Features:
    - Pure parameterized SQL queries with zero ORM overhead
    - Resilient fallback to static catalog if DB is unreachable
    """
    logger.info("[%s] AUDIT_CATALOG: Querying catalog (category='%s', search='%s')", request_id, category, search)

    if db:
        try:
            query = """
                SELECT p.id::text, p.title, COALESCE(c.name, 'General') AS category,
                       p.price::float, p.stock_quantity, COALESCE(p.image_blob_url, '') AS image_url
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = TRUE
            """
            params = []
            if category:
                params.append(category.lower())
                query += f" AND LOWER(c.name) = ${len(params)}"
            if search:
                params.append(f"%{search.lower()}%")
                query += f" AND LOWER(p.title) LIKE ${len(params)}"
            query += " ORDER BY p.created_at DESC LIMIT 100"

            rows = await db.fetch(query, *params)
            if rows:
                results = [Product(**dict(r)) for r in rows]
                logger.info("[%s] AUDIT_CATALOG: Retrieved %d live products from Azure PostgreSQL", request_id, len(results))
                return results
        except Exception as e:
            logger.warning("[%s] AUDIT_CATALOG: Live PostgreSQL query error (%s). Using fallback catalog.", request_id, e)

    # Resilient fallback
    results = PRODUCT_CATALOG
    if category:
        results = [p for p in results if p.category.lower() == category.lower()]
    if search:
        results = [p for p in results if search.lower() in p.title.lower()]

    logger.info("[%s] AUDIT_CATALOG: Returning %d fallback catalog products", request_id, len(results))
    return results


@router.get("/{product_id}", response_model=Product)
async def get_product_details(
    product_id: str,
    db=Depends(get_db_connection),
    request_id: str = Depends(get_request_id)
):
    """Retrieves product details by ID using pure parameterized SQL."""
    logger.info("[%s] AUDIT_CATALOG: Looking up product ID='%s'", request_id, product_id)

    if db:
        try:
            row = await db.fetchrow(
                """
                SELECT p.id::text, p.title, COALESCE(c.name, 'General') AS category,
                       p.price::float, p.stock_quantity, COALESCE(p.image_blob_url, '') AS image_url
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id::text = $1 OR p.title ILIKE $2
                """,
                product_id, f"%{product_id}%"
            )
            if row:
                logger.info("[%s] AUDIT_CATALOG: Found product '%s' in Azure PostgreSQL", request_id, row["title"])
                return Product(**dict(row))
        except Exception as e:
            logger.warning("[%s] AUDIT_CATALOG: DB lookup error (%s). Falling back.", request_id, e)

    for p in PRODUCT_CATALOG:
        if p.id == product_id:
            return p

    logger.warning("[%s] AUDIT_CATALOG: Product ID '%s' not found", request_id, product_id)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found.")
