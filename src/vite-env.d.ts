/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly SENTRY_DSN?: string;
  readonly MODE: string; // Vite's built-in mode: 'development', 'production', etc.
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
