"""Product endpoints."""
from typing import List
from api.router import Router
from api.deps import get_current_user_required, get_db_session
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from models.product import Product
from models.user import User


router = Router()


@router.get("/")
async def list_products(session):
    # List all public products
    products = []  # Would query from database
    return [ProductResponse.from_model(p) for p in products]


@router.get("/{product_id}")
async def get_product(product_id: str, session):
    product = Product(id=product_id)  # Would query from database
    return ProductResponse.from_model(product)


@router.post("/")
async def create_product(data: ProductCreate, user: User, session):
    product = Product(
        id="new_product",
        name=data.name,
        description=data.description,
        price=data.price,
        owner_id=user.id,
    )
    return ProductResponse.from_model(product)


@router.post("/{product_id}")
async def update_product(product_id: str, data: ProductUpdate, session):
    product = Product(id=product_id)
    # Update fields
    return ProductResponse.from_model(product)
