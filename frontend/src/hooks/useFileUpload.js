import { useState } from 'react';
import { uploadFile } from '../services/api';
import { useData } from '../context/DataContext';

export const useFileUpload = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { setAnalysisData } = useData();

  const handleUpload = async (file) => {
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // 2. Send it to Python
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
  
      if (!response.ok) throw new Error('Failed to connect to server');
  
      const data = await response.json();
      return true; // Tells UploadPage that success = true
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { handleUpload, loading, error };
};