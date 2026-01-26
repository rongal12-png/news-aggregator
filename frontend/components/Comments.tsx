'use client';

import { useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';
import { Locale } from '@/lib/i18n';
import {
  Comment,
  ReactionType,
  getStoryComments,
  getCommentReplies,
  createComment,
  updateComment,
  deleteComment,
  addReaction,
} from '@/lib/comments';

interface CommentsProps {
  storyId: number;
  locale: Locale;
}

const REACTION_EMOJIS: Record<ReactionType, string> = {
  like: '👍',
  dislike: '👎',
  heart: '❤️',
  smile: '😊',
  frown: '😠',
};

const texts = {
  en: {
    comments: 'Comments',
    login_to_comment: 'Login to comment',
    write_comment: 'Write a comment...',
    reply: 'Reply',
    edit: 'Edit',
    delete: 'Delete',
    cancel: 'Cancel',
    save: 'Save',
    post: 'Post',
    show_replies: 'Show replies',
    hide_replies: 'Hide replies',
    no_comments: 'No comments yet. Be the first to comment!',
    load_more: 'Load more comments',
    edited: '(edited)',
    deleted: '[deleted]',
    replying_to: 'Replying to',
    confirm_delete: 'Are you sure you want to delete this comment?',
  },
  he: {
    comments: 'תגובות',
    login_to_comment: 'התחבר כדי להגיב',
    write_comment: 'כתוב תגובה...',
    reply: 'הגב',
    edit: 'ערוך',
    delete: 'מחק',
    cancel: 'ביטול',
    save: 'שמור',
    post: 'פרסם',
    show_replies: 'הצג תגובות',
    hide_replies: 'הסתר תגובות',
    no_comments: 'אין תגובות עדיין. היה הראשון להגיב!',
    load_more: 'טען עוד תגובות',
    edited: '(נערך)',
    deleted: '[נמחק]',
    replying_to: 'מגיב ל',
    confirm_delete: 'האם אתה בטוח שברצונך למחוק תגובה זו?',
  },
};

function formatDate(dateStr: string, locale: Locale): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return locale === 'he' ? 'עכשיו' : 'just now';
  if (diffMins < 60) return locale === 'he' ? `לפני ${diffMins} דקות` : `${diffMins}m ago`;
  if (diffHours < 24) return locale === 'he' ? `לפני ${diffHours} שעות` : `${diffHours}h ago`;
  if (diffDays < 7) return locale === 'he' ? `לפני ${diffDays} ימים` : `${diffDays}d ago`;

  return date.toLocaleDateString(locale === 'he' ? 'he-IL' : 'en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function CommentItem({
  comment,
  locale,
  storyId,
  onReply,
  onUpdate,
  onDelete,
  depth = 0,
}: {
  comment: Comment;
  locale: Locale;
  storyId: number;
  onReply: (parentId: number, content: string) => Promise<void>;
  onUpdate: (commentId: number, content: string) => Promise<void>;
  onDelete: (commentId: number) => Promise<void>;
  depth?: number;
}) {
  const { user } = useAuth();
  const t = texts[locale];
  const [showReplies, setShowReplies] = useState(false);
  const [replies, setReplies] = useState<Comment[]>([]);
  const [loadingReplies, setLoadingReplies] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isReplying, setIsReplying] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [replyContent, setReplyContent] = useState('');
  const [reactions, setReactions] = useState(comment.reactions);
  const [userReaction, setUserReaction] = useState(comment.user_reaction);

  const isOwner = user?.id === comment.user.id;
  const canEdit = isOwner && !comment.is_deleted;
  const canDelete = isOwner || user?.is_admin;

  const loadReplies = async () => {
    if (loadingReplies) return;
    setLoadingReplies(true);
    try {
      const data = await getCommentReplies(comment.id);
      setReplies(data.replies);
      setShowReplies(true);
    } catch (err) {
      console.error('Failed to load replies:', err);
    } finally {
      setLoadingReplies(false);
    }
  };

  const handleReaction = async (type: ReactionType) => {
    if (!user) return;
    try {
      const result = await addReaction(comment.id, type);
      setReactions(result.reactions);
      setUserReaction(result.reaction);
    } catch (err) {
      console.error('Failed to add reaction:', err);
    }
  };

  const handleEdit = async () => {
    if (!editContent.trim()) return;
    try {
      await onUpdate(comment.id, editContent);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to edit comment:', err);
    }
  };

  const handleReply = async () => {
    if (!replyContent.trim()) return;
    try {
      await onReply(comment.id, replyContent);
      setReplyContent('');
      setIsReplying(false);
      // Reload replies
      await loadReplies();
    } catch (err) {
      console.error('Failed to reply:', err);
    }
  };

  const handleDelete = async () => {
    if (window.confirm(t.confirm_delete)) {
      await onDelete(comment.id);
    }
  };

  return (
    <div className={`comment-item depth-${Math.min(depth, 3)}`}>
      <div className="comment-header">
        <div className="comment-avatar">
          {comment.user.avatar_url ? (
            <img src={comment.user.avatar_url} alt="" />
          ) : (
            <span>{comment.user.name?.[0]?.toUpperCase() || '?'}</span>
          )}
        </div>
        <div className="comment-meta">
          <span className="comment-author">{comment.user.name || 'Anonymous'}</span>
          <span className="comment-time">
            {formatDate(comment.created_at, locale)}
            {comment.is_edited && <span className="edited-mark">{t.edited}</span>}
          </span>
        </div>
      </div>

      {isEditing ? (
        <div className="comment-edit">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={3}
          />
          <div className="edit-actions">
            <button onClick={handleEdit} className="btn-save">{t.save}</button>
            <button onClick={() => setIsEditing(false)} className="btn-cancel">{t.cancel}</button>
          </div>
        </div>
      ) : (
        <div className="comment-content">
          {comment.is_deleted ? t.deleted : comment.content}
        </div>
      )}

      {!comment.is_deleted && (
        <div className="comment-actions">
          <div className="reaction-buttons">
            {(Object.keys(REACTION_EMOJIS) as ReactionType[]).map((type) => (
              <button
                key={type}
                className={`reaction-btn ${userReaction === type ? 'active' : ''}`}
                onClick={() => handleReaction(type)}
                disabled={!user}
                title={type}
              >
                {REACTION_EMOJIS[type]}
                {reactions[type] > 0 && <span className="reaction-count">{reactions[type]}</span>}
              </button>
            ))}
          </div>

          <div className="action-buttons">
            {user && depth < 3 && (
              <button onClick={() => setIsReplying(!isReplying)} className="btn-action">
                {t.reply}
              </button>
            )}
            {canEdit && (
              <button onClick={() => setIsEditing(true)} className="btn-action">
                {t.edit}
              </button>
            )}
            {canDelete && (
              <button onClick={handleDelete} className="btn-action btn-delete">
                {t.delete}
              </button>
            )}
          </div>
        </div>
      )}

      {isReplying && (
        <div className="reply-form">
          <textarea
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            placeholder={`${t.replying_to} ${comment.user.name || 'Anonymous'}...`}
            rows={2}
          />
          <div className="reply-actions">
            <button onClick={handleReply} className="btn-save">{t.post}</button>
            <button onClick={() => setIsReplying(false)} className="btn-cancel">{t.cancel}</button>
          </div>
        </div>
      )}

      {comment.reply_count > 0 && !showReplies && (
        <button onClick={loadReplies} className="btn-show-replies" disabled={loadingReplies}>
          {loadingReplies ? '...' : `${t.show_replies} (${comment.reply_count})`}
        </button>
      )}

      {showReplies && replies.length > 0 && (
        <div className="replies">
          <button onClick={() => setShowReplies(false)} className="btn-hide-replies">
            {t.hide_replies}
          </button>
          {replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              locale={locale}
              storyId={storyId}
              onReply={onReply}
              onUpdate={onUpdate}
              onDelete={onDelete}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function Comments({ storyId, locale }: CommentsProps) {
  const { user } = useAuth();
  const t = texts[locale];
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [posting, setPosting] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);

  const loadComments = async (pageNum: number = 1, append: boolean = false) => {
    setLoading(true);
    try {
      const data = await getStoryComments(storyId, pageNum);
      if (append) {
        setComments((prev) => [...prev, ...data.comments]);
      } else {
        setComments(data.comments);
      }
      setHasMore(data.has_more);
      setTotal(data.total);
      setPage(pageNum);
    } catch (err) {
      console.error('Failed to load comments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComments();
  }, [storyId]);

  const handlePost = async () => {
    if (!newComment.trim() || posting) return;
    setPosting(true);
    try {
      const comment = await createComment(storyId, newComment);
      setComments((prev) => [comment, ...prev]);
      setNewComment('');
      setTotal((prev) => prev + 1);
    } catch (err) {
      console.error('Failed to post comment:', err);
    } finally {
      setPosting(false);
    }
  };

  const handleReply = async (parentId: number, content: string) => {
    await createComment(storyId, content, parentId);
  };

  const handleUpdate = async (commentId: number, content: string) => {
    const updated = await updateComment(commentId, content);
    setComments((prev) =>
      prev.map((c) => (c.id === commentId ? updated : c))
    );
  };

  const handleDelete = async (commentId: number) => {
    await deleteComment(commentId);
    setComments((prev) =>
      prev.map((c) =>
        c.id === commentId ? { ...c, is_deleted: true, content: '[deleted]' } : c
      )
    );
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      loadComments(page + 1, true);
    }
  };

  return (
    <section className="comments-section">
      <h2 className="section-title">
        {t.comments} {total > 0 && <span className="comment-count">({total})</span>}
      </h2>

      {user ? (
        <div className="comment-form">
          <div className="comment-input-wrapper">
            <div className="user-avatar">
              {user.avatar_url ? (
                <img src={user.avatar_url} alt="" />
              ) : (
                <span>{user.name?.[0]?.toUpperCase() || user.email[0].toUpperCase()}</span>
              )}
            </div>
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder={t.write_comment}
              rows={3}
            />
          </div>
          <button
            onClick={handlePost}
            disabled={!newComment.trim() || posting}
            className="btn-post"
          >
            {posting ? '...' : t.post}
          </button>
        </div>
      ) : (
        <div className="login-prompt">{t.login_to_comment}</div>
      )}

      <div className="comments-list">
        {loading && comments.length === 0 ? (
          <div className="loading">Loading...</div>
        ) : comments.length === 0 ? (
          <div className="no-comments">{t.no_comments}</div>
        ) : (
          <>
            {comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                locale={locale}
                storyId={storyId}
                onReply={handleReply}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
              />
            ))}
            {hasMore && (
              <button onClick={loadMore} disabled={loading} className="btn-load-more">
                {loading ? '...' : t.load_more}
              </button>
            )}
          </>
        )}
      </div>

      <style jsx>{`
        .comments-section {
          margin-top: var(--spacing-xl);
          padding-top: var(--spacing-xl);
          border-top: 1px solid var(--border-color);
        }

        .section-title {
          font-size: 1.25rem;
          font-weight: 600;
          margin-bottom: var(--spacing-lg);
          color: var(--text-primary);
        }

        .comment-count {
          color: var(--text-muted);
          font-weight: 400;
        }

        .comment-form {
          margin-bottom: var(--spacing-xl);
        }

        .comment-input-wrapper {
          display: flex;
          gap: var(--spacing-md);
          margin-bottom: var(--spacing-sm);
        }

        .user-avatar,
        .comment-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: var(--accent-color);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 600;
          flex-shrink: 0;
          overflow: hidden;
        }

        .user-avatar img,
        .comment-avatar img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .comment-form textarea,
        .comment-edit textarea,
        .reply-form textarea {
          flex: 1;
          padding: 12px;
          border: 1.5px solid var(--border-color);
          border-radius: var(--radius-md);
          background: var(--bg-primary);
          color: var(--text-primary);
          font-size: 0.9375rem;
          resize: vertical;
          min-height: 60px;
        }

        .comment-form textarea:focus,
        .comment-edit textarea:focus,
        .reply-form textarea:focus {
          outline: none;
          border-color: var(--accent-color);
        }

        .btn-post,
        .btn-save {
          background: var(--accent-color);
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: var(--radius-md);
          font-weight: 500;
          cursor: pointer;
          transition: background var(--transition-fast);
        }

        .btn-post:hover:not(:disabled),
        .btn-save:hover:not(:disabled) {
          background: var(--accent-hover);
        }

        .btn-post:disabled,
        .btn-save:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-cancel {
          background: transparent;
          border: 1px solid var(--border-color);
          padding: 10px 20px;
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          cursor: pointer;
        }

        .login-prompt {
          text-align: center;
          padding: var(--spacing-lg);
          color: var(--text-muted);
          background: var(--bg-secondary);
          border-radius: var(--radius-md);
          margin-bottom: var(--spacing-lg);
        }

        .comments-list {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-md);
        }

        .no-comments,
        .loading {
          text-align: center;
          padding: var(--spacing-xl);
          color: var(--text-muted);
        }

        .btn-load-more {
          display: block;
          width: 100%;
          padding: var(--spacing-md);
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .btn-load-more:hover:not(:disabled) {
          background: var(--bg-hover);
          color: var(--text-primary);
        }
      `}</style>

      <style jsx global>{`
        .comment-item {
          padding: var(--spacing-md);
          background: var(--bg-card);
          border-radius: var(--radius-md);
          border: 1px solid var(--border-color);
        }

        .comment-item.depth-1,
        .comment-item.depth-2,
        .comment-item.depth-3 {
          margin-inline-start: var(--spacing-lg);
          border-inline-start: 2px solid var(--accent-color);
        }

        .comment-header {
          display: flex;
          gap: var(--spacing-sm);
          margin-bottom: var(--spacing-sm);
        }

        .comment-avatar {
          width: 32px;
          height: 32px;
          font-size: 0.75rem;
        }

        .comment-meta {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .comment-author {
          font-weight: 500;
          color: var(--text-primary);
          font-size: 0.9375rem;
        }

        .comment-time {
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        .edited-mark {
          margin-inline-start: 4px;
          font-style: italic;
        }

        .comment-content {
          color: var(--text-secondary);
          line-height: 1.5;
          white-space: pre-wrap;
          margin-bottom: var(--spacing-sm);
        }

        .comment-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: var(--spacing-md);
          flex-wrap: wrap;
        }

        .reaction-buttons {
          display: flex;
          gap: 4px;
        }

        .reaction-btn {
          background: transparent;
          border: 1px solid transparent;
          padding: 4px 8px;
          border-radius: var(--radius-sm);
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 0.875rem;
          transition: all var(--transition-fast);
        }

        .reaction-btn:hover:not(:disabled) {
          background: var(--bg-hover);
          border-color: var(--border-color);
        }

        .reaction-btn.active {
          background: var(--accent-color);
          background-opacity: 0.1;
          border-color: var(--accent-color);
        }

        .reaction-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .reaction-count {
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        .action-buttons {
          display: flex;
          gap: var(--spacing-sm);
        }

        .btn-action {
          background: transparent;
          border: none;
          color: var(--text-muted);
          font-size: 0.8125rem;
          cursor: pointer;
          padding: 4px 8px;
          border-radius: var(--radius-sm);
        }

        .btn-action:hover {
          color: var(--text-primary);
          background: var(--bg-hover);
        }

        .btn-delete:hover {
          color: #ef4444;
        }

        .comment-edit,
        .reply-form {
          margin-top: var(--spacing-sm);
        }

        .edit-actions,
        .reply-actions {
          display: flex;
          gap: var(--spacing-sm);
          margin-top: var(--spacing-sm);
        }

        .btn-show-replies,
        .btn-hide-replies {
          background: transparent;
          border: none;
          color: var(--accent-color);
          font-size: 0.8125rem;
          cursor: pointer;
          padding: 8px 0;
          margin-top: var(--spacing-sm);
        }

        .btn-show-replies:hover,
        .btn-hide-replies:hover {
          text-decoration: underline;
        }

        .replies {
          margin-top: var(--spacing-md);
          display: flex;
          flex-direction: column;
          gap: var(--spacing-sm);
        }
      `}</style>
    </section>
  );
}
