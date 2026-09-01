/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend API origin for production builds (empty in dev; Vite proxy handles it). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
