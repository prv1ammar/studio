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

    const handleTest = async (id) => {
        try {
            const resp = await axios.post(`${API_BASE_URL}/credentials/${id}/test`);
            alert(resp.data.message || "Connection successful!");
        } catch (e) {
            alert("Test failed: " + (e.response?.data?.detail || e.message));
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
                                            <div>
                                                <div className="cred-name">{c.label}</div>
                                                <div className="cred-id-tag">{c.value}</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                className="secondary-btn"
                                                style={{ padding: '4px 8px', fontSize: '10px' }}
                                                onClick={() => handleTest(c.value)}
                                            >
                                                Test
                                            </button>
                                            <button className="delete-btn" onClick={() => handleDelete(c.value)}>
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
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
                                    placeholder="Main Account"
                                />
                            </div>
                            <div className="form-group">
                                <label>Service Type</label>
                                <select value={newCred.type} onChange={e => setNewCred({ ...newCred, type: e.target.value, data: {} })}>
                                    <option value="generic">Generic API Key</option>
                                    <option value="google">Google OAuth</option>
                                    <option value="slack">Slack Token</option>
                                    <option value="hubspot">HubSpot</option>
                                    <option value="salesforce">Salesforce</option>
                                    <option value="pipedrive">Pipedrive</option>
                                    <option value="discord">Discord</option>
                                    <option value="telegram">Telegram</option>
                                    <option value="mailchimp">Mailchimp</option>
                                    <option value="notion">Notion</option>
                                </select>
                            </div>

                            {/* Dynamic Fields based on Type */}
                            <div className="dynamic-cred-fields">
                                {newCred.type === 'hubspot' && (
                                    <div className="form-group">
                                        <label>Private App Access Token</label>
                                        <input
                                            type="password"
                                            placeholder="pat-na1-..."
                                            onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, api_key: e.target.value } })}
                                        />
                                    </div>
                                )}
                                {newCred.type === 'discord' && (
                                    <>
                                        <div className="form-group">
                                            <label>Webhook URL</label>
                                            <input
                                                placeholder="https://discord.com/api/webhooks/..."
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, webhook_url: e.target.value } })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Bot Name Override</label>
                                            <input
                                                placeholder="Studio Bot"
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, bot_name: e.target.value } })}
                                            />
                                        </div>
                                    </>
                                )}
                                {newCred.type === 'telegram' && (
                                    <>
                                        <div className="form-group">
                                            <label>Bot Token</label>
                                            <input
                                                type="password"
                                                placeholder="123456789:ABC..."
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, bot_token: e.target.value } })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Default Chat ID</label>
                                            <input
                                                placeholder="-100..."
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, chat_id: e.target.value } })}
                                            />
                                        </div>
                                    </>
                                )}
                                {newCred.type === 'mailchimp' && (
                                    <>
                                        <div className="form-group">
                                            <label>API Key</label>
                                            <input
                                                type="password"
                                                placeholder="abc...-us20"
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, api_key: e.target.value } })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Audience (List) ID</label>
                                            <input
                                                placeholder="a1b2c3d4"
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, list_id: e.target.value } })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Server Prefix</label>
                                            <input
                                                placeholder="us20"
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, server_prefix: e.target.value } })}
                                            />
                                        </div>
                                    </>
                                )}
                                {newCred.type === 'salesforce' && (
                                    <>
                                        <div className="form-group">
                                            <label>Instance URL</label>
                                            <input
                                                placeholder="https://custom.my.salesforce.com"
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, instance_url: e.target.value } })}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Access Token</label>
                                            <input
                                                type="password"
                                                onChange={e => setNewCred({ ...newCred, data: { ...newCred.data, access_token: e.target.value } })}
                                            />
                                        </div>
                                    </>
                                )}
                                {newCred.type === 'generic' && (
                                    <div className="form-group">
                                        <label>JSON Data</label>
                                        <textarea
                                            rows={5}
                                            placeholder='{"api_key": "...", "secret": "..."}'
                                            onChange={e => {
                                                try {
                                                    setNewCred({ ...newCred, data: JSON.parse(e.target.value) });
                                                } catch { }
                                            }}
                                        />
                                    </div>
                                )}
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
