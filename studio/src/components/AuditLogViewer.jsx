import React, { useState, useEffect } from 'react';
import { Activity, Search, Filter, Clock, User, Shield, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export default function AuditLogViewer({ workspaceId }) {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState('');

    useEffect(() => {
        if (workspaceId) {
            fetchLogs();
        }
    }, [workspaceId]);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('studio_token');
            const res = await axios.get(`${API_BASE_URL}/audit/list/${workspaceId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setLogs(res.data);
        } catch (e) {
            console.error("Failed to fetch audit logs", e);
        } finally {
            setLoading(false);
        }
    };

    const filteredLogs = logs.filter(log =>
        log.action.toLowerCase().includes(filter.toLowerCase()) ||
        log.user_id?.toLowerCase().includes(filter.toLowerCase())
    );

    const getActionIcon = (action) => {
        if (action.includes('delete')) return <AlertCircle size={14} className="text-red-400" />;
        if (action.includes('create')) return <Activity size={14} className="text-green-400" />;
        if (action.includes('invite')) return <User size={14} className="text-blue-400" />;
        return <Shield size={14} className="text-gray-400" />;
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    return (
        <div className="audit-viewer">
            <div className="audit-header">
                <div className="audit-title">
                    <Shield size={18} className="text-purple-400" />
                    <h3>Governance Audit Log</h3>
                </div>
                <div className="audit-filters">
                    <div className="search-box">
                        <Search size={14} />
                        <input
                            placeholder="Filter by action or user..."
                            value={filter}
                            onChange={e => setFilter(e.target.value)}
                        />
                    </div>
                    <button className="refresh-btn" onClick={fetchLogs} disabled={loading}>
                        <Clock size={14} /> Refresh
                    </button>
                </div>
            </div>

            <div className="audit-table-container">
                {loading ? (
                    <div className="loading-state">Loading audit records...</div>
                ) : (
                    <table className="audit-table">
                        <thead>
                            <tr>
                                <th>Action</th>
                                <th>User ID</th>
                                <th>Details</th>
                                <th>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredLogs.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="empty-state">No audit records found</td>
                                </tr>
                            ) : (
                                filteredLogs.map((log) => (
                                    <tr key={log.id}>
                                        <td className="action-cell">
                                            <div className="action-badge">
                                                {getActionIcon(log.action)}
                                                <span>{log.action}</span>
                                            </div>
                                        </td>
                                        <td className="user-cell" title={log.user_id}>
                                            {log.user_id?.split('-')[0]}...
                                        </td>
                                        <td className="details-cell">
                                            <pre>{JSON.stringify(log.details, null, 2)}</pre>
                                        </td>
                                        <td className="time-cell">{formatDate(log.timestamp)}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                )}
            </div>

            <style>{`
                .audit-viewer {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    gap: 1rem;
                    color: #e2e8f0;
                }
                .audit-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding-bottom: 1rem;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }
                .audit-title {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .audit-title h3 {
                    font-size: 1rem;
                    font-weight: 600;
                    margin: 0;
                }
                .audit-filters {
                    display: flex;
                    gap: 0.5rem;
                }
                .search-box {
                    display: flex;
                    align-items: center;
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 6px;
                    padding: 0.25rem 0.5rem;
                    gap: 0.5rem;
                }
                .search-box input {
                    background: transparent;
                    border: none;
                    color: white;
                    font-size: 0.8rem;
                    outline: none;
                    width: 200px;
                }
                .refresh-btn {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.1);
                    color: #94a3b8;
                    padding: 0.25rem 0.75rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.8rem;
                    transition: all 0.2s;
                }
                .refresh-btn:hover {
                    background: rgba(255,255,255,0.1);
                    color: white;
                }
                .audit-table-container {
                    flex: 1;
                    overflow: auto;
                    background: rgba(0,0,0,0.2);
                    border-radius: 8px;
                    border: 1px solid rgba(255,255,255,0.05);
                }
                .audit-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.85rem;
                }
                .audit-table th {
                    text-align: left;
                    padding: 0.75rem 1rem;
                    background: rgba(255,255,255,0.03);
                    color: #94a3b8;
                    font-weight: 500;
                    position: sticky;
                    top: 0;
                }
                .audit-table td {
                    padding: 0.75rem 1rem;
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                    vertical-align: top;
                }
                .action-badge {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    font-weight: 500;
                }
                .user-cell {
                    font-family: monospace;
                    color: #94a3b8;
                }
                .details-cell pre {
                    margin: 0;
                    white-space: pre-wrap;
                    color: #cbd5e1;
                    font-size: 0.75rem;
                    background: rgba(0,0,0,0.2);
                    padding: 0.5rem;
                    border-radius: 4px;
                }
                .time-cell {
                    color: #64748b;
                    font-size: 0.75rem;
                    white-space: nowrap;
                }
                .loading-state, .empty-state {
                    padding: 2rem;
                    text-align: center;
                    color: #64748b;
                }
            `}</style>
        </div>
    );
}
