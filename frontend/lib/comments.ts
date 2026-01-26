// Comments API client
import { authHeaders, getToken } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface CommentUser {
  id: number;
  name: string | null;
  avatar_url: string | null;
}

export interface ReactionCounts {
  like: number;
  dislike: number;
  heart: number;
  smile: number;
  frown: number;
}

export type ReactionType = 'like' | 'dislike' | 'heart' | 'smile' | 'frown';

export interface Comment {
  id: number;
  story_id: number;
  user: CommentUser;
  parent_id: number | null;
  content: string;
  is_edited: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  reactions: ReactionCounts;
  user_reaction: ReactionType | null;
  reply_count: number;
}

export interface CommentsResponse {
  comments: Comment[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

export interface RepliesResponse {
  replies: Comment[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// Get comments for a story
export async function getStoryComments(
  storyId: number,
  page: number = 1,
  limit: number = 20
): Promise<CommentsResponse> {
  const res = await fetch(
    `${API_URL}/comments/story/${storyId}?page=${page}&limit=${limit}`,
    {
      headers: authHeaders(),
      cache: 'no-store',
    }
  );

  if (!res.ok) {
    throw new Error('Failed to fetch comments');
  }

  return res.json();
}

// Get replies to a comment
export async function getCommentReplies(
  commentId: number,
  page: number = 1,
  limit: number = 10
): Promise<RepliesResponse> {
  const res = await fetch(
    `${API_URL}/comments/${commentId}/replies?page=${page}&limit=${limit}`,
    {
      headers: authHeaders(),
      cache: 'no-store',
    }
  );

  if (!res.ok) {
    throw new Error('Failed to fetch replies');
  }

  return res.json();
}

// Create a new comment
export async function createComment(
  storyId: number,
  content: string,
  parentId?: number
): Promise<Comment> {
  const res = await fetch(`${API_URL}/comments/story/${storyId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({
      content,
      parent_id: parentId || null,
    }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to create comment');
  }

  return res.json();
}

// Update a comment
export async function updateComment(
  commentId: number,
  content: string
): Promise<Comment> {
  const res = await fetch(`${API_URL}/comments/${commentId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ content }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to update comment');
  }

  return res.json();
}

// Delete a comment
export async function deleteComment(commentId: number): Promise<void> {
  const res = await fetch(`${API_URL}/comments/${commentId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to delete comment');
  }
}

// Add or toggle reaction
export async function addReaction(
  commentId: number,
  reactionType: ReactionType
): Promise<{ reaction: ReactionType | null; reactions: ReactionCounts }> {
  const res = await fetch(`${API_URL}/comments/${commentId}/reactions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({ reaction_type: reactionType }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to add reaction');
  }

  return res.json();
}

// Remove reaction
export async function removeReaction(
  commentId: number
): Promise<{ reactions: ReactionCounts }> {
  const res = await fetch(`${API_URL}/comments/${commentId}/reactions`, {
    method: 'DELETE',
    headers: authHeaders(),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to remove reaction');
  }

  return res.json();
}

// Check if user is logged in
export function isLoggedIn(): boolean {
  return !!getToken();
}
