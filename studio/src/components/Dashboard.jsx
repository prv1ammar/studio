import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Activity, Shield, Zap, Terminal, RefreshCw, XCircle,
    CheckCircle, AlertCircle, Cpu, HardDrive, Cpu as WorkerIcon,
    Search, Filter, ChevronRight, Clock, User
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function Dashboard({ isOpen, onClose }) {
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('overview'); // overview, logs, workers
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        if (isOpen) {
            refreshData();
            const interval = setInterval(refreshData, 5000);
            return () => clearInterval(interval);
        }
    }, [isOpen]);

    const refreshData = async () => {
        setLoading(true);
        try {
            const [logsResp, statsResp] = await Promise.all([
                axios.get(`${API_BASE_URL}/logs?limit=50`),
                axios.get(`${API_BASE_URL}/stats`)
            ]);
            setLogs(logsResp.data);
            setStats(statsResp.data);
        } catch (e) {
            console.error("Dashboard Sync Error", e);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    const filteredLogs = logs.filter(log =>
        log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (log.user_id && log.user_id.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="dashboard-overlay" onClick={onClose}>
            <div className="dashboard-modal" onClick={e => e.stopPropagation()}>
                <aside className="dashboard-sidebar">
                    <div className="dashboard-brand">
                        <div className="brand-icon">
                            <Shield size={18} />
                        </div>
                        <div className="brand-text">
                            <span className="brand-title">Studio Monitor</span>
                            <span className="brand-status">v3.0.0 Global</span>
                        </div>
                    </div>

                    <nav className="dashboard-nav">
                        <button
                            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
                            onClick={() => setActiveTab('overview')}
                        >
                            <Activity size={16} />
                            <span>Overview</span>
                        </button>
                        <button
                            className={`nav-item ${activeTab === 'logs' ? 'active' : ''}`}
                            onClick={() => setActiveTab('logs')}
                        >
                            <Terminal size={16} />
                            <span>Audit Logs</span>
                        </button>
                        <button
                            className={`nav-item ${activeTab === 'workers' ? 'active' : ''}`}
                            onClick={() => setActiveTab('workers')}
                        >
                            <Zap size={16} />
                            <span>Workers</span>
                        </button>
                    </nav>

                    <div className="dashboard-sidebar-footer">
                        <div className="health-badge">
                            <div className="health-dot pulse shadow-glow-green"></div>
                            <span>System Operational</span>
                        </div>
                    </div>
                </aside>

                <main className="dashboard-main">
                    <header className="dashboard-header">
                        <div className="header-left">
                            <h2>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</h2>
                            <p className="text-secondary text-xs">Real-time telemetry and audit trail</p>
                        </div>
                        <div className="header-actions">
                            <button className="dashboard-action-btn" onClick={refreshData} disabled={loading}>
                                <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
                                <span>Sync</span>
                            </button>
                            <button className="dashboard-close-btn" onClick={onClose}>
                                <XCircle size={20} />
                            </button>
                        </div>
                    </header>

                    <div className="dashboard-scrollable">
                        {activeTab === 'overview' && (
                            <div className="overview-grid">
                                <div className="stats-row">
                                    <StatCard
                                        title="Total Nodes"
                                        value={stats?.total_nodes || '0'}
                                        subtitle="Registered in Factory"
                                        icon={<Cpu size={20} />}
                                        color="blue"
                                    />
                                    <StatCard
                                        title="Uptime"
                                        value={stats?.uptime?.split(' ')[0] || '99.9%'}
                                        subtitle="PostgreSQL Connection"
                                        icon={<Activity size={20} />}
                                        color="green"
                                    />
                                    <StatCard
                                        title="Failures"
                                        value={stats?.failed_workflows || '0'}
                                        subtitle="Blocked Executions"
                                        icon={<AlertCircle size={20} />}
                                        color="red"
                                    />
                                    <StatCard
                                        title="Workers"
                                        value={stats?.worker_status === 'connected' ? '1' : '0'}
                                        subtitle="Active Arq Pool"
                                        icon={<WorkerIcon size={20} />}
                                        color="purple"
                                    />
                                </div>

                                <div className="recent-activity-section">
                                    <div className="section-header">
                                        <h3>Critical Audit Trail</h3>
                                        <button className="view-all-btn" onClick={() => setActiveTab('logs')}>
                                            View Logs <ChevronRight size={14} />
                                        </button>
                                    </div>
                                    <div className="mini-log-list">
                                        {logs.slice(0, 8).map((log, i) => (
                                            <div key={i} className="mini-log-item">
                                                <div className={`log-indicator ${getLogColor(log.action)}`}></div>
                                                <div className="log-info">
                                                    <span className="log-action-text">{log.action.replace('_', ' ')}</span>
                                                    <span className="log-meta">
                                                        {log.user_id ? log.user_id.split('-')[0] : 'System'} • {new Date(log.timestamp).toLocaleTimeString()}
                                                    </span>
                                                </div>
                                                <div className="log-details-preview">
                                                    {JSON.stringify(log.details).slice(0, 40)}...
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="health-grid">
                                    <HealthBar label="Database Latency" value={15} max={100} unit="ms" />
                                    <HealthBar label="Redis Queue Depth" value={0} max={50} unit="jobs" />
                                    <HealthBar label="Auth Token Load" value={8} max={100} unit="req/s" />
                                </div>
                            </div>
                        )}

                        {activeTab === 'logs' && (
                            <div className="logs-view">
                                <div className="filter-bar">
                                    <div className="search-box">
                                        <Search size={14} />
                                        <input
                                            type="text"
                                            placeholder="Search actions or users..."
                                            value={searchQuery}
                                            onChange={e => setSearchQuery(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <div className="full-log-table">
                                    <div className="table-header">
                                        <div className="col-time">Timestamp</div>
                                        <div className="col-action">Action</div>
                                        <div className="col-user">User Context</div>
                                        <div className="col-data">Details</div>
                                    </div>
                                    <div className="table-body">
                                        {filteredLogs.map((log, i) => (
                                            <div key={i} className="table-row">
                                                <div className="col-time"><Clock size={12} /> {new Date(log.timestamp).toLocaleString()}</div>
                                                <div className="col-action">
                                                    <span className={`log-tag ${getLogColor(log.action)}`}>{log.action}</span>
                                                </div>
                                                <div className="col-user"><User size={12} /> {log.user_id || 'System'}</div>
                                                <div className="col-data">
                                                    <code title={JSON.stringify(log.details)}>
                                                        {JSON.stringify(log.details).length > 100
                                                            ? JSON.stringify(log.details).slice(0, 100) + '...'
                                                            : JSON.stringify(log.details)}
                                                    </code>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'workers' && (
                            <div className="workers-view">
                                <div className="worker-card active">
                                    <div className="worker-header">
                                        <div className="flex items-center gap-3">
                                            <div className="worker-avatar">
                                                <Zap size={20} />
                                            </div>
                                            <div>
                                                <h4>Studio-Worker-01</h4>
                                                <p className="text-xs text-secondary">arq_pool:default</p>
                                            </div>
                                        </div>
                                        <div className="status-pill online">ONLINE</div>
                                    </div>
                                    <div className="worker-stats">
                                        <div className="w-stat">
                                            <span className="label">Uptime</span>
                                            <span className="value">2h 14m</span>
                                        </div>
                                        <div className="w-stat">
                                            <span className="label">Total Jobs</span>
                                            <span className="value">142</span>
                                        </div>
                                        <div className="w-stat">
                                            <span className="label">Failed</span>
                                            <span className="value">0</span>
                                        </div>
                                    </div>
                                    <div className="worker-footer">
                                        <div className="cpu-metric">
                                            <div className="flex justify-between text-xs mb-1">
                                                <span>Load</span>
                                                <span>4%</span>
                                            </div>
                                            <div className="progress-bg"><div className="progress-fill" style={{ width: '4%' }}></div></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}

function StatCard({ title, value, subtitle, icon, color }) {
    return (
        <div className={`stat-card ${color}`}>
            <div className="stat-header">
                <span className="stat-title">{title}</span>
                <div className="stat-icon">{icon}</div>
            </div>
            <div className="stat-value">{value}</div>
            <div className="stat-subtitle">{subtitle}</div>
        </div>
    );
}

function HealthBar({ label, value, max, unit }) {
    const percent = Math.min((value / max) * 100, 100);
    return (
        <div className="health-bar-container">
            <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-semibold text-secondary">{label}</span>
                <span className="text-xs font-bold">{value}{unit}</span>
            </div>
            <div className="health-bg">
                <div className="health-fill" style={{ width: `${percent}%` }}></div>
            </div>
        </div>
    );
}

function getLogColor(action) {
    if (action.includes('fail') || action.includes('error') || action.includes('delete')) return 'red';
    if (action.includes('success') || action.includes('add') || action.includes('save') || action.includes('login')) return 'green';
    return 'blue';
}
