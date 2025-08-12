import React, { useRef, useState } from 'react';
import { Button } from './ui/button';
import { Label } from './ui/label';

/**
 * Simple markdown-ish editor with citation + diagram insertion callbacks.
 * props:
 *  value: string
 *  onChange: (val:string)=>void
 *  onSave: ()=>Promise<void>
 *  onCite: (selection:string)=>void  (also updates references externally)
 *  onInsertDiagram: (diagramPath:string)=>void
 */
export default function EditorPanel({ value, onChange, onSave, onCite, onInsertDiagram }) {
  const ref = useRef(null);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try { await onSave(); } finally { setSaving(false); }
  };

  const citeSelection = () => {
    const el = ref.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    if (start === end) return; // nothing selected
    const selected = el.value.slice(start, end);
    onCite(selected);
  };

  const insertDiagram = (path) => {
    const el = ref.current;
    const tag = `![diagram](${path})`;
    if (!el) { onChange(value + '\n' + tag); return; }
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const before = el.value.slice(0, start);
    const after = el.value.slice(end);
    const next = before + tag + after;
    onChange(next);
    // place caret after insertion
    setTimeout(()=>{
      el.focus();
      el.selectionStart = el.selectionEnd = before.length + tag.length;
    }, 10);
    onInsertDiagram(path);
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2 items-center">
        <Button size="sm" variant="secondary" onClick={citeSelection}>Cite</Button>
        <Button size="sm" variant="outline" onClick={()=>insertDiagram('/diagram-placeholder.png')} data-testid="insert-diagram">Insert Diagram</Button>
        <Button size="sm" onClick={handleSave} disabled={saving} data-testid="save-editor">{saving ? 'Saving…' : 'Save'}</Button>
      </div>
      <div>
        <Label htmlFor="answer-editor">Answer</Label>
        <textarea
          id="answer-editor"
          ref={ref}
          className="mt-1 w-full min-h-[280px] rounded-md border bg-background p-3 text-sm"
          value={value}
          onChange={e=>onChange(e.target.value)}
          placeholder="Edit answer here. Use Cite to add a reference and Insert Diagram to include image placeholders."
        />
      </div>
    </div>
  );
}
