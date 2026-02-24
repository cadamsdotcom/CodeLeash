import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useInitialData } from '../hooks/useInitialData';

import Index from './Index';

vi.mock('../hooks/useInitialData', () => ({
  useInitialData: vi.fn(),
}));

describe('Index page', () => {
  it('renders greetings when provided via useInitialData', () => {
    const mockUseInitialData = vi.mocked(useInitialData);
    mockUseInitialData.mockReturnValue({
      greetings: [
        {
          id: '1',
          message: 'Hello from CodeLeash!',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
    });

    render(<Index />);

    expect(screen.getByText('CodeLeash')).toBeDefined();
    expect(screen.getByText('Hello from CodeLeash!')).toBeDefined();
  });

  it('renders empty state when no greetings provided', () => {
    const mockUseInitialData = vi.mocked(useInitialData);
    mockUseInitialData.mockReturnValue({ greetings: [] });

    render(<Index />);

    expect(screen.getByText('CodeLeash')).toBeDefined();
    expect(screen.getByText('No greetings yet.')).toBeDefined();
  });
});
