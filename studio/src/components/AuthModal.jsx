import React, { useState } from 'react';
import axios from 'axios';
import { Mail, Lock, User, X, LogIn, UserPlus, Loader2, Layout } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function AuthModal({ isOpen, onAuthSuccess }) {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [companyName, setCompanyName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const endpoint = isLogin ? '/auth/login' : '/auth/register';
        const payload = isLogin
            ? { email, password }
            : { email, password, full_name: fullName, company_name: companyName };

        try {
            const resp = await axios.post(`${API_BASE_URL}${endpoint}`, payload);
            const { access_token } = resp.data;

            localStorage.setItem('studio_token', access_token);
            localStorage.setItem('user_email', email);
            axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

            onAuthSuccess();
        } catch (err) {
            setError(err.response?.data?.detail || "Authentication failed. Please check your credentials.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-container p-0 overflow-hidden w-[420px] bg-[#0d1117] border border-white/10 rounded-2xl shadow-2xl relative">
                <div className="h-1 bg-gradient-to-r from-blue-600 via-indigo-500 to-blue-600 w-full" />

                <div className="p-8">
                    <header className="text-center mb-10">
                        <div className="mx-auto mb-6 flex justify-center transform hover:scale-105 transition-transform duration-300">
                            <img src="/logo.png" alt="Logo" className="h-16 object-contain" />
                        </div>
                        <h2 className="text-2xl font-bold text-white tracking-tight">{isLogin ? 'Welcome Back' : 'Get Started'}</h2>
                        <p className="text-gray-400 text-sm mt-3 leading-relaxed">
                            {isLogin
                                ? 'Sign in to access your enterprise automation workspace'
                                : 'Create your account to start building AI-powered workflows'}
                        </p>
                    </header>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {!isLogin && (
                            <div className="grid grid-cols-2 gap-4">
                                <div className="relative">
                                    <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                                    <input
                                        type="text"
                                        placeholder="Full Name"
                                        className="ins-input pl-11 w-full bg-white/5 border-white/10 focus:border-blue-500"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        required={!isLogin}
                                    />
                                </div>
                                <div className="relative">
                                    <Layout className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                                    <input
                                        type="text"
                                        placeholder="Company"
                                        className="ins-input pl-11 w-full bg-white/5 border-white/10 focus:border-blue-500"
                                        value={companyName}
                                        onChange={(e) => setCompanyName(e.target.value)}
                                        required={!isLogin}
                                    />
                                </div>
                            </div>
                        )}

                        <div className="relative">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                            <input
                                type="email"
                                placeholder="Email address"
                                className="ins-input pl-11 w-full bg-white/5 border-white/10 focus:border-blue-500"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        <div className="relative">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                            <input
                                type="password"
                                placeholder="Password"
                                className="ins-input pl-11 w-full bg-white/5 border-white/10 focus:border-blue-500"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-xs text-center animate-shake">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className={`prime-btn accent w-full py-4 justify-center text-sm font-semibold mt-4 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40 transition-all ${loading ? 'opacity-70 cursor-wait' : ''}`}
                        >
                            {loading ? <Loader2 className="animate-spin" size={20} /> : (isLogin ? 'Sign In to Studio' : 'Create My Account')}
                        </button>
                    </form>

                    <footer className="mt-8 text-center border-t border-white/5 pt-6 flex flex-col gap-3">
                        <span className="text-gray-500 text-xs">
                            {isLogin ? "New to Tyboo Studio?" : "Already part of the team?"}
                        </span>
                        <button
                            onClick={() => { setIsLogin(!isLogin); setError(null); }}
                            className="prime-btn w-full py-3 justify-center text-sm font-medium border-white/10 hover:border-blue-500 hover:text-blue-400 transition-all uppercase tracking-wide"
                        >
                            {isLogin ? "Create an Account" : "Sign In to your Account"}
                        </button>
                    </footer>
                </div>
            </div>
        </div>
    );
}
