import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Book, Search, Box, ChevronRight, Info, Layers, Loader2, X, Command } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function NodeReference({ onClose }) {
    const [nodes, setNodes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedNode, setSelectedNode] = useState(null);

    useEffect(() => {
        const fetchDocs = async () => {
            try {
                const res = await axios.get(`${API_BASE_URL}/docs/nodes`);
                setNodes(res.data);
            } catch (err) {
                console.error("Docs fetch error", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDocs();
    }, []);

    const filteredNodes = nodes.filter(n =>
        n.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        n.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        n.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="docs-overlay" onClick={onClose}>
            <div className="docs-modal" onClick={e => e.stopPropagation()}>
                {/* Sidebar */}
                <div className="docs-sidebar">
                    <div className="docs-sidebar-header">
                        <div className="docs-brand">
                            <div className="docs-brand-icon">
                                <Book size={16} color="#60A5FA" />
                            </div>
                            <h3>Component SDK</h3>
                        </div>

                        <div className="docs-search-container">
                            <Search className="docs-search-icon" size={16} />
                            <input
                                className="docs-search-input"
                                placeholder="Search by name, category..."
                                autoFocus
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="docs-sidebar-nav custom-scrollbar">
                        {loading ? (
                            <div className="docs-loading">
                                <Loader2 className="docs-spinner" />
                            </div>
                        ) : filteredNodes.length > 0 ? (
                            filteredNodes.map(n => (
                                <button
                                    key={n.id}
                                    className={`docs-nav-item ${selectedNode?.id === n.id ? 'active' : ''}`}
                                    onClick={() => setSelectedNode(n)}
                                >
                                    <div className="docs-nav-content">
                                        <div className="docs-nav-icon">
                                            <Box size={16} />
                                        </div>
                                        <div className="docs-nav-text">
                                            <div className="docs-nav-name">{n.name}</div>
                                            <div className="docs-nav-category-row">
                                                <div className="docs-nav-dot"></div>
                                                <span className="docs-nav-category">{n.category}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <ChevronRight size={14} className="docs-nav-arrow" />
                                </button>
                            ))
                        ) : (
                            <div className="docs-empty-state">
                                <p>No components found.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="docs-main">
                    <header className="docs-header">
                        <div className="docs-header-title">
                            <Command size={18} color="#9CA3AF" />
                            <span>Documentation</span>
                        </div>
                        <button className="docs-close-btn" onClick={onClose}>
                            <X size={20} />
                        </button>
                    </header>

                    <div className="docs-content custom-scrollbar">
                        {!selectedNode ? (
                            <div className="docs-placeholder">
                                <div className="docs-placeholder-icon">
                                    <Layers size={48} color="#60A5FA" />
                                </div>
                                <h2>Select a Component</h2>
                                <p>Browse the library to explore schemas and properties.</p>
                            </div>
                        ) : (
                            <div className="docs-detail">
                                {/* Header Info */}
                                <div className="docs-detail-header">
                                    <div className="docs-tags">
                                        <span className="docs-tag-category">
                                            {selectedNode.category}
                                        </span>
                                        <span className="docs-tag-version">v{selectedNode.version}</span>
                                    </div>
                                    <h1>{selectedNode.name}</h1>
                                    <p className="docs-description">{selectedNode.description}</p>
                                </div>

                                {/* Schemas Row */}
                                <div className="docs-schemas">
                                    {/* Input Schema Column */}
                                    <div className="docs-schema-col">
                                        <div className="docs-schema-header input-theme">
                                            <div className="docs-schema-icon">
                                                <Layers size={18} color="#818CF8" />
                                            </div>
                                            <h3>Input Schema</h3>
                                        </div>
                                        <div className="docs-schema-list">
                                            {Object.entries(selectedNode.inputs || {}).length > 0 ? (
                                                Object.entries(selectedNode.inputs).map(([key, val]) => (
                                                    <div key={key} className="docs-schema-card">
                                                        <div className="docs-schema-card-header">
                                                            <span className="docs-schema-key input-theme-text">{key}</span>
                                                            <span className="docs-schema-type input-theme-badge">{val.type}</span>
                                                        </div>
                                                        <p className="docs-schema-desc">{val.description || 'Configurable execution parameter.'}</p>
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="docs-schema-card dashed">
                                                    <Info size={16} color="#6B7280" />
                                                    <span>No static inputs required.</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Output Schema Column */}
                                    <div className="docs-schema-col">
                                        <div className="docs-schema-header output-theme">
                                            <div className="docs-schema-icon">
                                                <Box size={18} color="#34D399" />
                                            </div>
                                            <h3>Output Schema</h3>
                                        </div>
                                        <div className="docs-schema-list">
                                            {Object.entries(selectedNode.outputs || {}).length > 0 ? (
                                                Object.entries(selectedNode.outputs).map(([key, val]) => (
                                                    <div key={key} className="docs-schema-card">
                                                        <div className="docs-schema-card-header">
                                                            <span className="docs-schema-key output-theme-text">{key}</span>
                                                            <span className="docs-schema-type output-theme-badge">{val.type}</span>
                                                        </div>
                                                    </div>
                                                ))
                                            ) : (
                                                <div className="docs-schema-card dashed">
                                                    <Info size={16} color="#6B7280" />
                                                    <span>No distinct outputs recorded.</span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Footer / Technical ID */}
                                <div className="docs-footer">
                                    <div className="docs-technical-id">
                                        <span className="docs-technical-label">Technical Identifier</span>
                                        <div className="docs-technical-value">
                                            {selectedNode.id}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <style jsx="true">{`
                .docs-overlay {
                    position: fixed; inset: 0; z-index: 9999;
                    background: rgba(0, 0, 0, 0.75);
                    backdrop-filter: blur(16px);
                    display: flex; align-items: center; justify-content: center;
                    padding: 24px; font-family: 'Inter', system-ui, sans-serif;
                    animation: docsFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                }
                .docs-modal {
                    width: 100%; max-width: 1200px; height: 85vh;
                    background: #0A0D14; border-radius: 24px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    box-shadow: 0 40px 80px -20px rgba(0, 0, 0, 0.8), inset 0 0 0 1px rgba(255,255,255,0.05);
                    display: flex; overflow: hidden;
                }
                .docs-sidebar {
                    width: 320px; background: rgba(255, 255, 255, 0.01);
                    border-right: 1px solid rgba(255, 255, 255, 0.08);
                    display: flex; flex-direction: column; flex-shrink: 0;
                }
                .docs-sidebar-header {
                    padding: 24px; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                }
                .docs-brand {
                    display: flex; align-items: center; gap: 12px; margin-bottom: 24px;
                }
                .docs-brand-icon {
                    width: 36px; height: 36px; border-radius: 10px;
                    background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2);
                    display: flex; align-items: center; justify-content: center;
                }
                .docs-brand h3 {
                    margin: 0; font-size: 16px; font-weight: 600; color: #fff; letter-spacing: -0.02em;
                }
                .docs-search-container { position: relative; }
                .docs-search-icon {
                    position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #6B7280;
                }
                .docs-search-input {
                    width: 100%; padding: 10px 16px 10px 40px; box-sizing: border-box;
                    background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px; color: #E5E7EB; font-size: 14px;
                    transition: border-color 0.2s, background 0.2s;
                    outline: none; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                }
                .docs-search-input:focus {
                    border-color: rgba(59, 130, 246, 0.5); background: rgba(0, 0, 0, 0.6);
                }
                .docs-sidebar-nav {
                    flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 4px;
                }
                .docs-loading { display: flex; justify-content: center; height: 160px; align-items: center; }
                .docs-spinner { color: rgba(59, 130, 246, 0.5); animation: spin 1s linear infinite; }
                @keyframes spin { 100% { transform: rotate(360deg); } }
                
                .docs-nav-item {
                    width: 100%; text-align: left; padding: 12px; border-radius: 12px;
                    background: transparent; border: 1px solid transparent; cursor: pointer;
                    display: flex; align-items: center; justify-content: space-between;
                    transition: all 0.2s;
                }
                .docs-nav-item:hover {
                    background: rgba(255, 255, 255, 0.03); border-color: rgba(255, 255, 255, 0.05);
                }
                .docs-nav-item.active {
                    background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.2);
                    box-shadow: 0 0 20px rgba(59, 130, 246, 0.1);
                }
                .docs-nav-content { display: flex; align-items: center; gap: 12px; overflow: hidden; }
                .docs-nav-icon {
                    padding: 8px; border-radius: 8px; background: rgba(255, 255, 255, 0.05); color: #9CA3AF; transition: all 0.2s;
                }
                .docs-nav-item:hover .docs-nav-icon { color: #E5E7EB; }
                .docs-nav-item.active .docs-nav-icon { background: rgba(59, 130, 246, 0.2); color: #60A5FA; }
                
                .docs-nav-name {
                    font-size: 14px; font-weight: 500; color: #D1D5DB; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                }
                .docs-nav-item:hover .docs-nav-name { color: #fff; }
                .docs-nav-item.active .docs-nav-name { color: #DBEAFE; font-weight: 600; }
                
                .docs-nav-category-row { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
                .docs-nav-dot { width: 6px; height: 6px; border-radius: 50%; background: #4B5563; }
                .docs-nav-item.active .docs-nav-dot { background: #3B82F6; }
                .docs-nav-category { font-size: 10px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
                .docs-nav-arrow { color: #4B5563; opacity: 0; transition: opacity 0.2s, color 0.2s; }
                .docs-nav-item:hover .docs-nav-arrow { opacity: 1; }
                .docs-nav-item.active .docs-nav-arrow { opacity: 1; color: #60A5FA; }
                
                .docs-empty-state { text-align: center; padding: 40px; font-size: 12px; color: #6B7280; }
                
                .docs-main {
                    flex: 1; display: flex; flex-direction: column; position: relative;
                    background: radial-gradient(circle at top right, rgba(30, 58, 138, 0.1), #0A0D14 60%, #000);
                }
                .docs-header {
                    display: flex; align-items: center; justify-content: space-between;
                    padding: 20px 32px; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                    background: rgba(0, 0, 0, 0.2); backdrop-filter: blur(8px);
                }
                .docs-header-title { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; color: #9CA3AF; }
                .docs-close-btn {
                    padding: 8px; background: rgba(255, 255, 255, 0.05); border: none; border-radius: 50%;
                    color: #9CA3AF; cursor: pointer; transition: background 0.2s, color 0.2s;
                }
                .docs-close-btn:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
                
                .docs-content { flex: 1; overflow-y: auto; padding: 48px; position: relative; }
                
                .docs-placeholder {
                    position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; opacity: 0.5;
                }
                .docs-placeholder-icon {
                    width: 96px; height: 96px; border-radius: 50%; background: rgba(59, 130, 246, 0.1);
                    display: flex; align-items: center; justify-content: center; margin-bottom: 24px;
                }
                .docs-placeholder h2 { margin: 0; font-size: 24px; font-weight: 600; color: #fff; letter-spacing: -0.02em; }
                .docs-placeholder p { margin: 8px 0 0; font-size: 14px; color: #9CA3AF; }
                
                .docs-detail {
                    max-width: 900px; margin: 0 auto; animation: docsSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                }
                @keyframes docsSlideUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                @keyframes docsFadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                .docs-detail-header { margin-bottom: 48px; }
                .docs-tags { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
                .docs-tag-category {
                    padding: 4px 12px; background: linear-gradient(90deg, rgba(59, 130, 246, 0.2), rgba(168, 85, 247, 0.2));
                    border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 9999px; font-size: 10px; font-weight: 700; color: #93C5FD; text-transform: uppercase; letter-spacing: 0.1em;
                }
                .docs-tag-version {
                    font-family: monospace; font-size: 12px; color: #6B7280; background: rgba(255, 255, 255, 0.05); padding: 2px 8px; border-radius: 4px;
                }
                .docs-detail-header h1 {
                    margin: 0 0 16px; font-size: 48px; font-weight: 900; letter-spacing: -0.03em;
                    background: linear-gradient(180deg, #FFFFFF, #9CA3AF); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                }
                .docs-description {
                    margin: 0; font-size: 18px; color: #9CA3AF; line-height: 1.6; max-width: 800px; font-weight: 400;
                }
                
                .docs-schemas { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
                @media (max-width: 1000px) { .docs-schemas { grid-template-columns: 1fr; } }
                
                .docs-schema-col { display: flex; flex-direction: column; gap: 24px; }
                .docs-schema-header { 
                    display: flex; align-items: center; gap: 16px; padding-bottom: 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); 
                }
                .docs-schema-icon {
                    width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
                }
                .docs-schema-header.input-theme .docs-schema-icon { background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.2); }
                .docs-schema-header.output-theme .docs-schema-icon { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); }
                .docs-schema-header h3 { margin: 0; font-size: 16px; font-weight: 600; color: #E5E7EB; }
                
                .docs-schema-list { display: flex; flex-direction: column; gap: 16px; }
                .docs-schema-card {
                    padding: 20px; border-radius: 16px;
                    background: linear-gradient(135deg, rgba(255, 255, 255, 0.03), transparent);
                    border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.2s;
                }
                .docs-schema-card:hover { border-color: rgba(255, 255, 255, 0.15); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); }
                .docs-schema-card.dashed { border-style: dashed; display: flex; align-items: center; gap: 12px; font-style: italic; color: #6B7280; font-size: 14px; background: transparent; }
                
                .docs-schema-card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; }
                .docs-schema-key { font-family: monospace; font-size: 14px; font-weight: 700; transition: color 0.2s; }
                .input-theme-text { color: #A5B4FC; }
                .output-theme-text { color: #6EE7B7; }
                
                .docs-schema-type {
                    font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
                    padding: 4px 10px; border-radius: 6px;
                }
                .input-theme-badge { background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.2); color: #A5B4FC; }
                .output-theme-badge { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); color: #6EE7B7; }
                
                .docs-schema-desc { margin: 0; font-size: 14px; color: #9CA3AF; line-height: 1.5; font-weight: 500;}
                
                .docs-footer { margin-top: 48px; margin-bottom: 48px; padding-top: 32px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
                .docs-technical-id { display: inline-flex; flex-direction: column; gap: 8px; }
                .docs-technical-label { font-size: 10px; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.1em; padding-left: 4px; }
                .docs-technical-value {
                    padding: 12px 16px; background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px; font-family: monospace; font-size: 12px; color: #D1D5DB; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
                }
                
                .custom-scrollbar::-webkit-scrollbar { width: 8px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
            `}</style>
        </div>
    );
}
