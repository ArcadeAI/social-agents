from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from common.schemas import DocumentCategory


class AIGeneratedComment(BaseModel):
    """Schema for AI-generated comments."""

    id: str = Field(description="Unique identifier for the comment")
    document_id: str = Field(description="ID of the document this comment relates to")
    content: str = Field(description="The AI-generated comment content")
    tone: DocumentCategory = Field(description="The tone/category of the comment")
    created_at: datetime = Field(default_factory=datetime.now, description="When the comment was created")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the comment generation",
    )


class SubredditConfig(BaseModel):
    """Configuration for a subreddit to be processed."""

    subreddit: str = Field(description="The subreddit name")
    time_range: str = Field(description="Time range for fetching posts")
    limit: int = Field(description="Maximum number of posts to fetch")
    target_number: int = Field(description="Target number of posts to return")
    audience_specification: str = Field(description="Audience specification for content filtering")
    subreddit_description: str = Field(description="Description of the subreddit")
    active: bool = Field(default=True, description="Whether this subreddit is active for processing")
    created_at: datetime = Field(default_factory=datetime.now, description="When the subreddit was added")