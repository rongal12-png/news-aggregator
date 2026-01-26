from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel

from app.db import get_db
from app.models import Comment, CommentReaction, Story, User
from app.api.endpoints.auth import get_current_user, require_auth

router = APIRouter()


# ============ SCHEMAS ============

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    content: str


class ReactionCreate(BaseModel):
    reaction_type: str  # like, dislike, heart, smile, frown


class UserInfo(BaseModel):
    id: int
    name: Optional[str]
    avatar_url: Optional[str]


class ReactionCount(BaseModel):
    like: int = 0
    dislike: int = 0
    heart: int = 0
    smile: int = 0
    frown: int = 0


class CommentResponse(BaseModel):
    id: int
    story_id: int
    user: UserInfo
    parent_id: Optional[int]
    content: str
    is_edited: bool
    is_deleted: bool
    created_at: str
    updated_at: str
    reactions: ReactionCount
    user_reaction: Optional[str] = None  # Current user's reaction
    reply_count: int = 0

    class Config:
        from_attributes = True


# ============ HELPER FUNCTIONS ============

def get_reaction_counts(db: Session, comment_id: int) -> dict:
    """Get reaction counts for a comment."""
    reactions = db.query(
        CommentReaction.reaction_type,
        func.count(CommentReaction.id).label('count')
    ).filter(
        CommentReaction.comment_id == comment_id
    ).group_by(CommentReaction.reaction_type).all()

    counts = {'like': 0, 'dislike': 0, 'heart': 0, 'smile': 0, 'frown': 0}
    for reaction_type, count in reactions:
        if reaction_type in counts:
            counts[reaction_type] = count
    return counts


def get_user_reaction(db: Session, comment_id: int, user_id: int) -> Optional[str]:
    """Get user's reaction to a comment."""
    reaction = db.query(CommentReaction).filter(
        CommentReaction.comment_id == comment_id,
        CommentReaction.user_id == user_id
    ).first()
    return reaction.reaction_type if reaction else None


def format_comment(
    comment: Comment,
    db: Session,
    current_user: Optional[User] = None
) -> dict:
    """Format a comment for response."""
    reactions = get_reaction_counts(db, comment.id)
    user_reaction = None
    if current_user:
        user_reaction = get_user_reaction(db, comment.id, current_user.id)

    reply_count = db.query(func.count(Comment.id)).filter(
        Comment.parent_id == comment.id,
        Comment.is_deleted == False
    ).scalar()

    return {
        "id": comment.id,
        "story_id": comment.story_id,
        "user": {
            "id": comment.user.id,
            "name": comment.user.name,
            "avatar_url": comment.user.avatar_url
        },
        "parent_id": comment.parent_id,
        "content": comment.content if not comment.is_deleted else "[deleted]",
        "is_edited": comment.is_edited,
        "is_deleted": comment.is_deleted,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
        "reactions": reactions,
        "user_reaction": user_reaction,
        "reply_count": reply_count
    }


# ============ ENDPOINTS ============

@router.get("/story/{story_id}")
async def get_story_comments(
    story_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comments for a story (top-level only)."""
    # Check story exists
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Get top-level comments (no parent)
    offset = (page - 1) * limit
    comments = db.query(Comment).filter(
        Comment.story_id == story_id,
        Comment.parent_id == None
    ).order_by(Comment.created_at.desc()).offset(offset).limit(limit).all()

    # Get total count
    total = db.query(func.count(Comment.id)).filter(
        Comment.story_id == story_id,
        Comment.parent_id == None
    ).scalar()

    return {
        "comments": [format_comment(c, db, user) for c in comments],
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": offset + len(comments) < total
    }


@router.get("/{comment_id}/replies")
async def get_comment_replies(
    comment_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get replies to a comment."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    offset = (page - 1) * limit
    replies = db.query(Comment).filter(
        Comment.parent_id == comment_id
    ).order_by(Comment.created_at.asc()).offset(offset).limit(limit).all()

    total = db.query(func.count(Comment.id)).filter(
        Comment.parent_id == comment_id
    ).scalar()

    return {
        "replies": [format_comment(r, db, user) for r in replies],
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": offset + len(replies) < total
    }


@router.post("/story/{story_id}")
async def create_comment(
    story_id: int,
    data: CommentCreate,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new comment on a story."""
    # Check story exists
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Validate content
    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    if len(content) > 5000:
        raise HTTPException(status_code=400, detail="Comment too long (max 5000 characters)")

    # If replying, check parent exists
    if data.parent_id:
        parent = db.query(Comment).filter(
            Comment.id == data.parent_id,
            Comment.story_id == story_id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    # Create comment
    comment = Comment(
        story_id=story_id,
        user_id=user.id,
        parent_id=data.parent_id,
        content=content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return format_comment(comment, db, user)


@router.put("/{comment_id}")
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update a comment (only by owner)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")

    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit deleted comment")

    # Validate content
    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    if len(content) > 5000:
        raise HTTPException(status_code=400, detail="Comment too long (max 5000 characters)")

    comment.content = content
    comment.is_edited = True
    comment.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(comment)

    return format_comment(comment, db, user)


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete a comment (soft delete if has replies)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    # Check if has replies
    has_replies = db.query(Comment).filter(Comment.parent_id == comment_id).first()

    if has_replies:
        # Soft delete - keep for replies
        comment.is_deleted = True
        comment.content = "[deleted]"
        db.commit()
    else:
        # Hard delete
        db.delete(comment)
        db.commit()

    return {"message": "Comment deleted"}


# ============ REACTIONS ============

@router.post("/{comment_id}/reactions")
async def add_reaction(
    comment_id: int,
    data: ReactionCreate,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add or update a reaction to a comment."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Validate reaction type
    valid_reactions = ['like', 'dislike', 'heart', 'smile', 'frown']
    if data.reaction_type not in valid_reactions:
        raise HTTPException(status_code=400, detail=f"Invalid reaction type. Must be one of: {', '.join(valid_reactions)}")

    # Check existing reaction
    existing = db.query(CommentReaction).filter(
        CommentReaction.comment_id == comment_id,
        CommentReaction.user_id == user.id
    ).first()

    if existing:
        if existing.reaction_type == data.reaction_type:
            # Remove reaction (toggle off)
            db.delete(existing)
            db.commit()
            return {
                "message": "Reaction removed",
                "reaction": None,
                "reactions": get_reaction_counts(db, comment_id)
            }
        else:
            # Update reaction
            existing.reaction_type = data.reaction_type
            db.commit()
    else:
        # Add new reaction
        reaction = CommentReaction(
            comment_id=comment_id,
            user_id=user.id,
            reaction_type=data.reaction_type
        )
        db.add(reaction)
        db.commit()

    return {
        "message": "Reaction added",
        "reaction": data.reaction_type,
        "reactions": get_reaction_counts(db, comment_id)
    }


@router.delete("/{comment_id}/reactions")
async def remove_reaction(
    comment_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Remove user's reaction from a comment."""
    deleted = db.query(CommentReaction).filter(
        CommentReaction.comment_id == comment_id,
        CommentReaction.user_id == user.id
    ).delete()
    db.commit()

    return {
        "message": "Reaction removed" if deleted else "No reaction to remove",
        "reactions": get_reaction_counts(db, comment_id)
    }
