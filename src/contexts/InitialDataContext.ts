import { createContext } from 'react';

// Define the type for the initial data (can be customized based on your needs)
export type InitialData = Record<string, unknown>;

// Create and export the context for use in hooks
export const InitialDataContext = createContext<InitialData | undefined>(
  undefined
);
