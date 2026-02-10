import React, { useEffect, useState } from 'react';
import { MessageSquare, BookOpen, Globe, Layout, X, Zap } from 'lucide-react';
import '../Templates.css';
import { API_BASE_URL } from '../config';

const TemplateGallery = ({ onSelect, onClose }) => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API_BASE_URL}/templates`)
            .then(res => res.json())
            .then(data => {
                setTemplates(data || []);
                setLoading(false);
            })
            .catch(err => {
                console.error("Registry error: Templates unreachable", err);
                setLoading(false);
            });
    }, []);

    const getIcon = (iconName) => {
        const map = { MessageSquare, BookOpen, Globe };
        return map[iconName] || Zap;
    };

    return (
        <div className="template-overlay">
            <div className="template-modal">
                <div className="template-header">
                    <div>
                        <h2 style={{ fontSize: '1.8rem', fontWeight: 900, color: 'white', display: 'flex', alignItems: 'center', gap: '16px' }}>
                            <div className="logo-shield" style={{ width: 44, height: 44 }}>
                                <Layout size={24} color="white" />
                            </div>
                            Blueprint Archive
                        </h2>
                        <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', marginTop: '6px' }}>
                            Initialize your workspace with a pre-optimized neural architecture.
                        </p>
                    </div>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-white)' }}>
                        <X size={32} />
                    </button>
                </div>

                <div className="template-grid">
                    {loading ? (
                        <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '10rem' }}>
                            <div className="animate-spin" style={{ margin: '0 auto 1rem auto', width: 40, height: 40, border: '4px solid var(--accent-blue)', borderRightColor: 'transparent', borderRadius: '50%' }} />
                            <span style={{ color: 'var(--accent-blue)', fontWeight: 700, letterSpacing: '2px' }}>DECRYPTING BLUEPRINTS...</span>
                        </div>
                    ) : (
                        templates.map(t => {
                            const Icon = getIcon(t.icon);
                            return (
                                <div key={t.id} className="template-card" onClick={() => onSelect(t)}>
                                    <div className="use-badge">DEPLOY NOW</div>
                                    <div className="template-icon-box">
                                        <Icon size={28} />
                                    </div>
                                    <h3 style={{ color: 'white', fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.75rem' }}>{t.name}</h3>
                                    <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>{t.description}</p>

                                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                        {(t.nodes || []).slice(0, 4).map((n, i) => (
                                            <span key={i} style={{
                                                fontSize: '0.65rem',
                                                padding: '4px 10px',
                                                background: 'rgba(59, 130, 246, 0.1)',
                                                borderRadius: '6px',
                                                color: 'var(--accent-blue)',
                                                fontWeight: 700,
                                                textTransform: 'uppercase'
                                            }}>
                                                {n.data?.label || 'Unknown'}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
};

export default TemplateGallery;
