from pydantic import BaseModel
from typing import List, Optional

class ScraperConfig(BaseModel):
    timeout: int = 25
    delay_ms: int = 900
    user_agent: Optional[str] = None
    max_product_pages_per_site: int = 0
    min_price: float = 100.0
    max_price: float = 2500.0
    dynamic_mode: str = "auto"  # auto, never, always
    keywords: List[str] = []
    exclude_keywords: List[str] = ["chair", "console"]  # Exclude gaming chairs and consoles
