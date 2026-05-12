import { useState } from 'react';
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

      // Upload file to backend
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to connect to server');
      }

      const data = await response.json();

      // Convert backend arrays into Recharts format
      const formattedData = data.zeit.map((z, i) => ({
        zeit: z,
        raw: data.cof_raw[i],
        filtered: data.cof_filtered[i],
      }));

      // Save into global context
      setAnalysisData(formattedData);

      return true;

    } catch (err) {

      setError(err.message);
      return false;

    } finally {

      setLoading(false);
    }
  };

  return {
    handleUpload,
    loading,
    error
  };
};