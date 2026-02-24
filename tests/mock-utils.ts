import { vi } from 'vitest';

export const createMockResponse = (data: unknown, ok = true, status = 200) => {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(),
    redirected: false,
    statusText: ok ? 'OK' : 'Error',
    type: 'basic' as Response['type'],
    url: '',
    clone: vi.fn(),
    body: null,
    bodyUsed: false,
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    bytes: () => Promise.resolve(new Uint8Array()),
  } as Response);
};

export const createFetchMock = (responseMap: Record<string, unknown> = {}) => {
  return vi.fn().mockImplementation((url: string | URL | Request) => {
    const urlString =
      typeof url === 'string' ? url : url instanceof URL ? url.href : url.url;

    // Handle relative URLs by converting to absolute
    const absoluteUrl = urlString.startsWith('/')
      ? `http://localhost:8000${urlString}`
      : urlString;

    // Check if we have a specific mock for this URL
    for (const [pattern, response] of Object.entries(responseMap)) {
      if (absoluteUrl.includes(pattern)) {
        return typeof response === 'function'
          ? (response as () => Promise<Response>)()
          : createMockResponse(response);
      }
    }

    // If no specific mock found, throw an error to be explicit about unmocked calls
    throw new Error(`Unmocked fetch call to: ${absoluteUrl}`);
  });
};

// Common mock data factories
export const mockFactories = {
  documents: () => [],
  projectHistory: () =>
    createMockResponse({
      entries: [],
      total_count: 0,
      page: 1,
      page_size: 20,
      has_next: false,
    }),
  projectHistoryStats: () =>
    createMockResponse({
      total_actions: 0,
      action_type_counts: [],
      user_activity: [],
      recent_activity_count: 0,
    }),
  actionTypes: () => createMockResponse([]),
};

// Preset mock configurations for common test scenarios
export const presetMocks = {
  historyScreen: {
    '/api/history/project/project-123': mockFactories.projectHistory,
    '/api/history/project/project-123/statistics':
      mockFactories.projectHistoryStats,
    '/api/history/action-types': mockFactories.actionTypes,
  },
};
