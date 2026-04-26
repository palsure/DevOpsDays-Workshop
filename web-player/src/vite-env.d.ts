/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  /** When true, metrics are not POSTed (CI / device farm probes). */
  readonly VITE_QOE_SILENT: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
