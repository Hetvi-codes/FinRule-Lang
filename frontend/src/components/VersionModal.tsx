import React, { useState } from 'react';
import { X, History, RotateCcw, Clock, FileCode } from 'lucide-react';
import { ModelVersion } from '../api/client';

interface VersionModalProps {
  isOpen: boolean;
  onClose: () => void;
  versions: ModelVersion[];
  onRestore: (versionId: string) => void;
}

export const VersionModal: React.FC<VersionModalProps> = ({
  isOpen,
  onClose,
  versions,
  onRestore
}) => {
  const [selectedVersionId, setSelectedVersionId] = useState<string>(versions[0]?.id || '');

  if (!isOpen) return null;

  const activeVersion = versions.find(v => v.id === selectedVersionId) || versions[0];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '1.5rem'
    }}>
      <div className="glass-panel" style={{
        width: '840px',
        maxWidth: '95vw',
        height: '560px',
        maxHeight: '85vh',
        borderRadius: '0.75rem',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 24px 60px rgba(0,0,0,0.6)'
      }}>
        {/* Header */}
        <div style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-card)'
        }}>
          <div className="flex items-center gap-2">
            <History size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-main)' }}>
              Model Version History
            </span>
            <span className="badge badge-cyan" style={{ fontSize: '0.675rem' }}>
              {versions.length} Snapshots
            </span>
          </div>

          <button onClick={onClose} className="btn-ghost" style={{ padding: '0.35rem' }}>
            <X size={16} />
          </button>
        </div>

        {/* Content: Left list, Right preview */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Left: Snapshots list */}
          <div style={{
            width: '320px',
            borderRight: '1px solid var(--border-color)',
            overflowY: 'auto',
            padding: '0.75rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.4rem'
          }}>
            {versions.length === 0 ? (
              <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                No version history recorded yet.
              </div>
            ) : (
              versions.map((ver, idx) => {
                const isSelected = ver.id === (activeVersion?.id);
                return (
                  <div
                    key={ver.id || idx}
                    onClick={() => setSelectedVersionId(ver.id)}
                    style={{
                      padding: '0.65rem',
                      borderRadius: '0.45rem',
                      border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-color)',
                      background: isSelected ? 'var(--accent-cyan-light)' : 'var(--bg-card)',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.25rem',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span style={{ fontWeight: 600, fontSize: '0.8rem', color: isSelected ? 'var(--text-main)' : 'var(--text-muted)' }}>
                        {ver.commit_message || `Snapshot ${versions.length - idx}`}
                      </span>
                      {idx === 0 && (
                        <span className="badge badge-emerald" style={{ fontSize: '0.6rem' }}>
                          Current
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5" style={{ fontSize: '0.675rem', color: 'var(--text-dim)' }}>
                      <Clock size={11} />
                      <span>{ver.created_at ? new Date(ver.created_at).toLocaleString() : 'Just now'}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Right: Code snapshot preview & restore button */}
          {activeVersion && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1rem' }}>
              <div className="flex items-center justify-between" style={{ marginBottom: '0.75rem' }}>
                <div>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>
                    {activeVersion.commit_message || 'Snapshot'}
                  </span>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                    Created at {new Date(activeVersion.created_at).toLocaleString()}
                  </div>
                </div>

                <button
                  onClick={() => {
                    if (confirm('Restore this version into the editor? Current uncommitted changes will be replaced.')) {
                      onRestore(activeVersion.id);
                      onClose();
                    }
                  }}
                  className="btn-primary"
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                >
                  <RotateCcw size={13} />
                  <span>Restore Snapshot</span>
                </button>
              </div>

              {/* Code Preview */}
              <div style={{
                flex: 1,
                background: '#070a12',
                borderRadius: '0.5rem',
                border: '1px solid var(--border-color)',
                padding: '0.75rem 1rem',
                overflowY: 'auto',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem',
                color: '#38bdf8',
                whiteSpace: 'pre'
              }}>
                {activeVersion.source_code}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
