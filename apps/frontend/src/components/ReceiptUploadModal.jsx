import React, { useState } from 'react';

export default function ReceiptUploadModal({ isOpen, onClose }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [blobUrl, setBlobUrl] = useState(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const res = await fetch("/api/v1/uploads/receipt", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      setBlobUrl(data.blob_url);
    } catch (err) {
      console.error("Upload error:", err);
    } finally {
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
          <button className="btn-icon-pill btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '12px' }} onClick={handleUpload} disabled={uploading}>
            {uploading ? "Uploading to Azure Container..." : "⚡ Upload File"}
          </button>
        )}

        {blobUrl && (
          <div style={{ marginTop: '20px', padding: '12px', background: 'rgba(0,230,118,0.1)', border: '1px solid rgba(0,230,118,0.3)', borderRadius: '8px', fontSize: '0.85rem' }}>
            <div style={{ fontWeight: 700, color: 'var(--accent-green)' }}>✅ File Uploaded to Azure Blob Storage</div>
            <a href={blobUrl} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-cyan)', wordBreak: 'break-all' }}>{blobUrl}</a>
          </div>
        )}
      </div>
    </div>
  );
}
