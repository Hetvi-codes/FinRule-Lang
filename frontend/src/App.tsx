import React, { useState, useEffect, useRef, useCallback } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ResultsPanel } from './components/ResultsPanel';
import { TemplatesModal } from './components/TemplatesModal';
import { VersionModal } from './components/VersionModal';
import { CreateModelModal } from './components/CreateModelModal';
import { setupModelScriptLanguage } from './compiler/modelscriptMonaco';
import { 
  api, 
  CompileResult, 
  Project, 
  ModelItem, 
  TemplateItem, 
  ModelVersion 
} from './api/client';
import { Save, Check, FileCode, Play, Sparkles, Layers, BookmarkPlus } from 'lucide-react';

export const App: React.FC = () => {
  // Theme State
  const [isDark, setIsDark] = useState<boolean>(() => {
    return localStorage.getItem('finrule_theme') !== 'light';
  });

  // Projects & Models State
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProjectId, setCurrentProjectId] = useState<string>('');
  const [models, setModels] = useState<ModelItem[]>([]);
  const [currentModelId, setCurrentModelId] = useState<string>('');
  const [sourceCode, setSourceCode] = useState<string>('');

  // Compiler & Execution State
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [compileResult, setCompileResult] = useState<CompileResult | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);

  // UI State
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [showStudio, setShowStudio] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Resizable split panel
  const [editorWidthPct, setEditorWidthPct] = useState<number>(45);
  const isResizing = useRef<boolean>(false);
  const workspaceRef = useRef<HTMLDivElement>(null);

  // Modals
  const [showTemplatesModal, setShowTemplatesModal] = useState<boolean>(false);
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [customTemplates, setCustomTemplates] = useState<TemplateItem[]>(() => {
    try {
      const saved = localStorage.getItem('finrule_custom_templates');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [showVersionsModal, setShowVersionsModal] = useState<boolean>(false);
  const [versions, setVersions] = useState<ModelVersion[]>([]);
  const [showCreateModelModal, setShowCreateModelModal] = useState<boolean>(false);

  const editorRef = useRef<any>(null);

  // Resize handler
  const handleResizeMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isResizing.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMouseMove = (ev: MouseEvent) => {
      if (!isResizing.current || !workspaceRef.current) return;
      const rect = workspaceRef.current.getBoundingClientRect();
      const sidebarEl = workspaceRef.current.querySelector('[data-sidebar]') as HTMLElement;
      const sidebarWidth = sidebarEl ? sidebarEl.offsetWidth : 0;
      const available = rect.width - sidebarWidth;
      const relX = ev.clientX - rect.left - sidebarWidth;
      let pct = (relX / available) * 100;
      pct = Math.max(25, Math.min(70, pct)); // clamp 25%–70%
      setEditorWidthPct(pct);
    };

    const onMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, []);

  // Apply dark/light class to root
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
    }
    localStorage.setItem('finrule_theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // Default fallback model so editor is never stuck loading
  const DEFAULT_CODE = `// FinRule: SaaS Recurring Revenue & Churn Projection
model "SaaS Growth Engine" {
  starting_mrr = 75000
  monthly_growth = 0.055
  churn = 0.02
  cogs_rate = 0.22
  opex = 38000

  for month in 1 to 24 {
    mrr = starting_mrr * (1 + monthly_growth - churn) ^ month
    revenue = mrr
    cogs = revenue * cogs_rate
    gross_profit = revenue - cogs
    net_profit = gross_profit - opex

    output month, mrr, revenue, cogs, gross_profit, net_profit
  }
}

scenario "Aggressive Growth" {
  monthly_growth = 0.09
  churn = 0.015
  opex = 45000
}

scenario "Recession Stress Test" {
  monthly_growth = 0.02
  churn = 0.045
  opex = 32000
}
`;

  // Initial Data Load with auto-retry
  useEffect(() => {
    let retryTimer: any = null;

    const initData = async (retries = 3) => {
      try {
        // Load projects
        const projs = await api.getProjects();
        if (projs && projs.length > 0) {
          setProjects(projs);
          const firstProj = projs[0];
          setCurrentProjectId(firstProj.id);

          // Load models for first project
          const mods = await api.getModels(firstProj.id);
          if (mods && mods.length > 0) {
            setModels(mods);
            const firstMod = mods[0];
            setCurrentModelId(firstMod.id);
            setSourceCode(firstMod.source_code);
            runCompiler(firstMod.source_code, firstMod.id);
          }
        } else {
          // If empty, set sensible local defaults
          setSourceCode(DEFAULT_CODE);
          runCompiler(DEFAULT_CODE, 'default');
        }

        // Load templates
        const tpls = await api.getTemplates();
        if (tpls && tpls.length > 0) setTemplates(tpls);

        // Load custom templates from DB (MongoDB Atlas primary, local fallback)
        try {
          const customTpls = await api.getCustomTemplates();
          if (customTpls && customTpls.length > 0) {
            setCustomTemplates(prev => {
              const ids = new Set(customTpls.map(t => t.id));
              const merged = [...customTpls, ...prev.filter(t => !ids.has(t.id))];
              localStorage.setItem('finrule_custom_templates', JSON.stringify(merged));
              return merged;
            });
          }
        } catch {
          // Fall back gracefully to localStorage
        }

        // Load executions
        const execs = await api.getExecutions();
        if (execs && execs.length > 0) setExecutions(execs);
      } catch (err) {
        console.warn('Backend not ready yet, retrying in 2s...', err);
        // Use default code immediately so user never waits
        if (!sourceCode) {
          setSourceCode(DEFAULT_CODE);
          runCompiler(DEFAULT_CODE, 'default');
        }
        if (retries > 0) {
          retryTimer = setTimeout(() => initData(retries - 1), 2000);
        }
      }
    };

    initData();
    return () => clearTimeout(retryTimer);
  }, []);

  // Keyboard shortcut: Ctrl + Enter to run model
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        runCompiler();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveModel();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sourceCode, currentModelId, selectedScenario]);

  // Compiler execution runner
  const runCompiler = async (codeOverride?: string, modelIdOverride?: string, scenarioOverride?: string) => {
    const code = codeOverride !== undefined ? codeOverride : sourceCode;
    const modelId = modelIdOverride || currentModelId;
    const scen = scenarioOverride !== undefined ? scenarioOverride : selectedScenario;

    if (!code.trim()) return;

    setIsRunning(true);
    try {
      const res = await api.execute(code, modelId, scen);
      setCompileResult(res);

      // Extract scenario names from result
      if (res.scenarios) {
        setScenarios(Object.keys(res.scenarios));
      }

      // Refresh executions history
      const execs = await api.getExecutions();
      setExecutions(execs);
    } catch (err) {
      console.error('Compilation call failed:', err);
    } finally {
      setIsRunning(false);
    }
  };

  // Switch Model (with automatic save of currently edited model)
  const handleSelectModel = (modelId: string) => {
    if (modelId === currentModelId) return;

    // Auto-persist active model in local models list before switching away
    if (currentModelId && sourceCode) {
      setModels(prev => prev.map(m => m.id === currentModelId ? { ...m, source_code: sourceCode } : m));
      api.updateModel(currentModelId, { source_code: sourceCode, commit_message: 'Auto-save on model switch' }).catch(console.error);
    }

    const target = models.find(m => m.id === modelId);
    if (target) {
      setCurrentModelId(target.id);
      setSourceCode(target.source_code);
      setSelectedScenario('');
      runCompiler(target.source_code, target.id, '');
    }
  };

  // Open Create Model Modal (replaces browser prompt)
  const handleCreateModel = () => {
    setShowCreateModelModal(true);
  };

  // Confirm creation with custom boilerplate
  const handleConfirmCreateModel = async (name: string, templateType: 'loan' | 'growth' | 'blank') => {
    let initialCode = '';

    if (templateType === 'loan') {
      initialCode = `// FinRule: ${name}
model "${name}" {
  loan_amount = 500000
  annual_rate = 0.085
  term_months = 24
  monthly_rate = annual_rate / 12

  // Built-in PMT function calculates fixed monthly installment
  monthly_payment = PMT(monthly_rate, term_months, loan_amount)
  balance = loan_amount

  for month in 1 to 24 {
    interest_fee = balance * monthly_rate
    principal_paid = monthly_payment - interest_fee
    balance = balance - principal_paid

    output month, monthly_payment, principal_paid, interest_fee, balance
  }
}

scenario "Low Interest Rate" {
  annual_rate = 0.065
}

scenario "Rate Spike Stress Test" {
  annual_rate = 0.11
}
`;
    } else if (templateType === 'growth') {
      initialCode = `// FinRule: ${name}
model "${name}" {
  starting_revenue = 60000
  monthly_growth = 0.05
  cogs_rate = 0.20
  opex = 18000

  for month in 1 to 12 {
    revenue = starting_revenue * (1 + monthly_growth) ^ month
    cogs = revenue * cogs_rate
    gross_profit = revenue - cogs
    net_profit = gross_profit - opex

    output month, revenue, cogs, gross_profit, net_profit
  }
}

scenario "Aggressive Expansion" {
  monthly_growth = 0.08
  opex = 24000
}
`;
    } else {
      initialCode = `// FinRule: ${name}
model "${name}" {
  starting_balance = 100000
  monthly_rate = 0.04

  for month in 1 to 12 {
    balance = starting_balance * (1 + monthly_rate) ^ month
    output month, balance
  }
}
`;
    }

    try {
      const created = await api.createModel(currentProjectId, name, initialCode);
      setModels([...models, created]);
      setCurrentModelId(created.id);
      setSourceCode(created.source_code);
      runCompiler(created.source_code, created.id);
    } catch (err) {
      alert('Failed to create model: ' + err);
    }
  };

  // Delete Model
  const handleDeleteModel = async (modelId: string) => {
    try {
      await api.deleteModel(modelId);
      const remaining = models.filter(m => m.id !== modelId);
      setModels(remaining);
      if (remaining.length > 0) {
        handleSelectModel(remaining[0].id);
      }
    } catch (err) {
      alert('Failed to delete model: ' + err);
    }
  };

  // Save / Snapshot (updates local models state immediately)
  const saveModel = async (commitMessage?: string) => {
    if (!currentModelId) return;
    setIsSaving(true);
    // Keep local models list up to date immediately so switching never loses changes!
    setModels(prev => prev.map(m => m.id === currentModelId ? { ...m, source_code: sourceCode } : m));
    try {
      await api.updateModel(currentModelId, {
        source_code: sourceCode,
        commit_message: commitMessage || 'Manual code save'
      });
      setLastSaved(new Date());
    } catch (err) {
      console.error('Save failed:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Load versions
  const handleOpenVersions = async () => {
    if (!currentModelId) return;
    try {
      const vers = await api.getVersions(currentModelId);
      setVersions(vers);
      setShowVersionsModal(true);
    } catch (err) {
      alert('Failed to fetch versions: ' + err);
    }
  };

  // Restore version
  const handleRestoreVersion = async (versionId: string) => {
    try {
      const restored = await api.restoreVersion(currentModelId, versionId);
      setSourceCode(restored.source_code);
      runCompiler(restored.source_code, restored.id);
    } catch (err) {
      alert('Failed to restore version: ' + err);
    }
  };

  // Save custom template (MongoDB Atlas primary, localStorage fallback)
  const handleSaveCustomTemplate = async (newTpl: TemplateItem) => {
    const updated = [newTpl, ...customTemplates.filter(t => t.id !== newTpl.id)];
    setCustomTemplates(updated);
    localStorage.setItem('finrule_custom_templates', JSON.stringify(updated));

    try {
      const savedBackend = await api.createCustomTemplate({
        name: newTpl.name,
        category: newTpl.category,
        description: newTpl.description,
        source_code: newTpl.source_code
      });
      if (savedBackend?.id) {
        setCustomTemplates(prev => prev.map(t => t.id === newTpl.id ? { ...t, id: savedBackend.id } : t));
      }
    } catch (e) {
      console.warn('Backend custom template save skipped, saved locally:', e);
    }
  };

  // Delete custom template
  const handleDeleteCustomTemplate = async (id: string) => {
    const updated = customTemplates.filter(t => t.id !== id);
    setCustomTemplates(updated);
    localStorage.setItem('finrule_custom_templates', JSON.stringify(updated));

    try {
      await api.deleteCustomTemplate(id);
    } catch (e) {
      console.warn('Backend delete custom template failed:', e);
    }
  };


  // Clone or Load template
  const handleSelectTemplate = async (templateId: string, customItem?: TemplateItem) => {
    if (customItem || templateId.startsWith('custom-')) {
      const tpl = customItem || customTemplates.find(t => t.id === templateId);
      if (!tpl) return;
      try {
        const created = await api.createModel(currentProjectId, tpl.name, tpl.source_code);
        setModels([...models, created]);
        setCurrentModelId(created.id);
        setSourceCode(created.source_code);
        runCompiler(created.source_code, created.id);
      } catch (err) {
        alert('Failed to load custom template: ' + err);
      }
      return;
    }

    try {
      const cloned = await api.cloneTemplate(templateId, currentProjectId);
      setModels([...models, cloned]);
      setCurrentModelId(cloned.id);
      setSourceCode(cloned.source_code);
      runCompiler(cloned.source_code, cloned.id);
    } catch (err) {
      alert('Failed to clone template: ' + err);
    }
  };

  // Export CSV / JSON
  const handleExport = (format: 'csv' | 'json') => {
    if (!compileResult?.rows || compileResult.rows.length === 0) {
      alert('No data available to export. Run the model first.');
      return;
    }

    let content = '';
    let mimeType = '';
    let ext = '';

    if (format === 'csv') {
      const header = compileResult.columns.join(',');
      const rows = compileResult.rows.map(r => 
        compileResult.columns.map(c => JSON.stringify(r[c] ?? '')).join(',')
      ).join('\n');
      content = `${header}\n${rows}`;
      mimeType = 'text/csv';
      ext = 'csv';
    } else {
      content = JSON.stringify(compileResult.rows, null, 2);
      mimeType = 'application/json';
      ext = 'json';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentModel?.name || 'finrule_model'}_export.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Monaco Editor configuration
  const handleEditorBeforeMount = (monaco: Monaco) => {
    setupModelScriptLanguage(monaco);
  };

  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor;
    if (document.fonts) {
      document.fonts.ready.then(() => {
        monaco.editor.remeasureFonts();
        editor.layout();
      });
    }
  };


  const currentModel = models.find(m => m.id === currentModelId);
  const currentProject = projects.find(p => p.id === currentProjectId);

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: 'var(--bg-app)' }}>
      {/* Top Header (Clean, Uncongested SaaS Nav) */}
      <Header
        modelName={currentModel?.name || compileResult?.model_name || 'SaaS Growth Engine'}
        projectName={currentProject?.name || 'Strategic Finance 2026'}
        onOpenVersions={handleOpenVersions}
        onOpenTemplates={() => setShowTemplatesModal(true)}
        onExport={handleExport}
        showStudio={showStudio}
        onToggleStudio={() => setShowStudio(!showStudio)}
        isDark={isDark}
        onToggleTheme={() => setIsDark(!isDark)}
      />

      {/* Main Workspace Body */}
      <div ref={workspaceRef} className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <div data-sidebar>
          <Sidebar
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            projects={projects}
            currentProjectId={currentProjectId}
            onSelectProject={(id) => setCurrentProjectId(id)}
            models={models}
            currentModelId={currentModelId}
            onSelectModel={handleSelectModel}
            onCreateModel={handleCreateModel}
            onDeleteModel={handleDeleteModel}
            onOpenTemplates={() => setShowTemplatesModal(true)}
            executions={executions}
          />
        </div>

        {/* Center: Monaco Code Editor */}
        <div 
          className="flex flex-col" 
          style={{ 
            width: `${editorWidthPct}%`, 
            minWidth: '280px',
            flexShrink: 0,
            borderRight: 'none',
            background: 'var(--bg-panel)',
            height: '100%',
            minHeight: 0
          }}
        >
          {/* Editor Sub-Header / Execution Toolbar */}
          <div style={{
            minHeight: '44px',
            padding: '0.35rem 0.85rem',
            borderBottom: '1px solid var(--border-color)',
            background: 'var(--bg-sidebar)',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.65rem'
          }}>
            {/* Left: File name, DSL badge, Save, and Save as Template */}
            <div className="flex items-center gap-2">
              <FileCode size={15} color="var(--accent-emerald)" />
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)' }}>
                {currentModel?.name || 'Editor'}.fin
              </span>
              <span className="badge badge-emerald" style={{ fontSize: '0.625rem', padding: '0.05rem 0.35rem' }}>
                DSL v2.0
              </span>

              <div style={{ height: '14px', width: '1px', background: 'var(--border-color)', margin: '0 0.2rem' }} />

              <button
                onClick={() => saveModel()}
                disabled={isSaving}
                className="btn-ghost"
                style={{ fontSize: '0.725rem', padding: '0.2rem 0.45rem' }}
                title="Save current model (Ctrl + S)"
              >
                {isSaving ? (
                  <span>Saving...</span>
                ) : (
                  <>
                    <Save size={12} />
                    <span>{lastSaved ? 'Saved' : 'Save'}</span>
                  </>
                )}
              </button>

              <button
                onClick={() => setShowTemplatesModal(true)}
                className="btn-ghost"
                style={{ fontSize: '0.725rem', padding: '0.2rem 0.45rem', color: 'var(--accent-cyan)' }}
                title="Save this code as a reusable Custom Template"
              >
                <BookmarkPlus size={13} />
                <span>Save as Template</span>
              </button>
            </div>

            {/* Right: Scenario dropdown, Run Model Button, and execution time */}
            <div className="flex items-center gap-2">
              {/* Scenario Selector */}
              {scenarios.length > 0 && (
                <div className="flex items-center gap-1.5" style={{ 
                  background: 'var(--bg-input)', 
                  border: '1px solid var(--border-color)', 
                  borderRadius: '0.375rem',
                  padding: '0.15rem 0.45rem',
                  fontSize: '0.75rem'
                }}>
                  <Layers size={13} color="var(--accent-cyan)" />
                  <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>Scenario:</span>
                  <select
                    value={selectedScenario}
                    onChange={(e) => {
                      const scen = e.target.value;
                      setSelectedScenario(scen);
                      runCompiler(undefined, undefined, scen);
                    }}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-main)',
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="" style={{ background: '#0e1524', color: '#fff' }}>Base Model</option>
                    {scenarios.map((scen) => (
                      <option key={scen} value={scen} style={{ background: '#0e1524', color: '#fff' }}>
                        {scen}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Execution time pill */}
              {compileResult?.timings?.total_ms !== undefined && (
                <div className="badge badge-emerald" style={{ fontSize: '0.675rem' }}>
                  <Check size={10} />
                  {compileResult.timings.total_ms}ms
                </div>
              )}

              {/* Prominent Run Model Button */}
              <button
                onClick={() => runCompiler()}
                disabled={isRunning}
                className="btn-primary"
                style={{
                  padding: '0.25rem 0.75rem',
                  fontSize: '0.785rem',
                  boxShadow: '0 2px 10px rgba(16, 185, 129, 0.35)'
                }}
                title="Compile & Execute (Ctrl + Enter)"
              >
                {isRunning ? (
                  <>
                    <div style={{
                      width: '12px',
                      height: '12px',
                      border: '2px solid rgba(255,255,255,0.3)',
                      borderTopColor: '#ffffff',
                      borderRadius: '50%',
                      animation: 'spin 0.6s linear infinite'
                    }} />
                    <span>Running...</span>
                  </>
                ) : (
                  <>
                    <Play size={13} fill="#ffffff" />
                    <span>Run Model</span>
                    <span style={{ 
                      fontSize: '0.625rem', 
                      background: 'rgba(0,0,0,0.25)', 
                      padding: '0.05rem 0.3rem', 
                      borderRadius: '3px',
                      opacity: 0.9 
                    }}>
                      Ctrl+↵
                    </span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Monaco Editor Instance */}
          <div className="flex-1" style={{ minHeight: 0, position: 'relative', overflow: 'hidden' }}>
            <Editor
              height="100%"
              language="modelscript"
              theme={isDark ? 'finrule-dark' : 'finrule-light'}
              value={sourceCode}
              onChange={(value) => {
                const code = value || '';
                setSourceCode(code);
                if (currentModelId) {
                  setModels(prev => prev.map(m => m.id === currentModelId ? { ...m, source_code: code } : m));
                }
              }}
              beforeMount={handleEditorBeforeMount}
              onMount={handleEditorDidMount}
              options={{
                fontSize: 13,
                fontFamily: "'JetBrains Mono', Consolas, 'Courier New', monospace",
                lineNumbers: 'on',
                glyphMargin: false,
                folding: true,
                minimap: { enabled: false },
                wordWrap: 'on',
                wrappingStrategy: 'advanced',
                scrollBeyondLastLine: true,
                scrollBeyondLastColumn: 20,
                automaticLayout: true,
                tabSize: 2,
                cursorBlinking: 'smooth',
                cursorSmoothCaretAnimation: 'on',
                bracketPairColorization: { enabled: true },
                padding: { top: 12, bottom: 80 },
                cursorSurroundingLines: 3,
                smoothScrolling: true,
                overviewRulerLanes: 0,
                hideCursorInOverviewRuler: true,
                overviewRulerBorder: false,
                scrollbar: {
                  vertical: 'visible',
                  horizontal: 'visible',
                  verticalScrollbarSize: 8,
                  horizontalScrollbarSize: 8,
                  alwaysConsumeMouseWheel: false,
                },
              }}

            />
          </div>

          {/* Editor Status Bar */}
          <div style={{
            height: '24px',
            padding: '0 0.85rem',
            borderTop: '1px solid var(--border-color)',
            background: 'var(--bg-sidebar)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.675rem',
            color: 'var(--text-dim)'
          }}>
            <div className="flex items-center gap-3">
              <span>ModelScript DSL</span>
              <span>UTF-8</span>
            </div>
            <div className="flex items-center gap-2">
              <span>Press <kbd style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 4px', borderRadius: '3px' }}>Ctrl + Enter</kbd> to compile</span>
            </div>
          </div>
        </div>

        {/* Resize Handle */}
        <div
          onMouseDown={handleResizeMouseDown}
          style={{
            width: '5px',
            flexShrink: 0,
            background: 'var(--border-color)',
            cursor: 'col-resize',
            position: 'relative',
            zIndex: 10,
            transition: 'background 0.15s',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--accent-emerald)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'var(--border-color)')}
          title="Drag to resize panels"
        />

        {/* Right: Results & Compiler Studio Panel */}
        <ResultsPanel
          result={compileResult}
          isRunning={isRunning}
          showStudio={showStudio}
        />
      </div>

      {/* Modals */}
      <TemplatesModal
        isOpen={showTemplatesModal}
        onClose={() => setShowTemplatesModal(false)}
        templates={templates}
        customTemplates={customTemplates}
        currentSourceCode={sourceCode}
        currentModelName={currentModel?.name}
        onSelectTemplate={handleSelectTemplate}
        onSaveCustomTemplate={handleSaveCustomTemplate}
        onDeleteCustomTemplate={handleDeleteCustomTemplate}
      />

      <VersionModal
        isOpen={showVersionsModal}
        onClose={() => setShowVersionsModal(false)}
        versions={versions}
        onRestore={handleRestoreVersion}
      />

      <CreateModelModal
        isOpen={showCreateModelModal}
        onClose={() => setShowCreateModelModal(false)}
        onCreate={handleConfirmCreateModel}
      />
    </div>
  );
};
