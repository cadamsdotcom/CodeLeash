import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

import { entryUrlPlugin } from './vite-plugin-entry-url.js';

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const plugins = [react(), entryUrlPlugin()];

  return {
    plugins,

    base: command === 'build' ? '/dist/' : '/',
    build: {
      manifest: true,
      sourcemap: true,
      rollupOptions: {
        input: {
          main: './src/main.ts',
          app: './src/app.ts',
          index: './src/roots/index.tsx',
        },
        external: [],
      },
    },

    server: {
      host: true,
      port: parseInt(env.VITE_SERVER_PORT || '5173', 10),
      allowedHosts: true,
      cors: true,
    },
  };
});
