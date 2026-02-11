import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Plus, Trash2, Shield, Key, ExternalLink } from 'lucide-react';

const API_BASE_URL = window.location.origin.includes('localhost') ? 'http://localhost:8000' : '';

export default function CredentialModal({ isOpen, onClose }) {
    const [credentials, setCredentials] = useState([]);
    const [isAdding, setIsAdding] = useState(false);
    const [newCred, setNewCred] = useState({ id: '', type: 'generic', name: '', data: {} });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) fetchCredentials();
    }, [isOpen]);

    const fetchCredentials = async () => {
        try {
            const resp = await axios.get(`${API_BASE_URL}/credentials/list`);
            setCredentials(resp.data.credentials || []);
        } catch (e) {
            console.error("Failed to fetch credentials", e);
        }
    };

    const handleCreate = async () => {
        if (!newCred.id || !newCred.name) return alert("ID and Name are required");
        setLoading(true);
        try {
            await axios.post(`${API_BASE_URL}/credentials/add`, newCred);
            setIsAdding(false);
            setNewCred({ id: '', type: 'generic', name: '', data: {} });
            fetchCredentials();
        } catch (e) {
            alert("Failed to add credential: " + e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(`Delete credential ${id}?`)) return;
        try {
            await axios.delete(`${API_BASE_URL}/credentials/${id}`);
            fetchCredentials();
        } catch (e) {
            alert("Failed to delete");
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="cred-modal-box">
                <header className="modal-header">
                    <div className="title-row">
                        <Shield size={18} className="accent-text" />
                        <h2>Secure Credential Manager</h2>
                    </div>
                    <button className="close-btn" onClick={onClose}><X size={20} /></button>
                </header>

                <div className="modal-content">
                    <p className="modal-subtext">
                        Manage your API keys and tokens securely. All data is encrypted using <b>AES-256 GCM</b> at rest.
                    </p>

                    {!isAdding ? (
                        <div className="cred-list">
                            <button className="add-cred-dash" onClick={() => setIsAdding(true)}>
                                <Plus size={16} /> Add New Credential
                            </button>

                            {credentials.length === 0 ? (
                                <div className="empty-creds">No credentials saved yet.</div>
                            ) : (
                                credentials.map(c => (
                                    <div key={c.value} className="cred-item">
                                        <div className="cred-info">
                                            <Key size={14} className="tertiary-text" />
                                            <span className="cred-name">{c.label}</span>
                                            <span className="cred-id-tag">{c.value}</span>
                                        </div>
                                        <button className="delete-btn" onClick={() => handleDelete(c.value)}>
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    ) : (
                        <div className="cred-form">
                            <div className="form-group">
                                <label>Unique ID (e.g. google_main)</label>
                                <input
                                    value={newCred.id}
                                    onChange={e => setNewCred({ ...newCred, id: e.target.value })}
                                    placeholder="my_secret_id"
                                />
                            </div>
                            <div className="form-group">
                                <label>Display Name</label>
                                <input
                                    value={newCred.name}
                                    onChange={e => setNewCred({ ...newCred, name: e.target.value })}
                                    placeholder="Main Google Account"
                                />
                            </div>
                            <div className="form-group">
                                <label>Type</label>
                                <select value={newCred.type} onChange={e => setNewCred({ ...newCred, type: e.target.value })}>
                                    <option value="generic">Generic API Key</option>
                                    <option value="google">Google OAuth</option>
                                    <option value="slack">Slack Token</option>
                                    <option value="hubspot">HubSpot</option>
                                    <option value="notion">Notion</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>JSON Data (Paste your key/token object here)</label>
                                <textarea
                                    rows={5}
                                    placeholder='{"token": "xoxb-...", "client_id": "..."}'
                                    onChange={e => {
                                        try {
                                            setNewCred({ ...newCred, data: JSON.parse(e.target.value) });
                                        } catch { /* wait for valid json */ }
                                    }}
                                />
                            </div>
                            <div className="form-actions">
                                <button className="secondary-btn" onClick={() => setIsAdding(false)}>Cancel</button>
                                <button className="prime-btn accent" onClick={handleCreate} disabled={loading}>
                                    {loading ? 'Saving...' : 'Save Encrypted'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
