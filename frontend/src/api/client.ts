const API_BASE = '/api';

export interface CompileResult {
  success: boolean;
  timings: Record<string, number>;
  model_name?: string;
  columns: string[];
  rows: Record<string, any>[];
  summaries: Record<string, {
    total: number;
    avg: number;
    min: number;
    max: number;
    start: number;
    end: number;
    change_pct: number;
  }>;
  scenarios: Record<string, {
    columns: string[];
    rows: Record<string, any>[];
    summaries: Record<string, any>;
  }>;
  compiler_studio?: {
    tokens: Array<{ type: string; value: any; line: number; column: number; length: number }>;
    ast: any;
    symbol_table: Array<{ name: string; type: string; scope: string; line: number; column: number }>;
    ir: Array<{ op: string; arg1: string | null; arg2: string | null; result: string | null; line: number }>;
    diagnostics: Array<{ phase: string; message: string; line: number; column: number; severity: string; suggestion?: string; snippet?: string }>;
  };
  error?: {
    phase: string;
    message: string;
    line: number;
    column: number;
    severity: string;
    suggestion?: string;
    snippet?: string;
  };
}

export interface Project {
  id: string;
  name: string;
  description: string;
  created_at?: string;
}

export interface ModelItem {
  id: string;
  project_id: string;
  name: string;
  source_code: string;
  description: string;
  updated_at?: string;
}

export interface ModelVersion {
  id: string;
  model_id: string;
  source_code: string;
  commit_message: string;
  created_at: string;
}

export interface TemplateItem {
  id: string;
  name: string;
  category: string;
  description: string;
  source_code: string;
}

export const api = {
  // Execute ModelScript
  async execute(sourceCode: string, modelId?: string, scenarioName?: string): Promise<CompileResult> {
    const res = await fetch(`${API_BASE}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_code: sourceCode,
        model_id: modelId,
        scenario_name: scenarioName
      })
    });
    return res.json();
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    return res.json();
  },

  async createProject(name: string, description: string = ''): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description })
    });
    return res.json();
  },

  async deleteProject(id: string): Promise<void> {
    await fetch(`${API_BASE}/projects/${id}`, { method: 'DELETE' });
  },

  // Models
  async getModels(projectId: string): Promise<ModelItem[]> {
    const res = await fetch(`${API_BASE}/models?project_id=${encodeURIComponent(projectId)}`);
    return res.json();
  },

  async createModel(projectId: string, name: string, sourceCode: string): Promise<ModelItem> {
    const res = await fetch(`${API_BASE}/models`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, name, source_code: sourceCode })
    });
    return res.json();
  },

  async updateModel(id: string, updates: { name?: string; source_code?: string; commit_message?: string }): Promise<ModelItem> {
    const res = await fetch(`${API_BASE}/models/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    return res.json();
  },

  async deleteModel(id: string): Promise<void> {
    await fetch(`${API_BASE}/models/${id}`, { method: 'DELETE' });
  },

  // Versions
  async getVersions(modelId: string): Promise<ModelVersion[]> {
    const res = await fetch(`${API_BASE}/models/${modelId}/versions`);
    return res.json();
  },

  async restoreVersion(modelId: string, versionId: string): Promise<ModelItem> {
    const res = await fetch(`${API_BASE}/models/${modelId}/restore/${versionId}`, {
      method: 'POST'
    });
    return res.json();
  },

  // Templates
  async getTemplates(): Promise<TemplateItem[]> {
    const res = await fetch(`${API_BASE}/templates`);
    return res.json();
  },

  async getCustomTemplates(): Promise<TemplateItem[]> {
    const res = await fetch(`${API_BASE}/templates/custom`);
    return res.json();
  },

  async createCustomTemplate(tpl: { name: string; category?: string; description?: string; source_code: string }): Promise<TemplateItem> {
    const res = await fetch(`${API_BASE}/templates/custom`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tpl)
    });
    return res.json();
  },

  async deleteCustomTemplate(templateId: string): Promise<void> {
    await fetch(`${API_BASE}/templates/custom/${templateId}`, {
      method: 'DELETE'
    });
  },

  async cloneTemplate(templateId: string, projectId: string): Promise<ModelItem> {
    const res = await fetch(`${API_BASE}/templates/${templateId}/clone?project_id=${encodeURIComponent(projectId)}`, {
      method: 'POST'
    });
    return res.json();
  },

  // Executions
  async getExecutions(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/executions`);
    return res.json();
  }
};

