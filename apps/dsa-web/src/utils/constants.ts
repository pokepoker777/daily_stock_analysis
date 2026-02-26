// Vite dev proxy handles /api → backend; production is same-origin.
// Override with VITE_API_URL env var if needed.
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';
