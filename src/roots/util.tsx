import React from 'react';
import { createRoot } from 'react-dom/client';

import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { InitialDataProvider } from '../contexts/InitialDataProvider';

// DRY up createRoot usage. Reads initial data from data attributes on the root div.
export const createReactRoot = (ComponentClass: React.ComponentType) => {
  const initializeRoot = () => {
    const rootElement = document.getElementById('root');

    if (!rootElement) {
      throw new Error(`Root element with id "root" not found`);
    }

    const initialData = rootElement.dataset.initial;
    const data = initialData ? JSON.parse(initialData) : {};

    const component = React.createElement(ComponentClass);

    return createRoot(rootElement).render(
      <React.StrictMode>
        <ErrorBoundary>
          <InitialDataProvider data={data}>{component}</InitialDataProvider>
        </ErrorBoundary>
      </React.StrictMode>
    );
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeRoot);
  } else {
    initializeRoot();
  }
};
