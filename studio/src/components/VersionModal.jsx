import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { History, Download, X, Clock, FileJson } from 'lucide-react';

import { API_BASE_URL } from '../config';

export default function VersionModal({ isOpen, onClose, onLoadVersion }) {
    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) fetchVersions();
    }, [isOpen]);

    const fetchVersions = async () => {
        setLoading(true);
        try {
            const resp = await axios.get(`${API_BASE_URL}/workflow/versions`);
            setVersions(resp.data);
        } catch (e) {
            console.error("Failed to fetch versions", e);
        } finally {
            setLoading(false);
        }
    };

    const handleLoad = async (versionId) => {
        try {
            const resp = await axios.get(`${API_BASE_URL}/workflow/versions/${versionId}`);
            onLoadVersion(resp.data);
            onClose();
        } catch (e) {
            alert("Failed to load version.");
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-container p-6 w-[500px]">
                <header className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <History className="accent-text" size={20} />
                        <h2 className="text-xl font-bold">Version History</h2>
                    </div>
                    <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-full">
                        <X size={20} />
                    </button>
                </header>

                <div className="version-list space-y-3 max-h-[400px] overflow-y-auto pr-2">
                    {loading ? (
                        <div className="text-center py-8 text-gray-400">Loading history...</div>
                    ) : versions.length === 0 ? (
                        <div className="text-center py-8 text-gray-500 italic">No snapshots saved yet.</div>
                    ) : (
                        versions.map((v, i) => (
                            <div key={i} className="bg-white/5 border border-white/10 p-4 rounded-xl flex items-center justify-between hover:border-white/20 transition-all group">
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center text-blue-400">
                                        <FileJson size={20} />
                                    </div>
                                    <div>
                                        <h3 className="font-medium text-white group-hover:text-blue-400 transition-colors uppercase text-xs tracking-widest">{v.workflow_name}</h3>
                                        <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                                            <Clock size={12} />
                                            {new Date(v.created_at).toLocaleString()}
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleLoad(v.id)}
                                    className="p-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-all"
                                    title="Restore this version"
                                >
                                    <Download size={16} />
                                </button>
                            </div>
                        ))
                    )}
                </div>

                <footer className="mt-8 pt-6 border-t border-white/10 text-xs text-gray-500">
                    Snapshots are immutable JSON records saved on the server.
                </footer>
            </div>
        </div>
    );
}
