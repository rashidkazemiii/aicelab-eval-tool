import { useState } from 'react';

export const useFileUpload = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (selectedFile) => {
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      // We ensure it returns TRUE only if status is success
      if (data.status === "success") {
        return true;
      } 
      return false;
      
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  return { handleUpload, loading, error };
};