import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Terminal as TerminalIcon, RefreshCw, XCircle, CheckCircle, Info } from 'lucide-react';

import { API_BASE_URL } from '../config';

export default function LogViewer({ isOpen, onClose }) {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchLogs();
            const interval = setInterval(fetchLogs, 3000);
            return () => clearInterval(interval);
        }
    }, [isOpen]);

    const fetchLogs = async () => {
        try {
            const resp = await axios.get(`${API_BASE_URL}/logs?limit=100`);
            setLogs(resp.data);
        } catch (e) {
            console.error("Failed to fetch logs", e);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="log-panel">
            <header className="log-header">
                <div className="flex items-center gap-2">
                    <TerminalIcon size={14} className="accent-text" />
                    <span className="text-xs font-bold uppercase tracking-wider">System Audit Logs</span>
                </div>
                <div className="flex items-center gap-3">
                    <button className="log-action" onClick={fetchLogs}>
                        <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
                    </button>
                    <button className="log-action" onClick={onClose}><XCircle size={12} /></button>
                </div>
            </header>

            <div className="log-content">
                {logs.length === 0 ? (
                    <div className="empty-logs">No activity recorded yet.</div>
                ) : (
                    logs.map((log, i) => (
                        <div key={i} className="log-entry">
                            <span className="log-time">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                            <span className={`log-badge ${log.action.includes('success') ? 'success' : log.action.includes('fail') ? 'error' : 'info'}`}>
                                {log.action}
                            </span>
                            <span className="log-user">{log.user_id || 'System'}:</span>
                            <span className="log-msg">{JSON.stringify(log.details)}</span>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
