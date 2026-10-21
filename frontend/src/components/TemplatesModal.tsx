import React, { useState } from 'react';
import { X, Sparkles, Check, ArrowRight, BookOpen, Plus, Trash2, Bookmark, Code2 } from 'lucide-react';
import { TemplateItem } from '../api/client';

interface TemplatesModalProps {
  isOpen: boolean;
  onClose: () => void;
  templates: TemplateItem[];
  customTemplates: TemplateItem[];
  currentSourceCode?: string;
  currentModelName?: string;
  onSelectTemplate: (templateId: string, customItem?: TemplateItem) => void;
  onSaveCustomTemplate: (item: TemplateItem) => void;
  onDeleteCustomTemplate: (id: string) => void;
}

export const TemplatesModal: React.FC<TemplatesModalProps> = ({
  isOpen,
  onClose,
  templates,
  customTemplates,
  currentSourceCode = '',
  currentModelName = '',
  onSelectTemplate,
  onSaveCustomTemplate,
  onDeleteCustomTemplate
}) => {
  const allTemplates = [...templates, ...customTemplates];
  const [selectedId, setSelectedId] = useState<string>(allTemplates[0]?.id || '');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [isCreatingCustom, setIsCreatingCustom] = useState<boolean>(false);
  const [customName, setCustomName] = useState<string>(currentModelName || 'My Custom Model');
  const [customCategory, setCustomCategory] = useState<string>('Custom');
  const [customDesc, setCustomDesc] = useState<string>('Custom financial projection and rules model.');

  if (!isOpen) return null;

  const categories = [
    'All',
    ...(customTemplates.length > 0 ? ['My Custom Templates'] : []),
    ...Array.from(new Set(templates.map(t => t.category)))
  ];

  let filtered = allTemplates;
  if (selectedCategory === 'My Custom Templates') {
    filtered = customTemplates;
  } else if (selectedCategory !== 'All') {
    filtered = allTemplates.filter(t => t.category === selectedCategory);
  }

  const activeTemplate = allTemplates.find(t => t.id === selectedId) || filtered[0] || allTemplates[0];

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customName.trim()) return;

    const newTemplate: TemplateItem = {
      id: `custom-${Date.now()}`,
      name: customName.trim(),
      category: customCategory.trim() || 'Custom',
      description: customDesc.trim() || 'User-defined financial model',
      source_code: currentSourceCode || '// FinRule Custom Model\nmodel "Custom" {\n  output 1\n}\n'
    };

    onSaveCustomTemplate(newTemplate);
    setSelectedId(newTemplate.id);
    setSelectedCategory('My Custom Templates');
    setIsCreatingCustom(false);
  };

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
        width: '920px',
        maxWidth: '95vw',
        height: '640px',
        maxHeight: '90vh',
        borderRadius: '0.75rem',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 24px 60px rgba(0,0,0,0.6)'
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-card)'
        }}>
          <div className="flex items-center gap-2">
            <Sparkles size={18} color="var(--accent-amber)" />
            <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-main)' }}>
              Financial Model Templates Library
            </span>
            <span className="badge badge-emerald" style={{ fontSize: '0.675rem' }}>
              {templates.length} Pre-built
            </span>
            {customTemplates.length > 0 && (
              <span className="badge badge-cyan" style={{ fontSize: '0.675rem' }}>
                {customTemplates.length} Custom
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsCreatingCustom(!isCreatingCustom)}
              className="btn-secondary"
              style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem', borderColor: isCreatingCustom ? 'var(--accent-emerald)' : 'var(--border-color)' }}
            >
              <Plus size={13} color="var(--accent-emerald)" />
              <span>{isCreatingCustom ? 'Cancel New' : 'Save Current Code as Template'}</span>
            </button>
            <button onClick={onClose} className="btn-ghost" style={{ padding: '0.35rem' }}>
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Custom Template Creation Drawer */}
        {isCreatingCustom && (
          <form onSubmit={handleCreateSubmit} style={{
            background: 'var(--bg-input)',
            borderBottom: '1px solid var(--border-color)',
            padding: '0.85rem 1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.6rem'
          }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-emerald)' }}>
              Save Current Editor Code as a Reusable Template
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '0.65rem' }}>
              <div>
                <label style={{ fontSize: '0.7rem', color: 'var(--text-dim)', display: 'block', marginBottom: '0.2rem' }}>Template Name</label>
                <input
                  type="text"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  placeholder="e.g. My Custom Growth & Burn Model"
                  required
                  style={{
                    width: '100%',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '0.375rem',
                    padding: '0.35rem 0.6rem',
                    fontSize: '0.775rem',
                    color: 'var(--text-main)',
                    outline: 'none'
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.7rem', color: 'var(--text-dim)', display: 'block', marginBottom: '0.2rem' }}>Category</label>
                <input
                  type="text"
                  value={customCategory}
                  onChange={(e) => setCustomCategory(e.target.value)}
                  placeholder="e.g. Custom, Crypto, SaaS"
                  style={{
                    width: '100%',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '0.375rem',
                    padding: '0.35rem 0.6rem',
                    fontSize: '0.775rem',
                    color: 'var(--text-main)',
                    outline: 'none'
                  }}
                />
              </div>
            </div>
            <div>
              <label style={{ fontSize: '0.7rem', color: 'var(--text-dim)', display: 'block', marginBottom: '0.2rem' }}>Simple Description (What problem does it solve?)</label>
              <input
                type="text"
                value={customDesc}
                onChange={(e) => setCustomDesc(e.target.value)}
                placeholder="e.g. Calculates monthly runway and crypto staking returns"
                style={{
                  width: '100%',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '0.375rem',
                  padding: '0.35rem 0.6rem',
                  fontSize: '0.775rem',
                  color: 'var(--text-main)',
                  outline: 'none'
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.2rem' }}>
              <button type="button" onClick={() => setIsCreatingCustom(false)} className="btn-ghost" style={{ fontSize: '0.75rem' }}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" style={{ fontSize: '0.75rem', padding: '0.3rem 0.75rem' }}>
                <Check size={13} />
                <span>Save Template</span>
              </button>
            </div>
          </form>
        )}

        {/* Category Pills */}
        <div style={{
          display: 'flex',
          gap: '0.4rem',
          padding: '0.65rem 1.25rem',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-input)',
          overflowX: 'auto'
        }}>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                padding: '0.25rem 0.65rem',
                borderRadius: '9999px',
                fontSize: '0.725rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: selectedCategory === cat ? 'var(--accent-emerald)' : 'rgba(255,255,255,0.05)',
                color: selectedCategory === cat ? '#ffffff' : 'var(--text-muted)',
                transition: 'all 0.15s ease'
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Modal Body: Left List + Right Preview */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Left: Template Cards */}
          <div style={{
            width: '360px',
            borderRight: '1px solid var(--border-color)',
            overflowY: 'auto',
            padding: '0.75rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}>
            {filtered.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                No templates in this category. Click "+ Save Current Code as Template" to create one!
              </div>
            ) : (
              filtered.map(tpl => {
                const isSelected = tpl.id === selectedId;
                const isCustom = tpl.id.startsWith('custom-');
                return (
                  <div
                    key={tpl.id}
                    onClick={() => setSelectedId(tpl.id)}
                    style={{
                      padding: '0.75rem',
                      borderRadius: '0.5rem',
                      border: isSelected ? '1px solid var(--accent-emerald)' : '1px solid var(--border-color)',
                      background: isSelected ? 'var(--accent-emerald-light)' : 'var(--bg-card)',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.35rem',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: isSelected ? 'var(--text-main)' : 'var(--text-muted)' }}>
                        {tpl.name}
                      </span>
                      <div className="flex items-center gap-1">
                        <span className={`badge ${isCustom ? 'badge-amber' : 'badge-cyan'}`} style={{ fontSize: '0.625rem' }}>
                          {isCustom ? 'Custom' : tpl.category}
                        </span>
                        {isCustom && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (confirm(`Delete custom template "${tpl.name}"?`)) {
                                onDeleteCustomTemplate(tpl.id);
                              }
                            }}
                            className="btn-ghost"
                            style={{ padding: '0.2rem', color: 'var(--accent-rose)' }}
                            title="Delete custom template"
                          >
                            <Trash2 size={12} />
                          </button>
                        )}
                      </div>
                    </div>
                    <p style={{ fontSize: '0.725rem', color: 'var(--text-dim)', lineHeight: 1.35 }}>
                      {tpl.description}
                    </p>
                  </div>
                );
              })
            )}
          </div>

          {/* Right: Code Preview & Action */}
          {activeTemplate ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1rem' }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <div className="flex items-center justify-between">
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    {activeTemplate.name}
                  </h3>
                  <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>
                    {activeTemplate.category}
                  </span>
                </div>
                <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  {activeTemplate.description}
                </p>
              </div>

              {/* Source Preview */}
              <div style={{
                flex: 1,
                background: '#070a12',
                borderRadius: '0.5rem',
                border: '1px solid var(--border-color)',
                padding: '0.75rem 1rem',
                overflowY: 'auto',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem',
                color: '#a78bfa',
                whiteSpace: 'pre'
              }}>
                {activeTemplate.source_code}
              </div>

              {/* Footer Button */}
              <div style={{ marginTop: '0.85rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
                <button onClick={onClose} className="btn-secondary">
                  Cancel
                </button>
                <button
                  onClick={() => {
                    onSelectTemplate(activeTemplate.id, activeTemplate.id.startsWith('custom-') ? activeTemplate : undefined);
                    onClose();
                  }}
                  className="btn-primary"
                >
                  <span>Load into Workspace</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
              Select a template to view code
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
