import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Folder, Calendar, DownloadCloud, Loader2, Trash2 } from 'lucide-react';
import { API_BASE_URL } from '../config';

const WorkflowBrowserModal = ({ isOpen, onClose, onLoadWorkflow, currentWorkspaceId }) => {
    const [workflows, setWorkflows] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (isOpen) {
            fetchWorkflows();
        }
    }, [isOpen, currentWorkspaceId]);

    const fetchWorkflows = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API_BASE_URL}/workflows/list`, {
                params: { workspace_id: currentWorkspaceId }
            });
            setWorkflows(res.data.workflows || []);
        } catch (err) {
            console.error('Failed to fetch workflows', err);
        } finally {
            setLoading(false);
        }
    };

    const handleLoad = async (name) => {
        try {
            const res = await axios.get(`${API_BASE_URL}/workflows/load/${name}`);
            if (res.data) {
                onLoadWorkflow(name, res.data);
            }
        } catch (err) {
            console.error('Failed to load workflow', err);
            alert('Could not load the workflow. Please try again.');
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content" style={{ maxWidth: '600px', width: '100%', padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border-default)' }}>
                            <Folder size={20} color="var(--text-primary)" />
                        </div>
                        <div>
                            <h2 style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--text-primary)', margin: 0 }}>My Workflows</h2>
                            <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', margin: '4px 0 0 0' }}>Manage and load your saved workflows</p>
                        </div>
                    </div>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer' }}>
                        <X size={20} />
                    </button>
                </div>

                <div style={{ minHeight: '300px', maxHeight: '60vh', overflowY: 'auto' }}>
                    {loading ? (
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                            <Loader2 size={24} className="animate-spin text-gray-500" />
                        </div>
                    ) : workflows.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-tertiary)' }}>
                            <Folder size={48} style={{ opacity: 0.2, margin: '0 auto 16px auto' }} />
                            <p>No workflows saved yet.</p>
                            <p style={{ fontSize: '13px', marginTop: '8px' }}>Create and save a workflow to see it here.</p>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {workflows.map((wfName, idx) => (
                                <div key={idx} style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: '16px',
                                    borderRadius: '8px',
                                    background: 'var(--bg-tertiary)',
                                    border: '1px solid var(--border-default)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: 'var(--primary)', opacity: 0.1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <Folder size={16} color="var(--primary)" />
                                        </div>
                                        <div>
                                            <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>{wfName}</h4>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleLoad(wfName)}
                                        className="prime-btn"
                                        style={{ fontSize: '13px', padding: '6px 16px', background: 'var(--primary)', color: 'white' }}
                                    >
                                        <DownloadCloud size={14} /> Open
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default WorkflowBrowserModal;
