import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function UploadStatusViewer({ uploadId, onClose }) {
  const [uploadStatus, setUploadStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { token } = useAuth();

  useEffect(() => {
    if (!uploadId) return;

    const fetchUploadStatus = async () => {
      try {
        const response = await fetch(`/api/uploads/${uploadId}/status`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) throw new Error('Failed to fetch upload status');

        const data = await response.json();
        setUploadStatus(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUploadStatus();

    // Poll for updates every 2 seconds if upload is in progress
    const interval = setInterval(() => {
      if (uploadStatus?.status === 'processing' || uploadStatus?.status === 'uploading') {
        fetchUploadStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [uploadId, token, uploadStatus?.status]);

  if (loading) {
    return (
      <div className="upload-status-modal">
        <div className="upload-status-content">
          <div className="loading-spinner">Loading upload status...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="upload-status-modal">
        <div className="upload-status-content">
          <div className="error">Error: {error}</div>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#28a745';
      case 'failed': return '#dc3545';
      case 'processing': return '#ffc107';
      case 'uploading': return '#17a2b8';
      default: return '#6c757d';
    }
  };

  const getProgressPercentage = () => {
    if (!uploadStatus) return 0;

    const stages = ['uploading', 'processing', 'completed'];
    const currentStageIndex = stages.indexOf(uploadStatus.status);

    if (currentStageIndex === -1) return 0;
    if (uploadStatus.status === 'completed') return 100;

    // Base progress on current stage
    const baseProgress = (currentStageIndex / stages.length) * 100;

    // Add detailed progress within current stage if available
    if (uploadStatus.progress) {
      const stageProgress = (uploadStatus.progress / stages.length);
      return Math.min(baseProgress + stageProgress, 100);
    }

    return baseProgress;
  };

  return (
    <div className="upload-status-modal">
      <div className="upload-status-content">
        <div className="upload-status-header">
          <h3>Upload Status</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="upload-details">
          <div className="upload-info">
            <p><strong>File:</strong> {uploadStatus?.filename || 'Unknown'}</p>
            <p><strong>Size:</strong> {uploadStatus?.fileSize ? `${(uploadStatus.fileSize / 1024 / 1024).toFixed(2)} MB` : 'Unknown'}</p>
            <p><strong>Upload ID:</strong> {uploadId}</p>
          </div>

          <div className="status-indicator">
            <div
              className="status-badge"
              style={{ backgroundColor: getStatusColor(uploadStatus?.status) }}
            >
              {uploadStatus?.status?.toUpperCase() || 'UNKNOWN'}
            </div>
          </div>
        </div>

        <div className="progress-section">
          <div className="progress-bar-container">
            <div
              className="progress-bar"
              style={{
                width: `${getProgressPercentage()}%`,
                backgroundColor: getStatusColor(uploadStatus?.status)
              }}
            />
          </div>
          <div className="progress-text">
            {getProgressPercentage().toFixed(0)}% Complete
          </div>
        </div>

        <div className="upload-stages">
          <div className={`stage ${uploadStatus?.status === 'uploading' ? 'active' : uploadStatus?.status ? 'completed' : ''}`}>
            <div className="stage-icon">📤</div>
            <div className="stage-info">
              <h4>Uploading</h4>
              <p>File transfer in progress</p>
              {uploadStatus?.uploadProgress && (
                <div className="stage-progress">{uploadStatus.uploadProgress}%</div>
              )}
            </div>
          </div>

          <div className={`stage ${uploadStatus?.status === 'processing' ? 'active' : (uploadStatus?.status === 'completed' || uploadStatus?.status === 'failed') ? 'completed' : ''}`}>
            <div className="stage-icon">⚙️</div>
            <div className="stage-info">
              <h4>Processing</h4>
              <p>Extracting content and generating embeddings</p>
              {uploadStatus?.processingStep && (
                <div className="stage-substep">{uploadStatus.processingStep}</div>
              )}
            </div>
          </div>

          <div className={`stage ${uploadStatus?.status === 'completed' ? 'active completed' : uploadStatus?.status === 'failed' ? 'failed' : ''}`}>
            <div className="stage-icon">{uploadStatus?.status === 'failed' ? '❌' : '✅'}</div>
            <div className="stage-info">
              <h4>{uploadStatus?.status === 'failed' ? 'Failed' : 'Completed'}</h4>
              <p>{uploadStatus?.status === 'failed' ? 'Upload processing failed' : 'File ready for use'}</p>
              {uploadStatus?.error && (
                <div className="error-details">{uploadStatus.error}</div>
              )}
            </div>
          </div>
        </div>

        {uploadStatus?.metadata && (
          <div className="upload-metadata">
            <h4>Processing Details</h4>
            <div className="metadata-grid">
              {uploadStatus.metadata.pages && (
                <div className="metadata-item">
                  <span className="label">Pages:</span>
                  <span className="value">{uploadStatus.metadata.pages}</span>
                </div>
              )}
              {uploadStatus.metadata.processingTime && (
                <div className="metadata-item">
                  <span className="label">Processing Time:</span>
                  <span className="value">{uploadStatus.metadata.processingTime}s</span>
                </div>
              )}
              {uploadStatus.metadata.embeddings && (
                <div className="metadata-item">
                  <span className="label">Embeddings Generated:</span>
                  <span className="value">{uploadStatus.metadata.embeddings}</span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="upload-actions">
          {uploadStatus?.status === 'completed' && (
            <button className="btn btn-primary">View Content</button>
          )}
          {uploadStatus?.status === 'failed' && (
            <button className="btn btn-secondary">Retry Upload</button>
          )}
          <button className="btn btn-outline" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
