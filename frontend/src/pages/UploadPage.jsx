import React, { useState } from 'react';

// Minimal upload page skeleton. Uses the backend /api/uploads endpoint.
// TODO: Add better styling / progress feedback, error handling, multiple files, etc.
export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setResult(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${backendUrl}/api/uploads`, {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      const json = await res.json();
      setResult(json);
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h1>Upload File</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          disabled={loading}
        />
        <button type="submit" disabled={!file || loading} style={{ marginLeft: '1rem' }}>
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </form>
      {result && (
        <pre style={{ background: '#f5f5f5', padding: '1rem', marginTop: '1rem' }}>
{JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
