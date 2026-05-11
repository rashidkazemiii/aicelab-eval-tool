import React, { createContext, useState, useContext } from 'react';

const DataContext = createContext();

export const DataProvider = ({ children }) => {
  const [analysisData, setAnalysisData] = useState({
    zeit: [],
    raw: [],
    filtered: [],
    fileName: ""
  });

  return (
    <DataContext.Provider value={{ analysisData, setAnalysisData }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => useContext(DataContext);