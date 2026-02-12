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
            <div className="cred-modal-box">
                <header className="modal-header">
                    <div className="title-row">
                        <History size={18} className="accent-text" />
                        <h2>Workflow Version History</h2>
                    </div>
                    <button className="close-btn" onClick={onClose}><X size={20} /></button>
                </header>

                <div className="modal-content">
                    <p className="modal-subtext">
                        Restore previous versions of your workflow. Snapshots are immutable and saved securely on the server.
                    </p>

                    <div className="version-list">
                        {loading ? (
                            <div className="text-center py-8 text-gray-400">Loading history...</div>
                        ) : versions.length === 0 ? (
                            <div className="text-center py-8 text-gray-500 italic">No snapshots saved yet.</div>
                        ) : (
                            versions.map((v, i) => (
                                <div key={i} className="cred-item group">
                                    <div className="cred-info">
                                        <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center text-blue-400">
                                            <FileJson size={18} />
                                        </div>
                                        <div>
                                            <div className="cred-name">{v.workflow_name}</div>
                                            <div className="flex items-center gap-2 text-[10px] text-gray-500 font-bold uppercase tracking-wider mt-1">
                                                <Clock size={10} />
                                                {new Date(v.created_at).toLocaleString()}
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleLoad(v.id)}
                                        className="p-2 bg-blue-500/10 hover:bg-blue-600 hover:text-white text-blue-400 rounded-lg transition-all"
                                        title="Restore this version"
                                    >
                                        <Download size={16} />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
