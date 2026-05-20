import { useState } from 'react';
import { useData } from '../context/DataContext';
import { uploadFile, calculate } from '../services/api';

export const useFileUpload = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const { setFileName }       = useData();

  const handleUpload = async (file, dataType = 'OFT') => {
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);

      await uploadFile(formData, dataType);
      await calculate();

      setFileName(file.name);
      return true;
    } catch (err) {
      setError(err?.response?.data?.error || err.message || 'Upload failed');
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { handleUpload, loading, error };
};
