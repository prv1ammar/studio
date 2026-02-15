import React, { useState, useEffect } from 'react';
import { X, UserPlus, Shield, Check, Mail, Plus, Trash2, Users, Globe, Layout, Loader2, List } from 'lucide-react';
import AuditLogViewer from './AuditLogViewer';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export default function WorkspaceModal({ isOpen, onClose, currentWorkspaceId, onWorkspaceSwitch }) {
    const [workspaces, setWorkspaces] = useState([]);
    const [members, setMembers] = useState([]);
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteRole, setInviteRole] = useState('editor');
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('workspaces'); // 'workspaces' or 'members'
    const [selectedWs, setSelectedWs] = useState(null);

    const token = localStorage.getItem('studio_token');
    const headers = { Authorization: `Bearer ${token}` };

    useEffect(() => {
        if (isOpen) {
            fetchWorkspaces();
        }
    }, [isOpen]);

    useEffect(() => {
        if (selectedWs) {
            fetchMembers(selectedWs.id);
        }
    }, [selectedWs]);

    const fetchWorkspaces = async () => {
        try {
            const res = await axios.get(`${API_BASE_URL}/workspaces/list`, { headers });
            setWorkspaces(res.data);
            if (currentWorkspaceId) {
                const current = res.data.find(w => w.id === currentWorkspaceId);
                if (current) setSelectedWs(current);
            } else if (res.data.length > 0) {
                setSelectedWs(res.data[0]);
            }
        } catch (e) {
            console.error("Fetch WS Error", e);
        }
    };

    const fetchMembers = async (wsId) => {
        try {
            const res = await axios.get(`${API_BASE_URL}/workspaces/${wsId}/members`, { headers });
            setMembers(res.data);
        } catch (e) {
            console.error("Fetch Members Error", e);
        }
    };

    const handleCreateWorkspace = async () => {
        const name = prompt("Enter Workspace Name:");
        if (!name) return;
        try {
            await axios.post(`${API_BASE_URL}/workspaces/create`, { name }, { headers });
            fetchWorkspaces();
        } catch (e) {
            alert("Failed to create workspace");
        }
    };

    const handleInvite = async (e) => {
        e.preventDefault();
        if (!inviteEmail || !selectedWs) return;
        setLoading(true);
        try {
            await axios.post(`${API_BASE_URL}/workspaces/${selectedWs.id}/invite?email=${inviteEmail}&role=${inviteRole}`, {}, { headers });
            setInviteEmail('');
            fetchMembers(selectedWs.id);
            alert("User invited successfully!");
        } catch (e) {
            alert(e.response?.data?.detail || "Failed to invite user");
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="dashboard-overlay" onClick={onClose}>
            <div className="dashboard-modal ws-modal" onClick={e => e.stopPropagation()}>
                <aside className="dashboard-sidebar">
                    <div className="sidebar-header">
                        <Globe size={20} />
                        <h3>Collaboration</h3>
                    </div>
                    <nav className="sidebar-nav">
                        <button
                            className={activeTab === 'workspaces' ? 'active' : ''}
                            onClick={() => setActiveTab('workspaces')}
                        >
                            <Layout size={16} /> My Workspaces
                        </button>
                        <button
                            className={activeTab === 'members' ? 'active' : ''}
                            onClick={() => setActiveTab('members')}
                        >
                            <Users size={16} /> Workspace Team
                        </button>
                        <button
                            className={activeTab === 'audit' ? 'active' : ''}
                            onClick={() => setActiveTab('audit')}
                        >
                            <Shield size={16} /> Audit Logs
                        </button>
                    </nav>
                </aside>

                <main className="dashboard-main">
                    <header className="dashboard-header">
                        <div className="header-info">
                            <h2>{activeTab === 'workspaces' ? 'Workspaces' : `${selectedWs?.name} Team`}</h2>
                            <p>{activeTab === 'workspaces' ? 'Manage your shared environments' : 'Invite and manage collaborators'}</p>
                        </div>
                        <div className="header-actions">
                            <button className="prime-btn" onClick={handleCreateWorkspace}>
                                <Plus size={16} /> New Workspace
                            </button>
                            <button className="close-btn" onClick={onClose}><X size={20} /></button>
                        </div>
                    </header>

                    <div className="dashboard-content">
                        {activeTab === 'workspaces' && (
                            <div className="ws-grid">
                                {workspaces.map(ws => (
                                    <div
                                        key={ws.id}
                                        className={`ws-card ${selectedWs?.id === ws.id ? 'active' : ''}`}
                                        onClick={() => {
                                            setSelectedWs(ws);
                                            onWorkspaceSwitch(ws.id);
                                        }}
                                    >
                                        <div className="ws-card-icon">
                                            {ws.name[0].toUpperCase()}
                                        </div>
                                        <div className="ws-info">
                                            <h4>{ws.name}</h4>
                                            <p>{ws.id === currentWorkspaceId ? 'Current Active' : 'Switch Workspace'}</p>
                                        </div>
                                        {selectedWs?.id === ws.id && <Check className="check-icon" size={16} />}
                                    </div>
                                ))}
                            </div>
                        )}

                        {activeTab === 'members' && selectedWs && (
                            <div className="members-view">
                                <form className="invite-bar" onSubmit={handleInvite}>
                                    <div className="input-group">
                                        <Mail size={16} />
                                        <input
                                            placeholder="Enter user email..."
                                            value={inviteEmail}
                                            onChange={e => setInviteEmail(e.target.value)}
                                            required
                                        />
                                    </div>
                                    <select value={inviteRole} onChange={e => setInviteRole(e.target.value)}>
                                        <option value="editor">Editor</option>
                                        <option value="viewer">Viewer</option>
                                        <option value="owner">Owner</option>
                                    </select>
                                    <button type="submit" disabled={loading} className="prime-btn success">
                                        {loading ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
                                        Invite
                                    </button>
                                </form>

                                <div className="members-table">
                                    <div className="table-header">
                                        <span>User</span>
                                        <span>Role</span>
                                        <span>Status</span>
                                    </div>
                                    {members.map(member => (
                                        <div key={member.id} className="member-row">
                                            <div className="member-user">
                                                <div className="avatar">{member.email[0].toUpperCase()}</div>
                                                <div className="details">
                                                    <strong>{member.full_name || 'Collaborator'}</strong>
                                                    <span>{member.email}</span>
                                                </div>
                                            </div>
                                            <div className="member-role">
                                                <span className={`badge ${member.role}`}>{member.role}</span>
                                            </div>
                                            <div className="member-status">
                                                <span className="dot active"></span> Active
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {activeTab === 'audit' && selectedWs && (
                            <div className="audit-view" style={{ flex: 1, overflow: 'hidden' }}>
                                <AuditLogViewer workspaceId={selectedWs.id} />
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}
