import React, { useState } from 'react';
import { 
  Folder, 
  FileCode, 
  Plus, 
  Trash2, 
  ChevronRight, 
  ChevronDown, 
  Clock, 
  Sparkles, 
  PanelLeftClose, 
  PanelLeft,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { ModelItem, Project } from '../api/client';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  projects: Project[];
  currentProjectId: string;
  onSelectProject: (id: string) => void;
  models: ModelItem[];
  currentModelId: string;
  onSelectModel: (id: string) => void;
  onCreateModel: () => void;
  onDeleteModel: (id: string) => void;
  onOpenTemplates: () => void;
  executions: any[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  projects,
  currentProjectId,
  onSelectProject,
  models,
  currentModelId,
  onSelectModel,
  onCreateModel,
  onDeleteModel,
  onOpenTemplates,
  executions
}) => {
  const [activeTab, setActiveTab] = useState<'models' | 'history'>('models');

  if (!isOpen) {
    return (
      <aside style={{
        width: '42px',
        borderRight: '1px solid var(--border-color)',
        background: 'var(--bg-sidebar)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '0.75rem 0',
        gap: '0.75rem'
      }}>
        <button
          onClick={onToggle}
          className="btn-ghost"
          style={{ padding: '0.4rem' }}
          title="Expand Sidebar"
        >
          <PanelLeft size={16} />
        </button>
      </aside>
    );
  }

  const currentProject = projects.find(p => p.id === currentProjectId) || projects[0];

  return (
    <aside style={{
      width: '260px',
      borderRight: '1px solid var(--border-color)',
      background: 'var(--bg-sidebar)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      height: 'calc(100vh - 56px)',
      overflowY: 'auto'
    }}>
      {/* Sidebar Header */}
      <div style={{
        padding: '0.85rem 0.9rem',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div className="flex items-center gap-2">
          <Folder size={15} color="var(--accent-emerald)" />
          <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-main)' }}>
            {currentProject?.name || 'Models Workspace'}
          </span>
        </div>
        <button
          onClick={onToggle}
          className="btn-ghost"
          style={{ padding: '0.25rem' }}
          title="Collapse Sidebar"
        >
          <PanelLeftClose size={15} />
        </button>
      </div>

      {/* Tabs: Models vs Run History */}
      <div style={{
        display: 'flex',
        padding: '0.35rem 0.65rem',
        gap: '0.25rem',
        borderBottom: '1px solid var(--border-color)',
        background: 'rgba(0,0,0,0.1)'
      }}>
        <button
          onClick={() => setActiveTab('models')}
          style={{
            flex: 1,
            padding: '0.35rem 0',
            fontSize: '0.75rem',
            fontWeight: 600,
            borderRadius: '0.375rem',
            border: 'none',
            cursor: 'pointer',
            background: activeTab === 'models' ? 'var(--bg-card)' : 'transparent',
            color: activeTab === 'models' ? 'var(--accent-emerald)' : 'var(--text-dim)',
            transition: 'all 0.15s ease'
          }}
        >
          Models ({models.length})
        </button>
        <button
          onClick={() => setActiveTab('history')}
          style={{
            flex: 1,
            padding: '0.35rem 0',
            fontSize: '0.75rem',
            fontWeight: 600,
            borderRadius: '0.375rem',
            border: 'none',
            cursor: 'pointer',
            background: activeTab === 'history' ? 'var(--bg-card)' : 'transparent',
            color: activeTab === 'history' ? 'var(--accent-emerald)' : 'var(--text-dim)',
            transition: 'all 0.15s ease'
          }}
        >
          Run History
        </button>
      </div>

      {/* Tab Content: Models */}
      {activeTab === 'models' && (
        <div style={{ padding: '0.75rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          <div className="flex items-center justify-between" style={{ padding: '0 0.35rem 0.35rem 0.35rem' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)' }}>
              Project Models
            </span>
            <button
              onClick={onCreateModel}
              className="btn-ghost"
              style={{ padding: '0.15rem 0.35rem', fontSize: '0.75rem', color: 'var(--accent-emerald)' }}
              title="Create New Model"
            >
              <Plus size={13} />
              <span>New</span>
            </button>
          </div>

          {/* Model Items */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
            {models.map((m) => {
              const isSelected = m.id === currentModelId;
              return (
                <div
                  key={m.id}
                  onClick={() => onSelectModel(m.id)}
                  style={{
                    padding: '0.5rem 0.65rem',
                    borderRadius: '0.375rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.8125rem',
                    background: isSelected ? 'var(--accent-emerald-light)' : 'transparent',
                    border: isSelected ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid transparent',
                    color: isSelected ? 'var(--text-main)' : 'var(--text-muted)',
                    transition: 'all 0.12s ease'
                  }}
                  className="model-item-hover"
                >
                  <div className="flex items-center gap-2" style={{ overflow: 'hidden' }}>
                    <FileCode size={14} color={isSelected ? 'var(--accent-emerald)' : 'var(--text-dim)'} />
                    <span style={{ 
                      overflow: 'hidden', 
                      textOverflow: 'ellipsis', 
                      whiteSpace: 'nowrap',
                      fontWeight: isSelected ? 600 : 400
                    }}>
                      {m.name}
                    </span>
                  </div>

                  {models.length > 1 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm(`Delete model "${m.name}"?`)) {
                          onDeleteModel(m.id);
                        }
                      }}
                      className="btn-ghost"
                      style={{ padding: '0.15rem', opacity: 0.6 }}
                      title="Delete Model"
                    >
                      <Trash2 size={12} color="var(--accent-rose)" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Templates Section Card */}
          <div style={{
            marginTop: 'auto',
            padding: '0.85rem',
            background: 'var(--bg-card)',
            borderRadius: '0.5rem',
            border: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.45rem'
          }}>
            <div className="flex items-center gap-1.5">
              <Sparkles size={14} color="var(--accent-amber)" />
              <span style={{ fontWeight: 600, fontSize: '0.785rem', color: 'var(--text-main)' }}>
                Sample Templates
              </span>
            </div>
            <p style={{ fontSize: '0.7125rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
              Explore ready-to-use models: SaaS, Loan Amortization, Startup Runway, Unit Economics.
            </p>
            <button
              onClick={onOpenTemplates}
              className="btn-secondary"
              style={{ fontSize: '0.75rem', justifyContent: 'center', padding: '0.35rem 0.5rem' }}
            >
              Browse 5 Templates
            </button>
          </div>
        </div>
      )}

      {/* Tab Content: Execution History */}
      {activeTab === 'history' && (
        <div style={{ padding: '0.75rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.4rem', overflowY: 'auto' }}>
          <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)', padding: '0 0.25rem' }}>
            Past Executions
          </span>

          {executions.length === 0 ? (
            <div style={{ padding: '1.5rem 0.5rem', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.785rem' }}>
              No runs recorded yet. Click "Run Model" to execute.
            </div>
          ) : (
            executions.map((exec, idx) => (
              <div
                key={exec.id || idx}
                style={{
                  padding: '0.5rem 0.65rem',
                  borderRadius: '0.375rem',
                  background: 'var(--bg-input)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.25rem',
                  fontSize: '0.75rem'
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    {exec.success ? (
                      <CheckCircle2 size={13} color="var(--accent-emerald)" />
                    ) : (
                      <AlertCircle size={13} color="var(--accent-rose)" />
                    )}
                    <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                      {exec.scenario_name || 'Base Model'}
                    </span>
                  </div>
                  <span style={{ color: 'var(--text-dim)', fontSize: '0.675rem' }}>
                    {exec.timings?.total_ms ? `${exec.timings.total_ms}ms` : '0ms'}
                  </span>
                </div>

                <div className="flex items-center justify-between" style={{ color: 'var(--text-dim)', fontSize: '0.675rem' }}>
                  <span>{exec.row_count || 0} periods output</span>
                  <span>{exec.created_at ? new Date(exec.created_at).toLocaleTimeString() : 'Just now'}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </aside>
  );
};
