import React, { useState } from 'react';
import { API_BASE_URL } from '../config';

export default function ReceiptUploadModal({ isOpen, onClose }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [blobUrl, setBlobUrl] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setBlobUrl(null);
      setErrorMsg(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setErrorMsg(null);

    try {
      // Convert file to base64 for API transfer
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          const base64Content = reader.result.split(',')[1] || reader.result;
          const res = await fetch(`${API_BASE_URL}/api/v1/uploads/receipt`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              filename: selectedFile.name,
              content_b64: base64Content,
              content_type: selectedFile.type || "application/pdf"
            })
          });

          if (!res.ok) {
            throw new Error(`Upload failed with HTTP ${res.status}`);
          }
          const data = await res.json();
          setBlobUrl(data.blob_url);
        } catch (err) {
          setErrorMsg(err.message);
        } finally {
          setUploading(false);
        }
      };
      reader.readAsDataURL(selectedFile);
    } catch (err) {
      console.error("Upload error:", err);
      setErrorMsg(err.message);
      setUploading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card glass" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="section-title">📄 Upload Receipt to Azure Blob</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="form-group">
          <label className="form-label">Select PDF Receipt or Image:</label>
          <input type="file" className="form-input" accept=".pdf,image/*" onChange={handleFileChange} />
        </div>

        {selectedFile && (
          <button 
            className="btn-icon-pill btn-primary" 
            style={{ width: '100%', justifyContent: 'center', padding: '12px' }} 
            onClick={handleUpload} 
            disabled={uploading}
          >
            {uploading ? "Uploading to Azure Storage..." : "⚡ Upload File"}
          </button>
        )}

        {errorMsg && (
          <div style={{ marginTop: '16px', padding: '10px', background: 'rgba(255, 77, 77, 0.1)', border: '1px solid rgba(255, 77, 77, 0.3)', borderRadius: '8px', color: '#ff6b6b', fontSize: '0.85rem' }}>
            ⚠️ {errorMsg}
          </div>
        )}

        {blobUrl && (
          <div style={{ marginTop: '20px', padding: '12px', background: 'rgba(0,230,118,0.1)', border: '1px solid rgba(0,230,118,0.3)', borderRadius: '8px', fontSize: '0.85rem' }}>
            <div style={{ fontWeight: 700, color: 'var(--accent-green, #00e676)' }}>✅ File Uploaded to Azure Blob Storage</div>
            <a href={blobUrl} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-cyan, #00e5ff)', wordBreak: 'break-all' }}>{blobUrl}</a>
          </div>
        )}
      </div>
    </div>
  );
}
