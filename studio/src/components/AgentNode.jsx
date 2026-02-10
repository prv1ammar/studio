import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import {
    Cpu, Brain, Database, Search, Globe, MessageSquare,
    Wind, Layers, Mail, FileText, Settings, BookOpen,
    CheckCircle, User, Zap, ArrowRightCircle, LogOut, PenTool, Bot,
    Play, Loader2, Code, Type, Activity, Terminal,
    Scissors, Box, Link, Wrench
} from 'lucide-react';

const icons = {
    OpenAI: Cpu, Anthropic: Brain, Google: Globe, Mistral: Wind, Ollama: Layers,
    Pinecone: Layers, Chroma: Database, MongoDB: Database, PostgreSQL: Database,
    Supabase: Database, Tavily: Search, DuckDuckGo: Search, SerpApi: Search,
    Wikipedia: BookOpen, Gmail: Mail, Slack: MessageSquare, Notion: FileText,
    Airtable: Settings, chatInput: MessageSquare, textInput: Type,
    fileInput: FileText, urlLoader: Globe, promptTemplate: PenTool,
    chatPrompt: MessageSquare, toolCallingAgent: Bot, reactAgent: Zap,
    router: ArrowRightCircle, conditional: ArrowRightCircle,
    chatOutput: LogOut, textOutput: LogOut, faq: BookOpen,
    booking: CheckCircle, patient: User, orchestrator: Cpu,
    OpenRouter: Globe, Groq: Zap, DeepSeek: Brain, AstraDB: Database,
    FAISS: Layers, Milvus: Database, SearchAPI: Search, Python: Code,
    Bot, Code, Box
};

const getLucideIcon = (name) => {
    const iconMap = {
        Cpu, Brain, Database, Search, Globe, MessageSquare,
        Wind, Layers, Mail, FileText, Settings, BookOpen,
        CheckCircle, User, Zap, ArrowRightCircle, LogOut, PenTool, Bot,
        Code, Type, Terminal, Scissors, Box, Link, Wrench
    };
    if (iconMap[name]) return iconMap[name];
    return Activity;
};

const TYPE_COLORS = {
    Text: '#10b981',
    LanguageModel: '#8b5cf6',
    BaseRetriever: '#f59e0b',
    VectorStore: '#3b82f6',
    Data: '#06b6d4',
    Any: '#6b7280',
    Chain: '#f59e0b',
    Tool: '#ec4899'
};

const AgentNode = ({ id, data, selected }) => {
    const [iconError, setIconError] = React.useState(false);
    const isSvgIcon = !iconError && typeof data.icon === 'string' && (data.icon.includes('/') || data.icon.endsWith('.svg'));
    const IconComponent = (icons[data.icon] || getLucideIcon(data.icon || data.label));

    const color = data.color || '#3b82f6';
    const isExecuting = data.isExecuting;

    const getPortColor = (port) => {
        const type = port.type || (port.types && port.types[0]) || 'Any';
        return TYPE_COLORS[type] || TYPE_COLORS.Any;
    };

    const inputs = (data.inputs || []).filter(input => input.type === 'handle');
    const outputs = data.outputs || [];

    return (
        <div className={`prime-node-wrapper ${selected ? 'selected' : ''}`}>
            {/* Header */}
            <div className="prime-node-header">
                <div
                    className="prime-node-icon"
                    style={{
                        background: `${color}15`,
                        color: color,
                    }}
                >
                    {isSvgIcon ? (
                        <img
                            src={data.icon}
                            alt=""
                            style={{ width: 18, height: 18 }}
                            onError={() => setIconError(true)}
                        />
                    ) : (
                        <IconComponent size={18} strokeWidth={2.5} />
                    )}
                </div>

                <div className="prime-node-title-box">
                    <div className="prime-node-label">{data.label || 'Node'}</div>
                    <div className="prime-node-id">{data.category || 'Component'}</div>
                </div>

                {isExecuting && (
                    <div className="execution-pulse">
                        <Loader2 size={14} className="animate-spin" style={{ color: color }} />
                    </div>
                )}
            </div>

            {/* Body with Ports */}
            {(inputs.length > 0 || outputs.length > 0) && (
                <div className="prime-node-body">
                    <div className="port-column">
                        {inputs.map((input, idx) => {
                            const portColor = getPortColor(input);
                            return (
                                <div key={`in-${idx}`} className="port-row-input">
                                    <div className="port-handle-wrapper">
                                        <Handle
                                            type="target"
                                            position={Position.Left}
                                            id={input.name}
                                            className="custom-handle"
                                            style={{ background: portColor }}
                                        />
                                    </div>
                                    <span className="port-label">{input.display_name || input.name}</span>
                                </div>
                            );
                        })}
                    </div>

                    <div className="port-column">
                        {outputs.map((output, idx) => {
                            const portColor = getPortColor(output);
                            return (
                                <div key={`out-${idx}`} className="port-row-output">
                                    <span className="port-label">{output.display_name || output.name}</span>
                                    <div className="port-handle-wrapper">
                                        <Handle
                                            type="source"
                                            position={Position.Right}
                                            id={output.name}
                                            className="custom-handle"
                                            style={{ background: portColor }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default memo(AgentNode);
