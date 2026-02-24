import React, { ReactNode } from 'react';

import { InitialDataContext, InitialData } from './InitialDataContext';

// Provider component props
interface InitialDataProviderProps {
  children: ReactNode;
  data: InitialData;
}

// Provider component
export const InitialDataProvider: React.FC<InitialDataProviderProps> = ({
  children,
  data,
}) => {
  return (
    <InitialDataContext.Provider value={data}>
      {children}
    </InitialDataContext.Provider>
  );
};
