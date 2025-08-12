import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Mock API layer
vi.mock('../../lib/api', () => ({
  getJobResults: vi.fn().mockResolvedValue({ results: [ { id: 'abc123', question: 'What is a stack?', answers: { '2': 'A stack is LIFO structure.' }, page_references: [] } ] }),
  regenerateItem: vi.fn().mockResolvedValue({ item: { answers: { '2': 'regen answer' } } }),
  updateJobItem: vi.fn().mockResolvedValue({ status: 'updated' }),
  patchQuestion: vi.fn().mockResolvedValue({})
}));

// Mock Seo to avoid HelmetProvider context issues in jsdom
vi.mock('@/components/Seo', () => ({ default: () => null }));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useSearchParams: () => [ new URLSearchParams('job_id=testjob') ] };
});

// Import after mocks
import ReviewCenter from '../../pages/ReviewCenter';

describe('ReviewCenter integration', () => {
  it('save button triggers updateJobItem', async () => {
  const api = await import('../../lib/api');
  render(<MemoryRouter initialEntries={['/review?job_id=testjob']}><ReviewCenter /></MemoryRouter>);
  // Wait for any instance of the question text (multiple elements may contain it)
  await screen.findAllByText('What is a stack?');
  const saveBtn = await screen.findByTestId('save-editor');
  fireEvent.click(saveBtn);
  await waitFor(() => expect(api.updateJobItem).toHaveBeenCalledTimes(1));
  });
});
