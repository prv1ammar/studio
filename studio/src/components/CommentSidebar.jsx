import React, { useState, useEffect } from 'react';
import { X, MessageSquare, Send, User, Calendar, Trash2 } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export default function CommentSidebar({ isOpen, onClose, workflowId, selectedNodeId }) {
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState('');
    const [loading, setLoading] = useState(false);

    const token = localStorage.getItem('studio_token');
    const headers = { Authorization: `Bearer ${token}` };

    useEffect(() => {
        if (isOpen && workflowId) {
            fetchComments();
        }
    }, [isOpen, workflowId, selectedNodeId]);

    const fetchComments = async () => {
        try {
            const res = await axios.get(`${API_BASE_URL}/workspaces/workflows/${workflowId}/comments`, { headers });
            // If selectedNodeId is present, we could filter here or just show all
            setComments(res.data);
        } catch (e) {
            console.error("Fetch Comments Error", e);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!newComment.trim() || !workflowId) return;

        setLoading(true);
        try {
            await axios.post(`${API_BASE_URL}/workspaces/workflows/comments`, {
                workflow_id: workflowId,
                node_id: selectedNodeId || null,
                text: newComment
            }, { headers });
            setNewComment('');
            fetchComments();
        } catch (e) {
            alert("Failed to post comment");
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <aside className={`comment-sidebar ${isOpen ? 'open' : ''}`}>
            <div className="comment-sidebar-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <MessageSquare size={18} />
                    <h3>Collaborator Comments</h3>
                </div>
                <button className="close-btn" onClick={onClose}><X size={18} /></button>
            </div>

            <div className="comment-context-bar">
                {selectedNodeId ? (
                    <div className="node-context-tag">
                        Connected to Node: <code>{selectedNodeId.slice(0, 8)}...</code>
                    </div>
                ) : (
                    <div className="global-context-tag">General Feedback</div>
                )}
            </div>

            <div className="comments-list">
                {comments.length === 0 ? (
                    <div className="empty-comments">
                        <MessageSquare size={40} style={{ opacity: 0.1, marginBottom: '12px' }} />
                        <p>No feedback yet. Start the conversation!</p>
                    </div>
                ) : (
                    comments.filter(c => !selectedNodeId || c.node_id === selectedNodeId).map(comment => (
                        <div key={comment.id} className="comment-item">
                            <div className="comment-item-header">
                                <div className="comment-user">
                                    <div className="avatar micro">{comment.user_name[0].toUpperCase()}</div>
                                    <span className="user-name">{comment.user_name}</span>
                                </div>
                                <span className="comment-date">{new Date(comment.created_at).toLocaleDateString()}</span>
                            </div>
                            <div className="comment-text">{comment.text}</div>
                            {comment.node_id && !selectedNodeId && (
                                <div className="comment-node-id">Re: {comment.node_id.slice(0, 8)}</div>
                            )}
                        </div>
                    ))
                )}
            </div>

            <form className="comment-input-area" onSubmit={handleSend}>
                <textarea
                    placeholder={selectedNodeId ? "Add feedback to this node..." : "Add a general comment..."}
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSend(e);
                        }
                    }}
                />
                <button type="submit" disabled={loading || !newComment.trim()} className="send-comment-btn">
                    <Send size={16} />
                </button>
            </form>
        </aside>
    );
}
