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
      const response = await uploadFile(formData);
      // Assuming your FastAPI returns { status: 'success', zeit: [...], ... }
      if (response.data.status === 'success') {
        setAnalysisData({
          zeit: response.data.zeit,
          raw: response.data.cof_raw,
          filtered: response.data.cof_filtered,
          fileName: file.name
        });
        return true;
      }
    } catch (err) {
      setError("Communication failed. Is the Python server running on port 8000?");
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { handleUpload, loading, error };
};