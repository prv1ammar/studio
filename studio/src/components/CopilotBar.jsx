import React, { useState } from 'react';
import '../Copilot.css';
import { Send, Sparkles, Zap, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '../config';

const CopilotBar = ({ onGenerate }) => {
    const [prompt, setPrompt] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!prompt.trim()) return;

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/copilot/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });
            const data = await response.json();
            if (data.status === 'success' && data.flow) {
                onGenerate(data.flow);
            } else {
                alert("AI Oracle: Could not generate this flow. Please refine your vision.");
            }
        } catch (err) {
            console.error("Copilot Error:", err);
            alert("Connection error: AI Core is currently offline.");
        } finally {
            setLoading(false);
            setPrompt('');
        }
    };

    const suggestions = [
        "Architect a RAG pipeline",
        "Genesis: Simple ChatBot",
        "Neural Link: PDF Analysis"
    ];

    return (
        <div className="copilot-container">
            <form onSubmit={handleSubmit} className="copilot-input-wrapper">
                <Sparkles size={20} className="sparkle-icon" />
                <input
                    type="text"
                    className="copilot_input"
                    placeholder="Command your vision... (e.g. 'Build a PDF analyzer')"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                />
                <button type="submit" className="copilot-btn" disabled={loading}>
                    {loading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                </button>
            </form>

            {!loading && (
                <div className="copilot-suggestion">
                    {suggestions.map((s, i) => (
                        <div key={i} className="chip-suggestion" onClick={() => setPrompt(s)}>
                            <Zap size={10} style={{ display: 'inline', marginRight: 6 }} />
                            {s}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default CopilotBar;
