import React, { useEffect, useState } from 'react';
import { MessageSquare, BookOpen, Globe, Layout, X, Zap, Download, Tags, Cpu } from 'lucide-react';
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
            <div className="template-modal">
                <div className="template-header">
                    <div>
                        <h2 style={{ fontSize: '1.8rem', fontWeight: 900, color: 'white', display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <div className="logo-shield" style={{ width: 44, height: 44 }}>
                                <Cpu size={24} color="white" />
                            </div>
                            Blueprint Marketplace
                        </h2>
                        <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', marginTop: '6px' }}>
                            Jumpstart your AI agents with pre-built neural architectures.
                        </p>
                    </div>

                    <div style={{ display: 'flex', background: 'rgba(255,255,255,0.05)', padding: '4px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                        <button
                            onClick={() => setView('marketplace')}
                            style={{
                                padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                                background: view === 'marketplace' ? 'var(--accent-blue)' : 'transparent',
                                color: 'white', fontWeight: 600, fontSize: '0.85rem', transition: '0.2s'
                            }}
                        >
                            Global Market
                        </button>
                        <button
                            onClick={() => setView('workspace')}
                            style={{
                                padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                                background: view === 'workspace' ? 'var(--accent-blue)' : 'transparent',
                                color: 'white', fontWeight: 600, fontSize: '0.85rem', transition: '0.2s'
                            }}
                        >
                            Workspace
                        </button>
                    </div>

                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-white)' }}>
                        <X size={32} />
                    </button>
                </div>

                <div className="template-grid">
                    {loading ? (
                        <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '10rem' }}>
                            <div className="animate-spin" style={{ margin: '0 auto 1rem auto', width: 40, height: 40, border: '4px solid var(--accent-blue)', borderRightColor: 'transparent', borderRadius: '50%' }} />
                            <span style={{ color: 'var(--accent-blue)', fontWeight: 700, letterSpacing: '2px' }}>LOADING ARCHITECTURES...</span>
                        </div>
                    ) : templates.length === 0 ? (
                        <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '10rem', color: 'var(--text-dim)' }}>
                            <div style={{ marginBottom: '1rem', opacity: 0.5 }}><Box size={48} style={{ margin: '0 auto' }} /></div>
                            <h3 style={{ color: 'white' }}>No {view} blueprints found.</h3>
                            <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
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
                                <h3 style={{ color: 'white', fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.75rem' }}>{t.name}</h3>
                                <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>{t.description}</p>

                                <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem', flexWrap: 'wrap' }}>
                                    {(t.tags || []).map((tag, i) => (
                                        <span key={i} style={{ fontSize: '0.7rem', color: '#60a5fa', background: 'rgba(96, 165, 250, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                                            #{tag}
                                        </span>
                                    ))}
                                </div>

                                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: 'auto' }}>
                                    {(t.definition?.nodes || []).slice(0, 4).map((n, i) => (
                                        <span key={i} style={{
                                            fontSize: '0.65rem',
                                            padding: '4px 10px',
                                            background: 'rgba(255, 255, 255, 0.05)',
                                            borderRadius: '6px',
                                            color: '#cbd5e1',
                                            fontWeight: 600,
                                            textTransform: 'uppercase',
                                            border: '1px solid rgba(255,255,255,0.1)'
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
