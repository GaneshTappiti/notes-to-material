import React from 'react';
import { Button } from './ui/button';
import { FileText, Image } from 'lucide-react';

/**
 * SourcePanel lists retrieved pages + diagram thumbnails.
 * props:
 *  pages: Array<{id:string; file_name:string; page_no:number; text:string}>
 *  diagrams: string[]
 *  onInsertDiagram: (path:string)=>void
 *  onCite: (pageRef:string)=>void
 */
export default function SourcePanel({ pages, diagrams, onInsertDiagram, onCite }) {
  return (
    <div className="space-y-4">
      <div>
        <h4 className="font-semibold mb-2">Retrieved Pages</h4>
        <ul className="space-y-2">
          {pages.map(p => (
            <li key={p.id} className="p-2 border rounded">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                <span className="text-sm font-medium">{p.file_name}:{p.page_no}</span>
                <Button size="sm" variant="secondary" onClick={()=> onCite(`${p.file_name}:${p.page_no}`)}>Cite</Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-3">{p.text}</p>
            </li>
          ))}
          {pages.length === 0 && <li className="text-xs text-muted-foreground">No retrieved pages</li>}
        </ul>
      </div>
      <div>
        <h4 className="font-semibold mb-2">Diagrams</h4>
        <div className="grid grid-cols-2 gap-2">
          {diagrams.map(d => (
            <div key={d} className="border rounded p-1 flex flex-col items-center text-center gap-1">
              <div className="bg-muted h-16 w-full flex items-center justify-center text-[10px]">IMG</div>
              <Button size="xs" variant="outline" onClick={()=> onInsertDiagram(d)}>Insert</Button>
            </div>
          ))}
          {diagrams.length === 0 && <p className="text-xs text-muted-foreground">No diagrams</p>}
        </div>
      </div>
    </div>
  );
}
