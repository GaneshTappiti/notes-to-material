import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import EditorPanel from '../EditorPanel.jsx';

describe('EditorPanel', () => {
  it('calls onSave when Save clicked', async () => {
    const onSave = vi.fn().mockResolvedValue();
    render(<EditorPanel value="Answer" onChange={()=>{}} onSave={onSave} onCite={()=>{}} onInsertDiagram={()=>{}} />);
    fireEvent.click(screen.getByTestId('save-editor'));
    expect(onSave).toHaveBeenCalled();
  });
  it('inserts diagram placeholder', () => {
    const onChange = vi.fn();
    render(<EditorPanel value="A" onChange={onChange} onSave={()=>Promise.resolve()} onCite={()=>{}} onInsertDiagram={()=>{}} />);
    fireEvent.click(screen.getByTestId('insert-diagram'));
    // Expect onChange called with markdown image tag
    const arg = onChange.mock.calls[0][0];
    expect(arg).toContain('![diagram](');
  });
});
