import MagicString from 'magic-string';

/**
 * Vite plugin to resolve Rollup entry points as URLs
 * Allows importing entry points defined in rollupOptions.input as URLs
 * Useful for worklets, workers, or any code that needs the URL of a built entry
 */

export function entryUrlPlugin() {
  let config;
  let server;

  return {
    name: 'entry-url',

    configResolved(resolvedConfig) {
      config = resolvedConfig;
    },

    configureServer(_server) {
      server = _server;
    },

    transform(code, _id) {
      // Look for imports with ?entry-url
      if (!code.includes('?entry-url')) return null;

      const importRegex =
        /import\s+(\w+)\s+from\s+['"]([^'"]+)\?entry-url['"]/g;
      const matches = [...code.matchAll(importRegex)];

      if (matches.length === 0) return null;

      const s = new MagicString(code);

      for (const match of matches) {
        const [fullMatch, varName, importPath] = match;
        const start = match.index;
        const end = start + fullMatch.length;

        if (config.command === 'serve') {
          // In dev, convert relative path to full Vite dev server URL
          const absolutePath = importPath.startsWith('./')
            ? `/src/audio/${importPath.slice(2)}`
            : importPath;

          // Get actual server URL dynamically
          let host = 'localhost';
          let port = 5173;
          let protocol = 'http';

          if (server) {
            // Handle different host configurations
            const serverHost = server.config.server.host;
            if (serverHost === true || serverHost === '0.0.0.0') {
              host = 'localhost'; // Use localhost for worklet access even if server binds to 0.0.0.0
            } else if (serverHost && serverHost !== 'localhost') {
              host = serverHost;
            }

            port = server.config.server.port || 5173;
            protocol = server.config.server.https ? 'https' : 'http';
          }

          const devServerUrl = `${protocol}://${host}:${port}${absolutePath}`;
          s.overwrite(start, end, `const ${varName} = '${devServerUrl}';`);
        } else {
          // In production, create a unique placeholder
          const fileName = importPath
            .split('/')
            .pop()
            .replace(/\.(ts|tsx|js|jsx)$/, '');
          s.overwrite(
            start,
            end,
            `const ${varName} = "__ENTRY_URL_FOR_${fileName}__";`
          );
        }
      }

      return {
        code: s.toString(),
        map: s.generateMap({ hires: true }),
      };
    },

    generateBundle(options, bundle) {
      // Replace our placeholders with actual URLs in all chunks
      for (const [_, chunk] of Object.entries(bundle)) {
        if (chunk.type === 'chunk' && chunk.code.includes('__ENTRY_URL_FOR_')) {
          const regex = /"__ENTRY_URL_FOR_([a-zA-Z0-9_-]+)__"/g;

          chunk.code = chunk.code.replace(regex, (match, entryName) => {
            // Find the chunk that corresponds to this entry name
            for (const [chunkFileName, chunkInfo] of Object.entries(bundle)) {
              if (
                chunkInfo.type === 'chunk' &&
                chunkInfo.isEntry &&
                chunkInfo.name === entryName
              ) {
                return `"${config.base}${chunkFileName}"`;
              }
            }

            // Fallback
            console.warn(`Could not find chunk for entry: ${entryName}`);
            return `"${config.base}assets/${entryName}.js"`;
          });
        }
      }
    },
  };
}
