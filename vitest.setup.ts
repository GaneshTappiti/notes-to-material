import '@testing-library/jest-dom/vitest';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Global mocks that are noisy / heavy
vi.mock('@react-pdf/renderer', () => ({
	Document: ({ children }: any) => children,
	Page: ({ children }: any) => children,
	pdf: () => ({ toBlob: () => Promise.resolve(new Blob()) })
}));

afterEach(() => {
	cleanup();
});
