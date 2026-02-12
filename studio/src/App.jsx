import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  ReactFlow,
  addEdge,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  MiniMap,
  Panel
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './index.css';
import './collaboration.css';
import axios from 'axios';
import {
  Cpu, Send, Play, Settings, MessageSquare, Search, Database,
  ChevronRight, ChevronDown, FileText, Globe, Code, Mail, BookOpen,
  X, User, CheckCircle, Zap, Bot, Brain, Layers, Terminal,
  Download, Upload, Loader2, Layout, Activity, Trash2, Copy,
  Eye, EyeOff, Maximize2, Minimize2, Scissors, Box, Link, Wrench, Shield, Key,
  LogIn, UserPlus, Camera, History, Users
} from 'lucide-react';

import CredentialModal from './components/CredentialModal';
import Dashboard from './components/Dashboard';
import VersionModal from './components/VersionModal';
import AuthModal from './components/AuthModal';

import AgentNode from './components/AgentNode';
import CopilotBar from './components/CopilotBar';
import TemplateGallery from './components/TemplateGallery';
import PublishModal from './components/PublishModal';
import WorkspaceModal from './components/WorkspaceModal';
import CollaborationOverlay from './components/CollaborationOverlay';
import CommentSidebar from './components/CommentSidebar';
import { API_BASE_URL } from './config';

const nodeTypes = { agentNode: AgentNode };

const getSidebarIcon = (iconName) => {
  if (typeof iconName === 'string' && (iconName.includes('/') || iconName.endsWith('.svg'))) {
    return 'svg';
  }
  const iconMap = {
    MessageSquare, Cpu, BookOpen, User, Search, Database,
    FileText, Globe, Code, Mail, Settings, Zap, Bot, Brain,
    Layers, Terminal, CheckCircle, Activity, Scissors, Box, Link, Wrench,
    Layout, Upload, Download, Trash2, Play, Loader2, Shield
  };
  return iconMap[iconName] || Activity;
};

const SidebarIcon = ({ item }) => {
  const [error, setError] = useState(false);
  const icon = getSidebarIcon(item.icon);

  if (icon === 'svg' && !error) {
    return (
      <img
        src={item.icon}
        alt=""
        style={{ width: 16, height: 16 }}
        onError={() => setError(true)}
      />
    );
  }

  const IconComp = icon === 'svg' ? getSidebarIcon(item.label) : icon;
  return React.createElement(IconComp || Activity, { size: 16 });
};

const App = () => {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [library, setLibrary] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCats, setExpandedCats] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Welcome to Tyboo Studio. Start by dragging components from the sidebar or use the AI copilot to generate a workflow.' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showInspector, setShowInspector] = useState(false);
  const [publishData, setPublishData] = useState(null);
  const [showChat, setShowChat] = useState(true);
  const [showMinimap, setShowMinimap] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeJobId, setActiveJobId] = useState(null);
  const [systemStats, setSystemStats] = useState(null);
  const [isCredModalOpen, setIsCredModalOpen] = useState(false);
  const [isLogOpen, setIsLogOpen] = useState(false);
  const [isVersionOpen, setIsVersionOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('studio_token'));
  const [userEmail, setUserEmail] = useState(localStorage.getItem('user_email') || '');
  const [userProfile, setUserProfile] = useState(null);
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState(localStorage.getItem('active_workspace_id') || null);
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false);
  const [collaborators, setCollaborators] = useState({}); // {userId: {name, cursor}}
  const [workflowId, setWorkflowId] = useState(null);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [isCommentOpen, setIsCommentOpen] = useState(false);
  const socketRef = useRef(null);

  // Fetch user profile on mount or auth change
  useEffect(() => {
    if (isAuthenticated) {
      const fetchProfile = async () => {
        try {
          const resp = await axios.get(`${API_BASE_URL}/auth/me`);
          setUserProfile(resp.data);
          if (resp.data.email) setUserEmail(resp.data.email);
        } catch (e) {
          console.error("Failed to fetch user profile", e);
        }
      };
      fetchProfile();
    } else {
      setUserProfile(null);
    }
  }, [isAuthenticated]);

  // Fetch stats periodically
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/stats`);
        setSystemStats(res.data);
      } catch (e) { console.error("Stats Fetch Error", e); }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket initialization
  useEffect(() => {
    if (!isAuthenticated) return;

    // Use the name or a generated ID as the room name for now
    // In production, this would be a real workflow UUID from the DB
    const roomId = workflowId || 'default-room';
    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws/' + roomId;
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => console.log(`🔌 WebSocket Connected to room: ${roomId}`);
    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type?.startsWith('collaboration_')) {
        handleCollaborationMessage(msg);
      } else {
        handleWebSocketMessage(msg);
      }
    };
    socket.onclose = () => {
      console.log('🔌 WebSocket Disconnected');
    };

    return () => socket.close();
  }, [isAuthenticated, workflowId]);

  const handleCollaborationMessage = (msg) => {
    const { user_id, type, data } = msg;
    if (type === 'collaboration_cursor') {
      setCollaborators(prev => ({
        ...prev,
        [user_id]: { ...prev[user_id], cursor: data }
      }));
    }
  };

  const onMouseMove = useCallback((event) => {
    if (socketRef.current?.readyState === WebSocket.OPEN && isAuthenticated) {
      socketRef.current.send(JSON.stringify({
        type: 'cursor',
        user_id: userEmail,
        data: { x: event.clientX, y: event.clientY }
      }));
    }
  }, [isAuthenticated, userEmail]);

  useEffect(() => {
    if (isAuthenticated) {
      window.addEventListener('mousemove', onMouseMove);
      return () => window.removeEventListener('mousemove', onMouseMove);
    }
  }, [isAuthenticated, onMouseMove]);


  // Configure axios on mount
  useEffect(() => {
    const token = localStorage.getItem('studio_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('studio_token');
    localStorage.removeItem('user_email');
    setIsAuthenticated(false);
    setUserEmail('');
    delete axios.defaults.headers.common['Authorization'];
  };

  const handleWebSocketMessage = (msg) => {
    // We update nodes regardless of jobId to show multi-user activity if desired,
    // but typically we'd check if msg.jobId === activeJobId

    switch (msg.type) {
      case 'node_start':
        updateNodeExecutionState(msg.nodeId, true);
        break;
      case 'node_end':
        updateNodeExecutionState(msg.nodeId, false);
        break;
      case 'workflow_completed':
        setIsRunning(false);
        setActiveJobId(null);
        setMessages((prev) => [...prev, { role: 'bot', text: `✅ Workflow Complete: ${msg.result}` }]);
        break;
      case 'workflow_failed':
        setIsRunning(false);
        setActiveJobId(null);
        setMessages((prev) => [...prev, { role: 'bot', text: `❌ Workflow Failed: ${msg.error}` }]);
        break;
      default:
        break;
    }
  };

  const updateNodeExecutionState = (nodeId, isExecuting) => {
    setNodes((nds) => nds.map((n) =>
      n.id === nodeId ? { ...n, data: { ...n.data, isExecuting } } : n
    ));
  };

  // Fetch library on mount
  useEffect(() => {
    const fetchLibrary = async () => {
      try {
        // Try new /nodes endpoint first, fallback to /library
        let res;
        try {
          res = await axios.get(`${API_BASE_URL}/nodes`);
        } catch {
          res = await axios.get(`${API_BASE_URL}/library`);
        }
        setLibrary(res.data);
        console.log('📚 Node Library Loaded:', {
          categories: Object.keys(res.data).length,
          totalNodes: Object.values(res.data).flat().length,
          hasPrompts: 'Prompts' in res.data || 'Models_And_Agents' in res.data,
          categories: Object.keys(res.data).slice(0, 20)
        });
        if (res.data && Object.keys(res.data).length > 0) {
          setExpandedCats([Object.keys(res.data)[0]]);
        }
      } catch (e) {
        console.error('Failed to load library:', e);
        setLibrary({});
      }
    };
    fetchLibrary();
  }, []);

  useEffect(() => {
    if (selectedNode) {
      setShowInspector(true);
    } else {
      setShowInspector(false);
    }
  }, [selectedNode]);

  // Sync selectedNode when nodes change
  useEffect(() => {
    if (selectedNode) {
      const updated = nodes.find(n => n.id === selectedNode.id);
      if (updated && JSON.stringify(updated.data) !== JSON.stringify(selectedNode.data)) {
        setSelectedNode(updated);
      }
    }
  }, [nodes]);

  // Handle SmartDB dynamic metadata fetching
  useEffect(() => {
    const fetchSmartDBMetadata = async () => {
      // Only run for smartDB and if we have credentials
      if (!selectedNode || selectedNode.data.id !== 'smartDB') return;

      const { base_url, api_key, project_id } = selectedNode.data;
      if (!base_url || !api_key) return;

      try {
        // Fetch projects if not loaded or URL/Key changed
        // We use a flag _projects_loaded to avoid infinite loops
        const projectsLoaded = selectedNode.data._projects_loaded_for === `${base_url}-${api_key}`;

        if (!projectsLoaded) {
          const res = await axios.get(`${API_BASE_URL}/nodes/smartdb/metadata`, {
            params: { base_url, api_key }
          });

          if (res.data.projects && res.data.projects.length > 0) {
            updateNodeInputs('project_id', res.data.projects.map(p => p.label));
            updateNodeData({
              '_project_mapping': res.data.projects,
              '_projects_loaded_for': `${base_url}-${api_key}`
            });
          }
        }

        // Fetch tables if project_id is selected
        if (project_id) {
          const tablesLoaded = selectedNode.data._tables_loaded_for === `${project_id}`;
          if (!tablesLoaded) {
            const mapping = selectedNode.data._project_mapping || [];
            const project = mapping.find(p => p.label === project_id);
            const actualId = project ? project.value : project_id;

            const res = await axios.get(`${API_BASE_URL}/nodes/smartdb/metadata`, {
              params: { base_url, api_key, project_id: actualId }
            });

            if (res.data.tables) {
              updateNodeInputs('table_id', res.data.tables.map(t => t.label));
              updateNodeData({
                '_table_mapping': res.data.tables,
                '_tables_loaded_for': `${project_id}`
              });
            }
          }
        }
      } catch (error) {
        console.error("SmartDB Discovery Error:", error);
      }
    };

    fetchSmartDBMetadata();
  }, [selectedNode?.data.base_url, selectedNode?.data.api_key, selectedNode?.data.project_id]);

  // Handle Supabase dynamic table fetching
  useEffect(() => {
    const fetchSupabaseTables = async () => {
      if (!selectedNode || selectedNode.data.id !== 'supabase_SupabaseVectorStore') return;

      const { supabase_url, supabase_service_key } = selectedNode.data;
      if (!supabase_url || !supabase_service_key) return;

      try {
        const res = await axios.get(`${API_BASE_URL}/nodes/supabase/tables`, {
          params: { supabase_url, supabase_key: supabase_service_key }
        });

        if (res.data.tables && res.data.tables.length > 0) {
          // Add "All Tables" option at the beginning
          const tablesWithAll = [
            { label: '🌐 All Tables', value: 'all' },
            ...res.data.tables
          ];
          updateNodeInputs('table_name', tablesWithAll);
        }
      } catch (error) {
        console.error("Supabase Discovery Error:", error);
      }
    };

    fetchSupabaseTables();
  }, [selectedNode?.data.supabase_url, selectedNode?.data.supabase_service_key]);

  // Handle Credentials Fetching
  useEffect(() => {
    const fetchCredentialsMetadata = async () => {
      if (!selectedNode) return;
      const credField = selectedNode.data.inputs?.find(i => i.type === 'credentials');
      if (!credField) return;

      try {
        const res = await axios.get(`${API_BASE_URL}/credentials/list`);
        if (res.data.credentials) {
          updateNodeInputs(credField.name, res.data.credentials);
        }
      } catch (error) {
        console.error("Credentials Fetch Error:", error);
      }
    };
    fetchCredentialsMetadata();
  }, [selectedNode?.id]);

  const updateNodeInputs = (fieldName, options) => {
    setNodes((nds) => {
      const next = nds.map((n) => {
        if (n.id === selectedNode.id) {
          const newInputs = n.data.inputs.map(input => {
            if (input.name === fieldName) return { ...input, options };
            return input;
          });
          return { ...n, data: { ...n.data, inputs: newInputs } };
        }
        return n;
      });
      return next;
    });
  };

  const updateNodeData = (updates, value) => {
    if (!selectedNode) return;
    const items = typeof updates === 'object' && !Array.isArray(updates) ? updates : { [updates]: value };

    setNodes((nds) => {
      const next = nds.map((n) => {
        if (n.id === selectedNode.id) {
          return { ...n, data: { ...n.data, ...items } };
        }
        return n;
      });
      return next;
    });
  };

  // Connection handler
  const onConnect = useCallback((params) => {
    setEdges((eds) => addEdge({
      ...params,
      animated: true,
      style: { stroke: '#3b82f6', strokeWidth: 2 }
    }, eds));
  }, [setEdges]);

  // Validate connections
  const isValidConnection = useCallback((connection) => {
    const sourceNode = nodes.find((n) => n.id === connection.source);
    const targetNode = nodes.find((n) => n.id === connection.target);

    if (!sourceNode || !targetNode) return false;

    const sourceHandle = sourceNode.data.outputs?.find((o) => o.name === connection.sourceHandle);
    const targetHandle = targetNode.data.inputs?.find((i) => i.name === connection.targetHandle);

    if (!sourceHandle || !targetHandle) return true;

    const sourceType = sourceHandle.type || 'Any';
    const targetType = targetHandle.type || 'Any';

    return sourceType === 'Any' || targetType === 'Any' || sourceType === targetType;
  }, [nodes]);

  // Drop handler
  const onDrop = useCallback((e) => {
    e.preventDefault();
    const dataStr = e.dataTransfer.getData('application/reactflow');
    if (!dataStr || !reactFlowInstance) return;

    const data = JSON.parse(dataStr);
    const pos = reactFlowInstance.screenToFlowPosition({ x: e.clientX, y: e.clientY });

    const newNode = {
      id: `${data.id}-${Date.now()}`,
      type: 'agentNode',
      position: pos,
      data: {
        ...data,
        onExecute: async (nodeId) => {
          try {
            setNodes((nds) => nds.map((n) =>
              n.id === nodeId ? { ...n, data: { ...n.data, isExecuting: true } } : n
            ));

            const res = await axios.post(`${API_BASE_URL}/run/node`, {
              nodeId,
              graph: reactFlowInstance.toObject()
            });

            setMessages((prev) => [...prev, {
              role: 'bot',
              text: `Node "${data.label}" executed successfully. Result: ${JSON.stringify(res.data.result)}`
            }]);
          } catch (e) {
            setMessages((prev) => [...prev, {
              role: 'bot',
              text: `Node execution failed: ${e.message}`
            }]);
          } finally {
            setNodes((nds) => nds.map((n) =>
              n.id === nodeId ? { ...n, data: { ...n.data, isExecuting: false } } : n
            ));
          }
        }
      }
    };

    setNodes((nds) => nds.concat(newNode));
  }, [reactFlowInstance, setNodes]);

  // Send message / run workflow
  const handleSend = async () => {
    if (!reactFlowInstance || isRunning) return;

    const msg = inputValue.trim() || 'Run workflow';
    setMessages((prev) => [...prev, { role: 'user', text: msg }]);
    setInputValue('');
    setIsRunning(true);

    try {
      // Use Async execution
      const res = await axios.post(`${API_BASE_URL}/run/async`, {
        message: msg,
        graph: reactFlowInstance.toObject()
      });

      if (res.data.job_id) {
        setActiveJobId(res.data.job_id);
        setMessages((prev) => [...prev, { role: 'bot', text: `🚀 Workflow queued (Job: ${res.data.job_id.slice(0, 8)}...). Waiting for updates...` }]);
      }
    } catch (e) {
      setMessages((prev) => [...prev, {
        role: 'bot',
        text: `Error: ${e.response?.data?.detail || e.message}`
      }]);
      setIsRunning(false);
    }
  };

  // Run node
  const handleRunNode = () => {
    if (selectedNode && selectedNode.data.onExecute) {
      selectedNode.data.onExecute(selectedNode.id);
    }
  };

  // Export workflow
  const handleExport = () => {
    if (!reactFlowInstance) return;
    const flow = reactFlowInstance.toObject();
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(flow, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `workflow-${Date.now()}.json`);
    downloadAnchor.click();
  };

  // Import workflow
  const handleImport = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const flow = JSON.parse(event.target.result);
        setNodes(flow.nodes || []);
        setEdges(flow.edges || []);
      } catch (e) {
        alert('Invalid workflow file');
      }
    };
    reader.readAsText(file);
  };

  // Clear canvas
  const handleClear = () => {
    if (window.confirm('Clear all nodes and connections?')) {
      setNodes([]);
      setEdges([]);
      setSelectedNode(null);
    }
  };

  // Delete selected node
  const handleDeleteNode = () => {
    if (!selectedNode) return;
    setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
    setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
    setSelectedNode(null);
  };

  const handleSnapshot = async () => {
    try {
      const flow = {
        nodes,
        edges,
        name: workflowName
      };

      const res = await axios.post(`${API_BASE_URL}/workflow/snapshot`, flow, {
        params: { workspace_id: currentWorkspaceId }
      });

      if (res.data.version_id) {
        alert("Immutable snapshot created successfully!");
      }
    } catch (e) {
      console.error("Snapshot failed", e);
      alert("Failed to create snapshot. Please ensure you are logged in.");
    }
  };

  const handleLoadVersion = (data) => {
    if (data.nodes) setNodes(data.nodes);
    if (data.edges) setEdges(data.edges);
    if (data.name) setWorkflowName(data.name);
  };

  // Duplicate selected node
  const handleDuplicateNode = () => {
    if (!selectedNode) return;
    const newNode = {
      ...selectedNode,
      id: `${selectedNode.data.id}-${Date.now()}`,
      position: {
        x: selectedNode.position.x + 50,
        y: selectedNode.position.y + 50
      }
    };
    setNodes((nds) => nds.concat(newNode));
  };

  return (
    <div className="app-container">
      <CollaborationOverlay collaborators={collaborators} />
      {/* Header */}
      <header className="studio-header">
        <div className="logo-container" onClick={() => window.location.reload()}>
          <img src="/logo.png" alt="Zap Logo" className="h-8 object-contain mr-2" />
          <span className="title-text">Tyboo Studio</span>
        </div>

        <div className="prime-header-right">
          {/* Team Presence */}
          <div className="team-presence">
            {Object.entries(collaborators).map(([id, data]) => (
              <div key={id} className="presence-avatar" title={data.name || id}>
                {(data.name?.[0] || id[0]).toUpperCase()}
              </div>
            ))}
          </div>

          <div className="user-profile flex items-center gap-3 px-3 py-1 bg-white/5 rounded-full border border-white/10 mr-4 cursor-default">
            <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-[10px] font-bold shadow-lg shadow-blue-500/20">
              {(userProfile?.full_name?.[0] || userEmail?.[0] || 'U').toUpperCase()}
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-white leading-tight">
                {userProfile?.full_name || userEmail?.split('@')[0]}
              </span>
              {userProfile?.company_name && (
                <span className="text-[10px] text-gray-500 leading-tight">
                  {userProfile.company_name}
                </span>
              )}
            </div>
            <button onClick={handleLogout} className="p-1 ml-2 hover:text-red-400 transition-colors border-l border-white/10 pl-2" title="Logout">
              <LogIn size={14} className="rotate-180" />
            </button>
          </div>

          <button className="prime-btn" onClick={() => setShowTemplates(true)}>
            <Layout size={16} /> Templates
          </button>

          <button className="prime-btn" onClick={() => document.getElementById('import-input').click()}>
            <Upload size={16} /> Import
          </button>
          <input
            id="import-input"
            type="file"
            accept=".json"
            onChange={handleImport}
            style={{ display: 'none' }}
          />

          <button className="prime-btn" onClick={handleExport}>
            <Download size={16} /> Export
          </button>

          <button className="prime-btn" onClick={handleClear}>
            <Trash2 size={16} /> Clear
          </button>

          <button className="prime-btn" onClick={() => setIsCredModalOpen(true)}>
            <Shield size={16} /> Security
          </button>

          <button className="prime-btn" onClick={() => setIsLogOpen(true)}>
            <Activity size={16} /> Monitor
          </button>

          <button className="prime-btn" onClick={() => setIsVersionOpen(true)}>
            <History size={16} /> History
          </button>

          <button className="prime-btn" onClick={handleSnapshot}>
            <Camera size={16} /> Snapshot
          </button>



          <button className="prime-btn accent" onClick={handleSend} disabled={isRunning}>
            {isRunning ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
            Run
          </button>
        </div>

        {/* System Health Stats In Header */}
        {systemStats && (
          <div className="system-health-strip">
            <div className="stat-item">
              <Activity size={12} />
              <span>{systemStats.status}</span>
            </div>
            <div className="stat-item">
              <Layers size={12} />
              <span>{systemStats.total_nodes} Nodes</span>
            </div>
            {systemStats.failed_workflows > 0 && (
              <div className="stat-item error">
                <X size={12} />
                <span>{systemStats.failed_workflows} Failed</span>
              </div>
            )}
            <div className="stat-item success">
              <CheckCircle size={12} />
              <span>{systemStats.worker_status}</span>
            </div>
          </div>
        )}
      </header>

      <div className="studio-workspace">
        {/* Left Sidebar */}
        {!isSidebarCollapsed && (
          <aside className="catalog-sidebar">
            <div className="catalog-header">
              <input
                className="search-prime-input"
                placeholder="Search components..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="catalog-scroller">
              {library === null ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                  Loading...
                </div>
              ) : Object.entries(library).map(([cat, items]) => {
                const filtered = items.filter((i) =>
                  i.label.toLowerCase().includes(searchTerm.toLowerCase())
                );
                if (filtered.length === 0) return null;

                const isExpanded = expandedCats.includes(cat);

                return (
                  <div key={cat} className="cat-accord">
                    <div
                      className="cat-trigger"
                      onClick={() => setExpandedCats((prev) =>
                        isExpanded ? prev.filter((c) => c !== cat) : [...prev, cat]
                      )}
                    >
                      {cat}
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </div>

                    {isExpanded && filtered.map((item) => (
                      <div
                        key={item.id}
                        className="node-drag-item"
                        draggable
                        onDragStart={(e) => {
                          e.dataTransfer.setData('application/reactflow', JSON.stringify(item));
                          e.dataTransfer.effectAllowed = 'move';
                        }}
                      >
                        <div
                          className="drag-icon-prime"
                          style={{ backgroundColor: `${item.color}20`, color: item.color }}
                        >
                          <SidebarIcon item={item} />
                        </div>
                        <span className="drag-label-prime">{item.label}</span>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </aside>
        )}

        {/* Canvas */}
        <main className="canvas-prime" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={(e) => e.preventDefault()}
            onNodeClick={(_, node) => setSelectedNode(node)}
            onPaneClick={() => setSelectedNode(null)}
            nodeTypes={nodeTypes}
            isValidConnection={isValidConnection}
            fitView
          >
            <Background color="var(--border-default)" gap={16} />
            <Controls position="bottom-left" />
            {showMinimap && <MiniMap position="bottom-right" />}

            <Panel position="top-left">
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="prime-btn"
                  onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                  title={isSidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
                >
                  {isSidebarCollapsed ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
                </button>
                <button
                  className="prime-btn"
                  onClick={() => setShowMinimap(!showMinimap)}
                  title={showMinimap ? 'Hide minimap' : 'Show minimap'}
                >
                  {showMinimap ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
                <div className="v-divider"></div>
                <button
                  className="prime-btn collabs-btn"
                  onClick={() => setIsWorkspaceOpen(true)}
                  title="Collaboration & Workspaces"
                >
                  <Users size={16} /> Collaborate
                </button>
                <button
                  className={`prime-btn ${isCommentOpen ? 'accent' : ''}`}
                  onClick={() => setIsCommentOpen(!isCommentOpen)}
                  title="Workflow Comments"
                >
                  <MessageSquare size={16} /> Feedback
                </button>
              </div>
            </Panel>
          </ReactFlow>

          {/* Chat */}
          {showChat && (
            <div className="chat-prime-box">
              <div className="chat-prime-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MessageSquare size={16} />
                  <span>Chat</span>
                </div>
                <button
                  style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                  onClick={() => setShowChat(false)}
                >
                  <X size={16} />
                </button>
              </div>

              <div className="chat-prime-scroll">
                {messages.map((m, i) => (
                  <div key={i} className={`prime-bubble ${m.role}`}>
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        img: ({ node, ...props }) => (
                          <img
                            {...props}
                            style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '8px', cursor: 'zoom-in' }}
                            onClick={() => window.open(props.src, '_blank')}
                          />
                        ),
                        table: ({ node, ...props }) => (
                          <div style={{ overflowX: 'auto', margin: '8px 0' }}>
                            <table {...props} style={{ borderCollapse: 'collapse', width: '100%', fontSize: '12px' }} />
                          </div>
                        ),
                        th: ({ node, ...props }) => <th {...props} style={{ border: '1px solid var(--border-default)', padding: '4px 8px', backgroundColor: 'var(--bg-tertiary)' }} />,
                        td: ({ node, ...props }) => <td {...props} style={{ border: '1px solid var(--border-default)', padding: '4px 8px' }} />
                      }}
                    >
                      {m.text}
                    </ReactMarkdown>
                  </div>
                ))}
              </div>

              <div className="chat-prime-input-row">
                <input
                  className="prime-chat-input"
                  placeholder="Type a message..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                />
                <button className="prime-send-btn" onClick={handleSend}>
                  <Send size={16} />
                </button>
              </div>
            </div>
          )}

          {!showChat && (
            <button
              className="prime-btn"
              style={{ position: 'absolute', bottom: '16px', right: '16px' }}
              onClick={() => setShowChat(true)}
            >
              <MessageSquare size={16} /> Show Chat
            </button>
          )}

          <CopilotBar onGenerate={(flow) => {
            setNodes(flow.nodes || []);
            setEdges(flow.edges || []);
          }} />
        </main>

        {/* Right Inspector */}
        <aside className={`prime-inspector ${showInspector ? 'open' : ''}`}>
          {selectedNode ? (
            <>
              <div className="ins-head">
                <h3>{selectedNode.data.label}</h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="prime-btn"
                    style={{ padding: '4px', backgroundColor: 'var(--success-bg)', color: 'var(--success)' }}
                    onClick={handleRunNode}
                    title="Run Node"
                    disabled={selectedNode.data.isExecuting}
                  >
                    {selectedNode.data.isExecuting ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                  </button>
                  <button
                    className="prime-btn"
                    style={{ padding: '4px' }}
                    onClick={handleDuplicateNode}
                    title="Duplicate"
                  >
                    <Copy size={16} />
                  </button>
                  <button
                    className="prime-btn"
                    style={{ padding: '4px' }}
                    onClick={handleDeleteNode}
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                  <button
                    style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                    onClick={() => setSelectedNode(null)}
                  >
                    <X size={20} />
                  </button>
                </div>
              </div>

              <div className="ins-body">
                {selectedNode.data.description && (
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: 1.5 }}>
                    {selectedNode.data.description}
                  </p>
                )}

                {(selectedNode.data.inputs || []).filter(input => input.type !== 'handle').map((field) => (
                  <div key={field.name} style={{ marginBottom: '16px' }}>
                    <label className="ins-field-label">
                      {field.display_name || field.name}
                      {field.required && <span style={{ color: 'var(--error)' }}> *</span>}
                    </label>

                    {field.type === 'boolean' ? (
                      <div className="ins-toggle-group">
                        <input
                          type="checkbox"
                          checked={selectedNode.data[field.name] ?? field.default ?? false}
                          onChange={(e) => updateNodeData(field.name, e.target.checked)}
                        />
                        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                          {field.description || 'Enable this option'}
                        </span>
                      </div>
                    ) : (field.type === 'dropdown' || field.type === 'multiselect' || field.options) ? (
                      <select
                        className="ins-input"
                        multiple={field.type === 'multiselect'}
                        style={field.type === 'multiselect' ? { height: 'auto', minHeight: '80px' } : {}}
                        value={selectedNode.data[field.name] ?? (field.type === 'multiselect' ? [] : field.default ?? '')}
                        onChange={(e) => {
                          if (field.type === 'multiselect') {
                            const values = Array.from(e.target.selectedOptions).map(o => o.value);
                            updateNodeData(field.name, values);
                          } else {
                            updateNodeData(field.name, e.target.value);
                          }
                        }}
                      >
                        {field.type !== 'multiselect' && <option value="">Select...</option>}
                        {(field.options || []).map((opt) => {
                          const label = typeof opt === 'object' ? opt.label : opt;
                          const value = typeof opt === 'object' ? opt.value : opt;
                          return <option key={value} value={value}>{label}</option>;
                        })}
                      </select>
                    ) : (
                      <input
                        className="ins-input"
                        type={field.type === 'password' ? 'password' : field.type === 'number' ? 'number' : 'text'}
                        value={selectedNode.data[field.name] ?? field.default ?? ''}
                        onChange={(e) => updateNodeData(field.name, field.type === 'number' ? parseFloat(e.target.value) : e.target.value)}
                        placeholder={field.description}
                      />
                    )}

                    {field.description && field.type !== 'boolean' && (
                      <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '4px' }}>
                        {field.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <Settings size={48} style={{ marginBottom: '1rem', opacity: 0.3 }} />
              <p>Select a node to configure</p>
            </div>
          )}
        </aside>
      </div>

      {/* Modals */}
      {showTemplates && (
        <TemplateGallery
          onSelect={(template) => {
            setNodes(template.nodes || []);
            setEdges(template.edges || []);
            setShowTemplates(false);
          }}
          onClose={() => setShowTemplates(false)}
        />
      )}

      {publishData && (
        <PublishModal
          publishData={publishData}
          onClose={() => setPublishData(null)}
        />
      )}

      <CredentialModal isOpen={isCredModalOpen} onClose={() => setIsCredModalOpen(false)} />
      <Dashboard isOpen={isLogOpen} onClose={() => setIsLogOpen(false)} />
      <VersionModal
        isOpen={isVersionOpen}
        onClose={() => setIsVersionOpen(false)}
        onLoadVersion={handleLoadVersion}
      />

      <AuthModal
        isOpen={!isAuthenticated}
        onAuthSuccess={() => {
          setIsAuthenticated(true);
          setUserEmail(localStorage.getItem('user_email'));
        }}
      />

      <WorkspaceModal
        isOpen={isWorkspaceOpen}
        onClose={() => setIsWorkspaceOpen(false)}
        currentWorkspaceId={currentWorkspaceId}
        onWorkspaceSwitch={(wsId) => {
          setCurrentWorkspaceId(wsId);
          localStorage.setItem('active_workspace_id', wsId);
        }}
      />

      <CommentSidebar
        isOpen={isCommentOpen}
        onClose={() => setIsCommentOpen(false)}
        workflowId={workflowId}
        selectedNodeId={selectedNode?.id}
      />
    </div>
  );
};

export default () => (
  <ReactFlowProvider>
    <App />
  </ReactFlowProvider>
);
