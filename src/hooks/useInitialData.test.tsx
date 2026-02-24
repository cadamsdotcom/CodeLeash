import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { InitialData } from '../contexts/InitialDataContext';
import { InitialDataProvider } from '../contexts/InitialDataProvider';

import { useInitialData } from './useInitialData';

interface TestData {
  greetings: { id: string; message: string }[];
}

describe('useInitialData', () => {
  it('throws when used outside InitialDataProvider', () => {
    expect(() => renderHook(() => useInitialData())).toThrow(
      'useInitialData must be used within an InitialDataProvider'
    );
  });

  it('returns typed data when inside InitialDataProvider', () => {
    const testData: TestData = {
      greetings: [{ id: '1', message: 'Hello' }],
    };

    const { result } = renderHook(() => useInitialData<TestData>(), {
      wrapper: ({ children }) => (
        <InitialDataProvider data={testData as unknown as InitialData}>
          {children}
        </InitialDataProvider>
      ),
    });

    expect(result.current.greetings).toHaveLength(1);
    expect(result.current.greetings[0]?.message).toBe('Hello');
  });
});
