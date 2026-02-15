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
    const [executions, setExecutions] = useState([]);
    const [selectedExecution, setSelectedExecution] = useState(null);
    const [nodeHistory, setNodeHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('overview'); // overview, logs, executions, workers
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
                            className={`nav-item ${activeTab === 'executions' ? 'active' : ''}`}
                            onClick={() => setActiveTab('executions')}
                        >
                            <History size={16} />
                            <span>Executions</span>
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

                        {activeTab === 'executions' && (
                            <div className="executions-view">
                                {!selectedExecution ? (
                                    <div className="executions-list">
                                        <div className="table-header">
                                            <div className="col-time">Time</div>
                                            <div className="col-id">Execution ID</div>
                                            <div className="col-status">Status</div>
                                            <div className="col-action">Action</div>
                                        </div>
                                        <div className="table-body">
                                            {logs.filter(l => l.action.startsWith('workflow_')).map((exec, i) => (
                                                <div key={i} className="table-row clickable" onClick={async () => {
                                                    setSelectedExecution(exec);
                                                    const res = await axios.get(`${API_BASE_URL}/execution/${exec.details.execution_id}/nodes`);
                                                    setNodeHistory(res.data);
                                                }}>
                                                    <div className="col-time">{new Date(exec.timestamp).toLocaleString()}</div>
                                                    <div className="col-id text-xs font-mono">{exec.details.execution_id}</div>
                                                    <div className="col-status">
                                                        <span className={`log-tag ${exec.action === 'workflow_success' ? 'green' : 'red'}`}>
                                                            {exec.action.replace('workflow_', '')}
                                                        </span>
                                                    </div>
                                                    <div className="col-action"><ChevronRight size={14} /></div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="execution-detail">
                                        <button className="back-btn mb-4 flex items-center gap-2 text-xs text-secondary hover:text-white" onClick={() => setSelectedExecution(null)}>
                                            <ChevronRight size={14} className="rotate-180" /> Back to Executions
                                        </button>

                                        <div className="detail-header mb-6">
                                            <h3>Execution History: {selectedExecution.details.execution_id}</h3>
                                        </div>

                                        <div className="node-history-timeline">
                                            {nodeHistory.map((node, i) => (
                                                <details key={i} className="node-history-item mb-4 bg-white/5 rounded-lg border border-white/10 overflow-hidden">
                                                    <summary className="p-4 cursor-pointer hover:bg-white/10 flex items-center justify-between">
                                                        <div className="flex items-center gap-3">
                                                            <div className={`status-dot ${node.status === 'success' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                                                            <span className="font-bold">{node.node_id}</span>
                                                            <span className="text-xs text-secondary">({node.node_type})</span>
                                                        </div>
                                                        <span className="text-xs font-mono text-secondary">{node.execution_time.toFixed(3)}s</span>
                                                    </summary>
                                                    <div className="node-details-content p-4 border-t border-white/10 space-y-4">
                                                        <div className="grid grid-cols-2 gap-4">
                                                            <div>
                                                                <h4 className="text-xs font-bold uppercase text-tertiary mb-2">Input</h4>
                                                                <pre className="text-xs bg-black/50 p-2 rounded max-h-40 overflow-auto">{JSON.stringify(node.input, null, 2)}</pre>
                                                            </div>
                                                            <div>
                                                                <h4 className="text-xs font-bold uppercase text-tertiary mb-2">Output</h4>
                                                                <pre className="text-xs bg-black/50 p-2 rounded max-h-40 overflow-auto">{JSON.stringify(node.output, null, 2)}</pre>
                                                            </div>
                                                        </div>
                                                        {node.logs && node.logs.length > 0 && (
                                                            <div>
                                                                <h4 className="text-xs font-bold uppercase text-tertiary mb-2">Internal Logs</h4>
                                                                <div className="text-xs font-mono bg-black/30 p-2 rounded space-y-1">
                                                                    {node.logs.map((l, j) => <div key={j} className="text-blue-300">{l}</div>)}
                                                                </div>
                                                            </div>
                                                        )}
                                                        {node.stack_trace && (
                                                            <div className="mt-4">
                                                                <h4 className="text-xs font-bold uppercase text-red-400 mb-2">Stack Trace</h4>
                                                                <pre className="text-xs bg-red-900/20 text-red-200 p-2 rounded overflow-auto whitespace-pre-wrap">{node.stack_trace}</pre>
                                                            </div>
                                                        )}
                                                    </div>
                                                </details>
                                            ))}
                                        </div>
                                    </div>
                                )}
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
