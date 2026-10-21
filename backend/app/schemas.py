from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------- 인증
class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=1, max_length=50)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(ORM):
    id: int
    email: str
    name: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------- 상품
class ProductOut(ORM):
    id: int
    name: str
    brand: str
    model_no: str
    category: str


class ProductDetailOut(ProductOut):
    listings_count: int


class ProductSearchItem(ProductOut):
    lowest_price: int | None = None
    score: int | None = None
    label: str = "HOLD"


class ProductRegisterIn(BaseModel):
    url: str = Field(min_length=10, max_length=500, pattern=r"^https?://")
    name: str | None = Field(default=None, max_length=100)


# ---------------------------------------------------------------- AI
class ChatIn(BaseModel):
    product_id: int
    question: str = Field(min_length=1, max_length=200)


# ---------------------------------------------------------------- 관심 상품
class WatchIn(BaseModel):
    product_id: int
    target_price: int | None = Field(default=None, ge=0)


class WatchPatch(BaseModel):
    target_price: int | None = Field(default=None, ge=0)


# ---------------------------------------------------------------- RPA
class PriceItem(BaseModel):
    listing_id: int
    price: int = Field(ge=0)
    shipping_fee: int = Field(default=0, ge=0)
    in_stock: bool = True


class PriceBulkIn(BaseModel):
    collected_at: datetime | None = None
    items: list[PriceItem] = Field(max_length=5000)


class PublicPriceItem(BaseModel):
    model_no: str
    good_id: str
    price: int = Field(ge=0)
    store_type: str | None = None
    survey_date: date


class PublicPriceIn(BaseModel):
    items: list[PublicPriceItem] = Field(max_length=5000)


class ModelUploadIn(BaseModel):
    version: str
    algorithm: str
    f1: float | None = None
    precision: float | None = None
    trained_rows: int = 0
    artifact_b64: str
    activate: bool = True


class JobLogIn(BaseModel):
    job_name: str = Field(max_length=50)
    status: str = Field(pattern=r"^(SUCCESS|PARTIAL|FAIL|RUNNING)$")
    collected: int = 0
    failed: int = 0
    message: str | None = Field(default=None, max_length=500)
    started_at: datetime
    ended_at: datetime | None = None
