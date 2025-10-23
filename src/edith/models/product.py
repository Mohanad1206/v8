from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Product(BaseModel):
    id: str = Field(..., description="Unique product ID")
    name: str = Field(..., description="Product name")
    price_egp: Optional[float] = Field(None, description="Price in EGP")
    currency: str = Field("EGP", description="Currency")
    url: str = Field(..., description="Product URL")
    image_url: Optional[str] = Field(None, description="Image URL")
    brand: Optional[str] = Field(None, description="Brand")
    category: Optional[str] = Field(None, description="Category")
    source: str = Field(..., description="Source site")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="Scraped timestamp")

    class Config:
        from_attributes = True
