import React, { useState, useEffect, useRef } from 'react';
import { X, Sparkles, Building2, TrendingUp, FileCode, Check } from 'lucide-react';

interface CreateModelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string, templateType: 'loan' | 'growth' | 'blank') => void;
}

export const CreateModelModal: React.FC<CreateModelModalProps> = ({
  isOpen,
  onClose,
  onCreate
}) => {
  const [modelName, setModelName] = useState('Loan Eligibility & Underwriting');
  const [selectedType, setSelectedType] = useState<'loan' | 'growth' | 'blank'>('loan');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.select(), 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!modelName.trim()) return;
    onCreate(modelName.trim(), selectedType);
    onClose();
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
        width: '520px',
        maxWidth: '95vw',
        borderRadius: '0.75rem',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: '0 24px 60px rgba(0,0,0,0.6)',
        border: '1px solid var(--border-color)',
        background: 'var(--bg-card)'
      }}>
        {/* Header */}
        <div style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-sidebar)'
        }}>
          <div className="flex items-center gap-2">
            <div style={{
              width: '26px',
              height: '26px',
              borderRadius: '6px',
              background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Sparkles size={14} color="#ffffff" />
            </div>
            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)' }}>
              Create New Financial Model
            </span>
          </div>

          <button onClick={onClose} className="btn-ghost" style={{ padding: '0.35rem' }}>
            <X size={16} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Model Name */}
          <div>
            <label style={{ fontSize: '0.775rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.35rem' }}>
              Model Name
            </label>
            <input
              ref={inputRef}
              type="text"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="e.g. Home Loan Eligibility, Crypto APY Simulator"
              required
              style={{
                width: '100%',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-color)',
                borderRadius: '0.45rem',
                padding: '0.55rem 0.75rem',
                fontSize: '0.85rem',
                color: 'var(--text-main)',
                outline: 'none',
                fontFamily: 'inherit'
              }}
            />
          </div>

          {/* Starter Boilerplate Selector */}
          <div>
            <label style={{ fontSize: '0.775rem', fontWeight: 600, color: 'var(--text-dim)', display: 'block', marginBottom: '0.45rem' }}>
              Choose Starter Boilerplate
            </label>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
              {/* Option 1: Loan & Banking */}
              <div
                onClick={() => setSelectedType('loan')}
                style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: '0.5rem',
                  border: selectedType === 'loan' ? '1px solid var(--accent-emerald)' : '1px solid var(--border-color)',
                  background: selectedType === 'loan' ? 'var(--accent-emerald-light)' : 'var(--bg-input)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.15s ease'
                }}
              >
                <div className="flex items-center gap-2.5">
                  <Building2 size={16} color="var(--accent-emerald)" />
                  <div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)' }}>
                      Loan & Banking Amortization
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                      Pre-wired with loan amount, interest PMT, and monthly principal schedule.
                    </div>
                  </div>
                </div>
                {selectedType === 'loan' && <Check size={15} color="var(--accent-emerald)" />}
              </div>

              {/* Option 2: Business Growth */}
              <div
                onClick={() => setSelectedType('growth')}
                style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: '0.5rem',
                  border: selectedType === 'growth' ? '1px solid var(--accent-emerald)' : '1px solid var(--border-color)',
                  background: selectedType === 'growth' ? 'var(--accent-emerald-light)' : 'var(--bg-input)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.15s ease'
                }}
              >
                <div className="flex items-center gap-2.5">
                  <TrendingUp size={16} color="var(--accent-cyan)" />
                  <div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)' }}>
                      Revenue & Growth Projection
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                      Pre-wired with compounding monthly growth, expense deduction, and net profit.
                    </div>
                  </div>
                </div>
                {selectedType === 'growth' && <Check size={15} color="var(--accent-emerald)" />}
              </div>

              {/* Option 3: Blank Model */}
              <div
                onClick={() => setSelectedType('blank')}
                style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: '0.5rem',
                  border: selectedType === 'blank' ? '1px solid var(--accent-emerald)' : '1px solid var(--border-color)',
                  background: selectedType === 'blank' ? 'var(--accent-emerald-light)' : 'var(--bg-input)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'all 0.15s ease'
                }}
              >
                <div className="flex items-center gap-2.5">
                  <FileCode size={16} color="var(--accent-amber)" />
                  <div>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)' }}>
                      Minimal Blank Model
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                      Clean slate with basic loop structure ready for custom formulas.
                    </div>
                  </div>
                </div>
                {selectedType === 'blank' && <Check size={15} color="var(--accent-emerald)" />}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button type="button" onClick={onClose} className="btn-secondary" style={{ fontSize: '0.8rem' }}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" style={{ fontSize: '0.8rem', padding: '0.45rem 1rem' }}>
              Create Model
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
