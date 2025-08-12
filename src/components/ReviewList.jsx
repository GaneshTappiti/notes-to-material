import React from 'react';
import { FixedSizeList as List } from 'react-window';
import { Badge } from './ui/badge';

/**
 * ReviewList renders a virtualized list of questions grouped by question text.
 * props:
 *  groups: Array<{ question_text: string; variants: Array<{question_id:string; marks:number; page_references:string[]}> }>
 *  activeId: string
 *  onSelect: (question_id:string)=>void
 */
export default function ReviewList({ groups, activeId, onSelect }) {
  const Row = ({ index, style }) => {
    const group = groups[index];
    const isActive = group.variants.some(v => v.question_id === activeId);
    return (
      <li style={style} className={`p-3 cursor-pointer border-b last:border-b-0 ${isActive ? 'bg-secondary' : ''}`} onClick={() => onSelect(group.variants[0].question_id)}>
        <div className="flex items-center justify-between mb-1">
          <p className="text-sm font-medium truncate" title={group.question_text}>{group.question_text}</p>
          <div className="flex gap-1">
            {group.variants.map(v => <Badge key={v.question_id} variant="outline" className="text-[10px]">{v.marks}M</Badge>)}
          </div>
        </div>
        <div className="flex gap-2 text-xs text-muted-foreground">
          <span>{group.variants.flatMap(v=>v.page_references||[]).length} refs</span>
        </div>
      </li>
    );
  };
  return (
    <ul className="divide-y max-h-[70vh] overflow-hidden">
      <List
        height={560}
        itemCount={groups.length}
        itemSize={76}
        width={'100%'}
        className="overflow-y-auto"
      >
        {Row}
      </List>
    </ul>
  );
}
