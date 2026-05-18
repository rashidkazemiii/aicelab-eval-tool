import React, { createContext, useState, useContext } from 'react';

const DataContext = createContext();

export const DataProvider = ({ children }) => {

  // Recharts needs an array of objects
  const [analysisData, setAnalysisData] = useState([]);
  const [fileName, setFileName] = useState('');

  return (
    <DataContext.Provider value={{ analysisData, setAnalysisData, fileName, setFileName }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => useContext(DataContext);