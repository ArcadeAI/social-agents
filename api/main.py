import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from common.schemas import Document, AIGeneratedComment, SubredditConfig
from parser_agents.reddit.agent import get_content, InputSchema
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Stream Agent API",
    description="API for managing subreddits, documents, and AI-generated comments",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
subreddits_store: Dict[str, SubredditConfig] = {}
documents_store: Dict[str, Document] = {}
comments_store: Dict[str, AIGeneratedComment] = {}

# Response models
class SubredditResponse(BaseModel):
    id: str
    config: SubredditConfig

class DocumentResponse(BaseModel):
    id: str
    document: Document

class CommentResponse(BaseModel):
    id: str
    comment: AIGeneratedComment

class ProcessSubredditResponse(BaseModel):
    subreddit: str
    documents_count: int
    document_ids: List[str]

# Subreddit endpoints
@app.post("/subreddits/", response_model=SubredditResponse)
async def add_subreddit(config: SubredditConfig):
    """Add a new subreddit configuration."""
    subreddit_id = str(uuid.uuid4())
    subreddits_store[subreddit_id] = config
    logger.info(f"Added subreddit: {config.subreddit}")
    return SubredditResponse(id=subreddit_id, config=config)

@app.get("/subreddits/", response_model=List[SubredditResponse])
async def get_subreddits():
    """Get all subreddit configurations."""
    return [SubredditResponse(id=id, config=config) for id, config in subreddits_store.items()]

@app.get("/subreddits/{subreddit_id}", response_model=SubredditResponse)
async def get_subreddit(subreddit_id: str):
    """Get a specific subreddit configuration."""
    if subreddit_id not in subreddits_store:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    return SubredditResponse(id=subreddit_id, config=subreddits_store[subreddit_id])

@app.put("/subreddits/{subreddit_id}", response_model=SubredditResponse)
async def update_subreddit(subreddit_id: str, config: SubredditConfig):
    """Update a subreddit configuration."""
    if subreddit_id not in subreddits_store:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    subreddits_store[subreddit_id] = config
    logger.info(f"Updated subreddit: {config.subreddit}")
    return SubredditResponse(id=subreddit_id, config=config)

@app.delete("/subreddits/{subreddit_id}")
async def delete_subreddit(subreddit_id: str):
    """Delete a subreddit configuration."""
    if subreddit_id not in subreddits_store:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    config = subreddits_store.pop(subreddit_id)
    logger.info(f"Deleted subreddit: {config.subreddit}")
    return {"message": f"Subreddit {config.subreddit} deleted successfully"}

@app.post("/subreddits/{subreddit_id}/process", response_model=ProcessSubredditResponse)
async def process_subreddit(subreddit_id: str):
    """Process a subreddit and save the documents."""
    if subreddit_id not in subreddits_store:
        raise HTTPException(status_code=404, detail="Subreddit not found")

    config = subreddits_store[subreddit_id]

    # Convert SubredditConfig to InputSchema
    input_schema = InputSchema(
        subreddit=config.subreddit,
        time_range=config.time_range,
        limit=config.limit,
        target_number=config.target_number,
        audience_specification=config.audience_specification,
        subreddit_description=config.subreddit_description
    )

    try:
        # Get content from the subreddit
        documents = await get_content(input_schema)

        # Save documents to storage
        document_ids = []
        for doc in documents:
            doc_id = str(uuid.uuid4())
            documents_store[doc_id] = doc
            document_ids.append(doc_id)

        logger.info(f"Processed subreddit {config.subreddit}: {len(documents)} documents saved")

        return ProcessSubredditResponse(
            subreddit=config.subreddit,
            documents_count=len(documents),
            document_ids=document_ids
        )
    except Exception as e:
        logger.error(f"Error processing subreddit {config.subreddit}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing subreddit: {str(e)}")

# Document endpoints
@app.get("/documents/", response_model=List[DocumentResponse])
async def get_documents():
    """Get all saved documents."""
    return [DocumentResponse(id=id, document=doc) for id, doc in documents_store.items()]

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get a specific document."""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(id=document_id, document=documents_store[document_id])

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document."""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = documents_store.pop(document_id)
    logger.info(f"Deleted document: {document_id}")
    return {"message": f"Document {document_id} deleted successfully"}

# AI-generated comment endpoints
@app.post("/comments/", response_model=CommentResponse)
async def add_comment(comment: AIGeneratedComment):
    """Add a new AI-generated comment."""
    comment_id = str(uuid.uuid4())
    # Create a new comment with the generated ID
    new_comment = AIGeneratedComment(
        id=comment_id,
        document_id=comment.document_id,
        content=comment.content,
        tone=comment.tone,
        metadata=comment.metadata
    )
    comments_store[comment_id] = new_comment
    logger.info(f"Added comment for document: {comment.document_id}")
    return CommentResponse(id=comment_id, comment=new_comment)

@app.get("/comments/", response_model=List[CommentResponse])
async def get_comments():
    """Get all AI-generated comments."""
    return [CommentResponse(id=id, comment=comment) for id, comment in comments_store.items()]

@app.get("/comments/{comment_id}", response_model=CommentResponse)
async def get_comment(comment_id: str):
    """Get a specific AI-generated comment."""
    if comment_id not in comments_store:
        raise HTTPException(status_code=404, detail="Comment not found")
    return CommentResponse(id=comment_id, comment=comments_store[comment_id])

@app.get("/documents/{document_id}/comments", response_model=List[CommentResponse])
async def get_document_comments(document_id: str):
    """Get all comments for a specific document."""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document_comments = [
        CommentResponse(id=id, comment=comment)
        for id, comment in comments_store.items()
        if comment.document_id == document_id
    ]
    return document_comments

@app.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str):
    """Delete an AI-generated comment."""
    if comment_id not in comments_store:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment = comments_store.pop(comment_id)
    logger.info(f"Deleted comment: {comment_id}")
    return {"message": f"Comment {comment_id} deleted successfully"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "subreddits_count": len(subreddits_store),
        "documents_count": len(documents_store),
        "comments_count": len(comments_store)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)