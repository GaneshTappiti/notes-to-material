import React, { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import UploadStatusViewer from '../components/UploadStatusViewer';

export default function UploadPage() {
  const [files, setFiles] = useState([]);
  const [uploads, setUploads] = useState(new Map());
  const [selectedUpload, setSelectedUpload] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const { token } = useAuth();
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  const handleFileSelect = (selectedFiles) => {
    const newFiles = Array.from(selectedFiles).map(file => ({
      id: Date.now() + Math.random(),
      file,
      status: 'pending',
      progress: 0,
      uploadId: null
    }));
    setFiles(prev => [...prev, ...newFiles]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFileSelect(droppedFiles);
    }
  };

  const uploadFile = async (fileItem) => {
    const formData = new FormData();
    formData.append('file', fileItem.file);

    // Update file status to uploading
    setFiles(prev => prev.map(f =>
      f.id === fileItem.id ? { ...f, status: 'uploading', progress: 0 } : f
    ));

    try {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 100;
          setFiles(prev => prev.map(f =>
            f.id === fileItem.id ? { ...f, progress } : f
          ));
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          setFiles(prev => prev.map(f =>
            f.id === fileItem.id ? {
              ...f,
              status: 'completed',
              progress: 100,
              uploadId: response.upload_id || response.id,
              result: response
            } : f
          ));
        } else {
          setFiles(prev => prev.map(f =>
            f.id === fileItem.id ? {
              ...f,
              status: 'failed',
              error: `Upload failed: ${xhr.status}`
            } : f
          ));
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        setFiles(prev => prev.map(f =>
          f.id === fileItem.id ? {
            ...f,
            status: 'failed',
            error: 'Upload failed: Network error'
          } : f
        ));
      });

      // Send the request
      xhr.open('POST', `${backendUrl}/api/uploads`);
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.send(formData);

    } catch (error) {
      setFiles(prev => prev.map(f =>
        f.id === fileItem.id ? {
          ...f,
          status: 'failed',
          error: error.message
        } : f
      ));
    }
  };

  const uploadAllFiles = () => {
    files.filter(f => f.status === 'pending').forEach(uploadFile);
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status !== 'completed' && f.status !== 'failed'));
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'uploading': return '📤';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return '#6c757d';
      case 'uploading': return '#17a2b8';
      case 'completed': return '#28a745';
      case 'failed': return '#dc3545';
      default: return '#6c757d';
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-header">
        <h1>Upload Files</h1>
        <div className="upload-stats">
          <span>Total: {files.length}</span>
          <span>Pending: {files.filter(f => f.status === 'pending').length}</span>
          <span>Uploading: {files.filter(f => f.status === 'uploading').length}</span>
          <span>Completed: {files.filter(f => f.status === 'completed').length}</span>
          <span>Failed: {files.filter(f => f.status === 'failed').length}</span>
        </div>
      </div>

      <div
        className={`upload-dropzone ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="dropzone-content">
          <div className="dropzone-icon">📁</div>
          <h3>Drop files here or click to browse</h3>
          <p>Supports PDF, DOC, DOCX, TXT files</p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt"
            onChange={(e) => handleFileSelect(e.target.files)}
            style={{ display: 'none' }}
          />
        </div>
      </div>

      {files.length > 0 && (
        <div className="upload-controls">
          <button
            className="btn btn-primary"
            onClick={uploadAllFiles}
            disabled={files.filter(f => f.status === 'pending').length === 0}
          >
            Upload All ({files.filter(f => f.status === 'pending').length})
          </button>
          <button
            className="btn btn-secondary"
            onClick={clearCompleted}
            disabled={files.filter(f => f.status === 'completed' || f.status === 'failed').length === 0}
          >
            Clear Completed
          </button>
        </div>
      )}

      <div className="upload-list">
        {files.map((fileItem) => (
          <div key={fileItem.id} className="upload-item">
            <div className="file-info">
              <div className="file-icon">{getStatusIcon(fileItem.status)}</div>
              <div className="file-details">
                <div className="file-name">{fileItem.file.name}</div>
                <div className="file-meta">
                  {(fileItem.file.size / 1024 / 1024).toFixed(2)} MB
                  <span
                    className="file-status"
                    style={{ color: getStatusColor(fileItem.status) }}
                  >
                    {fileItem.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            <div className="upload-progress">
              {fileItem.status === 'uploading' && (
                <div className="progress-bar-container">
                  <div
                    className="progress-bar"
                    style={{
                      width: `${fileItem.progress}%`,
                      backgroundColor: getStatusColor(fileItem.status)
                    }}
                  />
                  <span className="progress-text">{fileItem.progress.toFixed(0)}%</span>
                </div>
              )}
              {fileItem.error && (
                <div className="error-message">{fileItem.error}</div>
              )}
            </div>

            <div className="upload-actions">
              {fileItem.status === 'pending' && (
                <button className="btn btn-sm" onClick={() => uploadFile(fileItem)}>
                  Upload
                </button>
              )}
              {fileItem.uploadId && (
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => setSelectedUpload(fileItem.uploadId)}
                >
                  View Status
                </button>
              )}
              <button
                className="btn btn-sm btn-danger"
                onClick={() => removeFile(fileItem.id)}
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedUpload && (
        <UploadStatusViewer
          uploadId={selectedUpload}
          onClose={() => setSelectedUpload(null)}
        />
      )}
    </div>
  );
}
