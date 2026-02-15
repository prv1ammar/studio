import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Cpu, DollarSign, Loader2, Zap } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function UsageStats({ workspaceId }) {
    const [usage, setUsage] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (workspaceId) {
            fetchUsage();
        }
    }, [workspaceId]);

    const fetchUsage = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('studio_token');
            // We'll add this endpoint to billing API
            const res = await axios.get(`${API_BASE_URL}/billing/usage/${workspaceId}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setUsage(res.data);
        } catch (e) {
            console.error("Failed to fetch usage stats", e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center p-20">
            <Loader2 className="animate-spin text-blue-500" size={32} />
        </div>
    );

    if (!usage) return <div className="p-10 text-center opacity-50">No usage data found for this month.</div>;

    const taskPercentage = Math.min(100, (usage.tasks_executed / usage.task_limit) * 100);
    const tokenPercentage = Math.min(100, (usage.ai_tokens_used / usage.token_limit) * 100);

    return (
        <div className="p-6 space-y-8 overflow-y-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-black text-white flex items-center gap-2">
                        <Zap size={20} className="text-yellow-400" />
                        Usage Quota
                    </h2>
                    <p className="text-xs text-gray-500 mt-1">Real-time resource tracking for current billing period ({usage.month})</p>
                </div>
                <div className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full">
                    <span className="text-[10px] font-bold text-blue-400 uppercase tracking-widest">{usage.tier} Plan</span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Tasks Progress */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                                <Activity size={20} />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-white">Workflow Tasks</h3>
                                <p className="text-[10px] text-gray-400">Node executions</p>
                            </div>
                        </div>
                        <span className="text-xs font-mono text-gray-300">
                            {usage.tasks_executed.toLocaleString()} / {usage.task_limit === -1 ? '∞' : usage.task_limit.toLocaleString()}
                        </span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-1000 ${taskPercentage > 90 ? 'bg-red-500' : 'bg-indigo-500'}`}
                            style={{ width: `${taskPercentage}%` }}
                        />
                    </div>
                </div>

                {/* Tokens Progress */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400">
                                <Cpu size={20} />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-white">AI Tokens</h3>
                                <p className="text-[10px] text-gray-400">Neural computation</p>
                            </div>
                        </div>
                        <span className="text-xs font-mono text-gray-300">
                            {usage.ai_tokens_used.toLocaleString()} / {usage.token_limit === -1 ? '∞' : usage.token_limit.toLocaleString()}
                        </span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-1000 ${tokenPercentage > 90 ? 'bg-red-500' : 'bg-purple-500'}`}
                            style={{ width: `${tokenPercentage}%` }}
                        />
                    </div>
                </div>
            </div>

            <div className="bg-gradient-to-br from-white/5 to-transparent border border-white/10 rounded-xl p-6">
                <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center text-green-400">
                        <DollarSign size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white">Estimated Accrued Cost</h3>
                        <p className="text-xs text-gray-500 italic">Self-managed API costs (approximate)</p>
                    </div>
                </div>
                <div className="text-4xl font-black text-white">
                    ${usage.estimated_cost?.toFixed(4)}
                </div>
            </div>
        </div>
    );
}
