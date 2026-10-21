import React, { useState } from 'react';
import { 
  Play, 
  Layers, 
  Download, 
  History, 
  Moon, 
  Sun, 
  Terminal, 
  Code2, 
  Check, 
  ChevronDown,
  Sparkles,
  FolderOpen
} from 'lucide-react';

interface HeaderProps {
  modelName: string;
  projectName: string;
  isRunning?: boolean;
  onRun?: () => void;
  scenarios?: string[];
  selectedScenario?: string;
  onSelectScenario?: (scen: string) => void;
  onSave?: () => void;
  onOpenVersions: () => void;
  onOpenTemplates: () => void;
  onExport: (format: 'csv' | 'json') => void;
  showStudio: boolean;
  onToggleStudio: () => void;
  isDark: boolean;
  onToggleTheme: () => void;
  executionTimeMs?: number;
}

export const Header: React.FC<HeaderProps> = ({
  modelName,
  projectName,
  onOpenVersions,
  onOpenTemplates,
  onExport,
  showStudio,
  onToggleStudio,
  isDark,
  onToggleTheme,
}) => {
  const [showExportMenu, setShowExportMenu] = useState(false);

  return (
    <header className="glass-panel" style={{ 
      height: '56px', 
      borderBottom: '1px solid var(--border-color)',
      padding: '0 1rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'relative',
      zIndex: 40
    }}>
      {/* Brand & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2" style={{ marginRight: '0.5rem' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(16, 185, 129, 0.35)'
          }}>
            <Code2 size={16} color="#ffffff" strokeWidth={2.5} />
          </div>
          <span style={{ fontWeight: 800, fontSize: '1rem', letterSpacing: '-0.02em', background: 'linear-gradient(135deg, #ffffff 40%, #94a3b8 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: isDark ? 'transparent' : 'var(--text-main)' }}>
            FinRule
          </span>
          <span className="badge badge-emerald" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
            DSL v2.0
          </span>
        </div>

        <div style={{ height: '16px', width: '1px', background: 'var(--border-color)' }} />

        {/* Project & Model Title */}
        <div className="flex items-center gap-2" style={{ fontSize: '0.8125rem' }}>
          <span style={{ color: 'var(--text-dim)' }}>{projectName}</span>
          <span style={{ color: 'var(--text-dim)' }}>/</span>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{modelName}</span>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2">
        {/* Compiler Studio Toggle Button */}
        <button
          onClick={onToggleStudio}
          className="btn-secondary"
          style={{
            borderColor: showStudio ? 'var(--accent-cyan)' : 'var(--border-color)',
            color: showStudio ? 'var(--accent-cyan)' : 'var(--text-muted)',
            background: showStudio ? 'var(--accent-cyan-light)' : 'transparent'
          }}
          title="Toggle Principles of Compiler Design Inspector"
        >
          <Terminal size={14} />
          <span>Compiler Studio</span>
          <span className="badge badge-cyan" style={{ fontSize: '0.65rem', padding: '0 0.3rem' }}>
            Course
          </span>
        </button>

        {/* Templates */}
        <button
          onClick={onOpenTemplates}
          className="btn-ghost"
          title="Pre-built Financial Templates"
        >
          <Sparkles size={15} color="var(--accent-amber)" />
          <span>Templates</span>
        </button>

        {/* Version History */}
        <button
          onClick={onOpenVersions}
          className="btn-ghost"
          title="Model Version Snapshots"
        >
          <History size={15} />
          <span>History</span>
        </button>

        {/* Export Menu */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="btn-ghost"
            title="Export Data"
          >
            <Download size={15} />
            <ChevronDown size={12} />
          </button>

          {showExportMenu && (
            <div 
              className="glass-panel" 
              style={{
                position: 'absolute',
                right: 0,
                top: '100%',
                marginTop: '0.35rem',
                borderRadius: '0.5rem',
                padding: '0.35rem',
                minWidth: '130px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.4)'
              }}
            >
              <button
                onClick={() => { onExport('csv'); setShowExportMenu(false); }}
                className="btn-ghost w-full"
                style={{ justifyContent: 'flex-start', fontSize: '0.775rem', padding: '0.4rem 0.6rem' }}
              >
                Export as CSV
              </button>
              <button
                onClick={() => { onExport('json'); setShowExportMenu(false); }}
                className="btn-ghost w-full"
                style={{ justifyContent: 'flex-start', fontSize: '0.775rem', padding: '0.4rem 0.6rem' }}
              >
                Export as JSON
              </button>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          className="btn-ghost"
          style={{ padding: '0.45rem' }}
          title={isDark ? "Switch to Light Mode" : "Switch to Dark Mode"}
        >
          {isDark ? <Sun size={15} /> : <Moon size={15} />}
        </button>
      </div>
    </header>
  );
};
