import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { GreetingList } from './GreetingList';

describe('GreetingList', () => {
  it('renders greetings', () => {
    const greetings = [
      {
        id: '1',
        message: 'Hello from CodeLeash!',
        created_at: '2026-01-01T00:00:00Z',
      },
      { id: '2', message: 'Welcome!', created_at: '2026-01-02T00:00:00Z' },
    ];

    render(<GreetingList greetings={greetings} />);

    expect(screen.getByText('Hello from CodeLeash!')).toBeDefined();
    expect(screen.getByText('Welcome!')).toBeDefined();
  });

  it('shows empty state when no greetings', () => {
    render(<GreetingList greetings={[]} />);

    expect(screen.getByText('No greetings yet.')).toBeDefined();
  });
});
