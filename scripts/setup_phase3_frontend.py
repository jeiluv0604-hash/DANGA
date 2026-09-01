# -*- coding: utf-8 -*-
import os

files = {}

# 1. package.json
files['apps/frontend/package.json'] = """{
  "name": "damga-ops-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "lucide-react": "^1.16.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "recharts": "^2.12.7"
  },
  "devDependencies": {
    "@playwright/test": "^1.45.0",
    "@testing-library/jest-dom": "^6.4.6",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "jsdom": "^24.1.0",
    "typescript": "~5.5.3",
    "vite": "^5.3.4",
    "vitest": "^2.0.4"
  }
}
"""

# 2. tsconfig.json
files['apps/frontend/tsconfig.json'] = """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": false,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src", "tests"]
}
"""

# 3. vite.config.ts
files['apps/frontend/vite.config.ts'] = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
"""

# 4. vitest.config.ts
files['apps/frontend/vitest.config.ts'] = """import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
  },
});
"""

# 5. playwright.config.ts
files['apps/frontend/playwright.config.ts'] = """import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'tablet',
      use: { ...devices['iPad (gen 7)'], viewport: { width: 820, height: 1180 } },
    },
  ],
});
"""

# 6. index.html
files['apps/frontend/index.html'] = """<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DAMGA-OPS | 담가화로 경영자동화 Cockpit</title>
  </head>
  <body class="bg-slate-950 text-slate-100 antialiased selection:bg-amber-500 selection:text-black">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

# 7. setup.ts
files['apps/frontend/tests/setup.ts'] = """import '@testing-library/jest-dom';
"""

# 8. src/index.css
files['apps/frontend/src/index.css'] = """/* Modern Executive Dark Theme for DAMGA-OPS CEO Cockpit */
:root {
  --bg-main: #090d16;
  --bg-card: #131b2e;
  --bg-card-hover: #1b2640;
  --bg-card-accent: #1e293b;
  --border-subtle: #23314e;
  --border-strong: #3b82f6;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent-gold: #f59e0b;
  --accent-blue: #38bdf8;
  --status-critical: #ef4444;
  --status-high: #f97316;
  --status-medium: #eab308;
  --status-ok: #10b981;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: var(--bg-main);
  color: var(--text-primary);
  min-height: 100vh;
  line-height: 1.5;
}

button {
  cursor: pointer;
  border: none;
  background: none;
  font-family: inherit;
}

input, select {
  font-family: inherit;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #0b1120;
}
::-webkit-scrollbar-thumb {
  background: #23314e;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #3b82f6;
}

/* Utility Animations */
@keyframes pulse-subtle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.animate-pulse-subtle {
  animation: pulse-subtle 2s infinite ease-in-out;
}
"""

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print(f"Successfully generated {len(files)} base frontend configuration files.")

