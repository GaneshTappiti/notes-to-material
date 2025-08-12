// Simple API client for local backend
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';
const API_KEY = import.meta.env.VITE_API_KEY; // optional

function authHeaders(extra: Record<string,string> = {}) {
  return {
    ...(API_KEY ? { 'x-api-key': API_KEY } : {}),
    ...extra,
  } as Record<string,string>;
}

export interface UploadResponse { file_id: string; filename: string; pages: number; ocr_status: string }

export async function uploadFile(f: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', f);
  const res = await fetch(`${API_BASE}/uploads`, { method: 'POST', body: form, headers: authHeaders() });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

export async function getUploadStatus(file_id: string) {
  const res = await fetch(`${API_BASE}/uploads/${file_id}`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Status fetch failed');
  return res.json();
}

export async function createEmbeddings(file_id: string, pages: {page_no: number; text: string}[]) {
  const res = await fetch(`${API_BASE}/embeddings`, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify({ file_id, pages }) });
  if (!res.ok) throw new Error('Embeddings failed');
  return res.json();
}

export async function retrieve(query: string, top_k = 5) {
  const res = await fetch(`${API_BASE}/retrieve`, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify({ query, top_k }) });
  if (!res.ok) throw new Error('Retrieve failed');
  return res.json();
}

export async function generate(prompt: string, top_k = 5, marks?: number[]) {
  const res = await fetch(`${API_BASE}/generate`, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify({ prompt, top_k, marks }) });
  if (!res.ok) throw new Error('Generate failed');
  return res.json();
}

export async function getJobResults(job_id: string, page=1) {
  const res = await fetch(`${API_BASE}/jobs/${job_id}/results?page=${page}`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Results fetch failed');
  return res.json();
}

export async function regenerateItem(question: string, top_k=5, marks?: number[]) {
  const res = await fetch(`${API_BASE}/generate_item`, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify({ question, top_k, marks }) });
  if (!res.ok) throw new Error('Regenerate failed');
  return res.json();
}

export async function deleteJob(job_id: string) {
  const res = await fetch(`${API_BASE}/jobs/${job_id}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Delete job failed');
  return res.json();
}

export async function updateJobItem(job_id: string, index: number, updates: {question?: string; answers?: Record<string,string>; page_references?: string[]}) {
  const res = await fetch(`${API_BASE}/jobs/update_item`, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify({ job_id, index, ...updates }) });
  if (!res.ok) throw new Error('Update item failed');
  return res.json();
}

// Direct patch of question by id (for future per-question editing API)
export async function patchQuestion(qid: string, updates: {question?: string; answers?: Record<string,string>; page_references?: string[]; status?: string}) {
  const res = await fetch(`${API_BASE}/questions/${qid}`, { method: 'PATCH', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify(updates) });
  if (!res.ok) throw new Error('Patch question failed');
  return res.json();
}

export async function createExport(payload: { job_id: string; template: string; title?: string; footer?: string }) {
  const res = await fetch(`${API_BASE}/exports`, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }), body: JSON.stringify(payload) });
  if (!res.ok) throw new Error('Export failed');
  return res.json();
}

export async function deleteUpload(file_id: string) {
  const res = await fetch(`${API_BASE}/uploads/${file_id}`, { method: 'DELETE', headers: authHeaders() });
  if (!res.ok) throw new Error('Delete upload failed');
  return res.json();
}

export async function listJobs(page = 1, limit = 50) {
  const res = await fetch(`${API_BASE}/jobs?page=${page}&limit=${limit}`, { headers: authHeaders() });
  if (!res.ok) throw new Error('List jobs failed');
  return res.json();
}

export async function approveJobItem(job_id: string, index: number) {
  return updateJobItem(job_id, index, { /* explicit status */ } as any);
}
