"""
Defines the pagination models used for API responses including page info
and hypermedia links for HATEOAS-style navigation.
"""

from typing import List
from pydantic import BaseModel, Field, HttpUrl

class Pagination(BaseModel):
    """Basic pagination information."""
    page: int = Field(..., description="Current page number.")
    per_page: int = Field(..., description="Number of items per page.")
    total_items: int = Field(..., description="Total number of items.")
    total_pages: int = Field(..., description="Total number of pages.")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "per_page": 10,
                "total_items": 50,
                "total_pages": 5
            }
        }

class PaginationLink(BaseModel):
    """Defines a navigational pagination link."""
    rel: str
    href: HttpUrl
    method: str = "GET"

class EnhancedPagination(Pagination):
    """Extends basic pagination to include HATEOAS links."""
    links: List[PaginationLink] = []

    def add_link(self, rel: str, href: str):
        """Appends a link to the pagination."""
        self.links.append(PaginationLink(rel=rel, href=href))
