import { useContext } from 'react';

import {
  InitialDataContext,
  InitialData,
} from '../contexts/InitialDataContext';

// Hook to use the initial data
export const useInitialData = <T = InitialData>(): T => {
  const context = useContext(InitialDataContext);

  if (context === undefined) {
    throw new Error(
      'useInitialData must be used within an InitialDataProvider'
    );
  }

  return context as T;
};
