import React, { useState } from 'react';
import { X, Copy, Check, Globe, Terminal, Loader2 } from 'lucide-react';

const PublishModal = ({ onClose, publishData }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = (text) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const curlCommand = `curl -X POST ${publishData.url} \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello from my custom agent!"}'`;

    return (
        <div className="template-overlay">
            <div className="template-modal" style={{ maxWidth: '600px', height: 'auto', paddingBottom: '2rem' }}>
                <div className="template-header">
                    <div>
                        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'white', display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <Globe className="text-accent-primary" size={20} /> Workflow Published!
                        </h2>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>Your agent is now live as a production-ready API.</p>
                    </div>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                        <X size={20} />
                    </button>
                </div>

                <div style={{ padding: '2rem' }}>
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
                            API ENDPOINT
                        </label>
                        <div style={{ display: 'flex', gap: '8px', background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                            <code style={{ flex: 1, fontSize: '0.8rem', color: 'var(--accent-primary)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {publishData.url}
                            </code>
                            <button onClick={() => handleCopy(publishData.url)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                                {copied ? <Check size={16} color="#10b981" /> : <Copy size={16} />}
                            </button>
                        </div>
                    </div>

                    <div>
                        <label style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Terminal size={12} /> CURL EXAMPLE
                        </label>

                        <pre style={{
                            background: '#050608',
                            padding: '1.25rem',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            color: '#a0a6b8',
                            overflowX: 'auto',
                            border: '1px solid var(--border-strong)',
                            fontFamily: 'var(--font-mono)',
                            lineHeight: 1.5
                        }}>
                            {curlCommand}
                        </pre>
                    </div>

                    <button
                        onClick={onClose}
                        style={{
                            width: '100%',
                            marginTop: '2rem',
                            background: 'var(--accent-primary)',
                            color: 'black',
                            border: 'none',
                            padding: '12px',
                            borderRadius: '10px',
                            fontWeight: 800,
                            cursor: 'pointer'
                        }}
                    >
                        GOT IT
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PublishModal;
