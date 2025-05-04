"""Schema for creating a URL link"""
# pylint: disable=unused-argument
# pylint: disable=unused-import

from pydantic import BaseModel, Field, HttpUrl

class Link(BaseModel):
    """URL Link functionality"""
    rel: str = Field(..., description="Relation type of the link.")
    href: HttpUrl = Field(..., description="The URL of the link.")
    action: str = Field(
        ..., description="HTTP method for the action this link represents."
    )
    type: str = Field(
        default="application/json",
        description="Content type of the response for this link.",
    )

    class Config:
        """Configuration schema"""
        json_schema_extra = {
            "example": {
                "rel": "self",
                "href": "https://api.example.com/qr/123",
                "action": "GET",
                "type": "application/json",
            }
        }
