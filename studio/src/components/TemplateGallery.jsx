import React, { useEffect, useState } from 'react';
import { MessageSquare, BookOpen, Globe, Layout, X, Zap, Download, Tags, Cpu, Box, Loader2 } from 'lucide-react';
import axios from 'axios';
import '../Templates.css';
import { API_BASE_URL } from '../config';

const TemplateGallery = ({ currentWorkspaceId, onCloneSuccess, onClose }) => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [cloningId, setCloningId] = useState(null);
    const [view, setView] = useState('marketplace'); // 'marketplace' or 'workspace'

    useEffect(() => {
        const fetchTemplates = async () => {
            setLoading(true);
            try {
                const token = localStorage.getItem('studio_token');
                const isMarketplace = view === 'marketplace';
                const res = await axios.get(`${API_BASE_URL}/templates/list`, {
                    params: {
                        workspace_id: currentWorkspaceId,
                        public_only: isMarketplace
                    },
                    headers: { Authorization: `Bearer ${token}` }
                });
                setTemplates(res.data || []);
            } catch (err) {
                console.error("Templates fetch error:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchTemplates();
    }, [view, currentWorkspaceId]);

    const handleClone = async (templateId) => {
        if (!currentWorkspaceId) {
            alert("Please select or create a workspace first.");
            return;
        }
        setCloningId(templateId);
        try {
            const token = localStorage.getItem('studio_token');
            const res = await axios.post(`${API_BASE_URL}/templates/clone/${templateId}?workspace_id=${currentWorkspaceId}`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (res.data.status === 'success') {
                onCloneSuccess(res.data);
                onClose();
            }
        } catch (err) {
            console.error("Cloning failed:", err);
            alert("Failed to clone template: " + (err.response?.data?.detail || err.message));
        } finally {
            setCloningId(null);
        }
    };

    return (
        <div className="template-overlay">
            <div className="template-modal" onClick={(e) => e.stopPropagation()}>
                <div className="template-header">
                    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                        <div className="logo-shield" style={{ width: 44, height: 44, background: 'var(--accent)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Cpu size={24} color="#ffffff" />
                        </div>
                        <div>
                            <h2 style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--text-primary)', margin: 0, lineHeight: 1 }}>
                                Blueprint Marketplace
                            </h2>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '6px', margin: '4px 0 0 0' }}>
                                Jumpstart your AI agents with pre-built neural architectures.
                            </p>
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                        <div style={{ display: 'flex', background: 'var(--bg-app)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-default)' }}>
                            <button
                                onClick={() => setView('marketplace')}
                                style={{
                                    padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                                    background: view === 'marketplace' ? 'var(--accent)' : 'transparent',
                                    color: view === 'marketplace' ? '#ffffff' : 'var(--text-primary)',
                                    fontWeight: 600, fontSize: '0.85rem', transition: '0.2s'
                                }}
                            >
                                Global Market
                            </button>
                            <button
                                onClick={() => setView('workspace')}
                                style={{
                                    padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                                    background: view === 'workspace' ? 'var(--accent)' : 'transparent',
                                    color: view === 'workspace' ? '#ffffff' : 'var(--text-primary)',
                                    fontWeight: 600, fontSize: '0.85rem', transition: '0.2s'
                                }}
                            >
                                Workspace
                            </button>
                        </div>

                        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', padding: '8px' }}>
                            <X size={28} />
                        </button>
                    </div>
                </div>

                <div className="template-grid">
                    {loading ? (
                        <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '10rem' }}>
                            <Loader2 size={40} className="animate-spin" style={{ margin: '0 auto 1rem auto', color: 'var(--accent)' }} />
                            <span style={{ color: 'var(--accent)', fontWeight: 700, letterSpacing: '2px' }}>LOADING ARCHITECTURES...</span>
                        </div>
                    ) : templates.length === 0 ? (
                        <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '10rem', color: 'var(--text-secondary)' }}>
                            <div style={{ marginBottom: '1rem', opacity: 0.5 }}><Box size={48} style={{ margin: '0 auto' }} /></div>
                            <h3 style={{ color: 'var(--text-primary)', fontSize: '1.25rem', fontWeight: 600 }}>No {view} blueprints found.</h3>
                            <p style={{ fontSize: '0.95rem', marginTop: '0.5rem', color: 'var(--text-tertiary)' }}>
                                {view === 'workspace' ? "Publish one of your workflows as a template to see it here!" : "The marketplace is currently empty."}
                            </p>
                        </div>
                    ) : (
                        templates.map(t => (
                            <div key={t.id} className="template-card">
                                <div className="use-badge" onClick={() => handleClone(t.id)}>
                                    {cloningId === t.id ? 'CLONING...' : 'DEPLOY TEMPLATE'}
                                </div>
                                <div className="template-icon-box">
                                    <Layout size={28} />
                                </div>
                                <h3 style={{ color: 'var(--text-primary)', fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.75rem' }}>{t.name}</h3>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>{t.description}</p>

                                <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem', flexWrap: 'wrap' }}>
                                    {(t.tags || []).map((tag, i) => (
                                        <span key={i} style={{ fontSize: '0.7rem', color: 'var(--accent)', background: 'var(--bg-elevated)', padding: '2px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                                            #{tag}
                                        </span>
                                    ))}
                                </div>

                                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: 'auto' }}>
                                    {(t.definition?.nodes || []).slice(0, 4).map((n, i) => (
                                        <span key={i} style={{
                                            fontSize: '0.65rem',
                                            padding: '4px 10px',
                                            background: 'var(--bg-surface)',
                                            borderRadius: '6px',
                                            color: 'var(--text-secondary)',
                                            fontWeight: 600,
                                            textTransform: 'uppercase',
                                            border: '1px solid var(--border-default)'
                                        }}>
                                            {n.type.split('_').join(' ')}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default TemplateGallery;
