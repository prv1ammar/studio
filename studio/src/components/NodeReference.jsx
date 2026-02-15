import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Book, Search, Box, ChevronRight, Info, Layers, Loader2, X } from 'lucide-react';
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
        <div className="dashboard-overlay" onClick={onClose}>
            <div className="dashboard-modal docs-modal" onClick={e => e.stopPropagation()} style={{ width: '90vw', height: '85vh', maxWidth: '1200px' }}>
                <aside className="dashboard-sidebar" style={{ width: '300px' }}>
                    <div className="sidebar-header">
                        <Book size={20} className="text-blue-400" />
                        <h3>Node Library</h3>
                    </div>

                    <div className="px-4 mb-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={14} />
                            <input
                                className="search-prime-input w-full pl-9 py-2 text-xs"
                                placeholder="Filter components..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="sidebar-nav overflow-y-auto" style={{ flex: 1 }}>
                        {loading ? (
                            <div className="flex items-center justify-center h-full"><Loader2 className="animate-spin" /></div>
                        ) : filteredNodes.map(n => (
                            <button
                                key={n.id}
                                className={`flex items-center justify-between group ${selectedNode?.id === n.id ? 'active' : ''}`}
                                onClick={() => setSelectedNode(n)}
                            >
                                <div className="flex items-center gap-3">
                                    <Box size={14} className="opacity-40 group-hover:opacity-100" />
                                    <div className="text-left">
                                        <div className="font-bold">{n.name}</div>
                                        <div className="text-[9px] opacity-40 uppercase tracking-tighter">{n.category}</div>
                                    </div>
                                </div>
                                <ChevronRight size={14} className="opacity-0 group-hover:opacity-40" />
                            </button>
                        ))}
                    </div>
                </aside>

                <main className="dashboard-main bg-[#0b0c0e]">
                    <header className="dashboard-header border-b border-white/5">
                        <div className="header-info">
                            <h2>Component Reference</h2>
                            <p>Deep-dive into the technical specifications of every building block.</p>
                        </div>
                        <button className="close-btn" onClick={onClose}><X size={24} /></button>
                    </header>

                    <div className="dashboard-content p-8 overflow-y-auto">
                        {!selectedNode ? (
                            <div className="flex flex-col items-center justify-center h-full opacity-20">
                                <Info size={64} className="mb-4" />
                                <h3>Select a component to view details</h3>
                            </div>
                        ) : (
                            <div className="space-y-8 max-w-3xl">
                                <div className="space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-[10px] font-bold text-blue-400 uppercase tracking-widest">
                                            {selectedNode.category}
                                        </div>
                                        <div className="text-xs text-gray-500">Version {selectedNode.version}</div>
                                    </div>
                                    <h1 className="text-4xl font-black text-white">{selectedNode.name}</h1>
                                    <p className="text-lg text-gray-400 leading-relaxed font-medium">
                                        {selectedNode.description}
                                    </p>
                                </div>

                                <div className="grid grid-cols-2 gap-8">
                                    <div className="space-y-4">
                                        <h4 className="flex items-center gap-2 text-white font-bold border-b border-white/5 pb-2">
                                            <Layers size={16} className="text-green-400" />
                                            Input Schema
                                        </h4>
                                        <div className="space-y-3">
                                            {Object.entries(selectedNode.inputs || {}).map(([key, val]) => (
                                                <div key={key} className="p-3 bg-white/5 rounded-lg border border-white/5">
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="font-mono text-xs text-indigo-400 font-bold">{key}</span>
                                                        <span className="text-[9px] px-1.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded uppercase">{val.type}</span>
                                                    </div>
                                                    <p className="text-[10px] text-gray-400">{val.description || 'Configurable parameter.'}</p>
                                                </div>
                                            ))}
                                            {Object.keys(selectedNode.inputs || {}).length === 0 && <div className="text-xs text-gray-500 italic">No static inputs required.</div>}
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <h4 className="flex items-center gap-2 text-white font-bold border-b border-white/5 pb-2">
                                            <Box size={16} className="text-orange-400" />
                                            Output Schema
                                        </h4>
                                        <div className="space-y-3">
                                            {Object.entries(selectedNode.outputs || {}).map(([key, val]) => (
                                                <div key={key} className="p-3 bg-white/5 rounded-lg border border-white/5">
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="font-mono text-xs text-orange-400 font-bold">{key}</span>
                                                        <span className="text-[9px] px-1.5 py-0.5 bg-orange-500/20 text-orange-300 rounded uppercase">{val.type}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-blue-500/5 border border-blue-500/10 rounded-2xl p-6">
                                    <h5 className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-2">Technical ID</h5>
                                    <code className="text-xs text-gray-500">{selectedNode.id}</code>
                                </div>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}
