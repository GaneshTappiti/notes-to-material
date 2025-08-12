import { useState } from 'react';
import { retrieve, generate } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

export default function RagPlayground(){
  const [query,setQuery]=useState('photosynthesis');
  const [retrieveRes,setRetrieveRes]=useState<any|null>(null);
  const [genPrompt,setGenPrompt]=useState('Generate 1 short question about photosynthesis.');
  const [genRes,setGenRes]=useState<any|null>(null);
  const [loading,setLoading]=useState(false);

  const doRetrieve=async()=>{setLoading(true);try{const r=await retrieve(query,5);setRetrieveRes(r);}finally{setLoading(false);}};
  const doGenerate=async()=>{setLoading(true);try{const r=await generate(genPrompt,5);setGenRes(r);}finally{setLoading(false);}};

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">RAG Playground</h1>
      <Card>
        <CardHeader><CardTitle>Retrieve</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Query" />
          <Button disabled={loading} onClick={doRetrieve}>Retrieve</Button>
          {retrieveRes && <pre className="text-xs max-h-64 overflow-auto bg-muted p-2 rounded">{JSON.stringify(retrieveRes,null,2)}</pre>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Generate</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Textarea value={genPrompt} onChange={e=>setGenPrompt(e.target.value)} />
            <Button disabled={loading} onClick={doGenerate}>Generate</Button>
            {genRes && <pre className="text-xs max-h-64 overflow-auto bg-muted p-2 rounded">{JSON.stringify(genRes,null,2)}</pre>}
        </CardContent>
      </Card>
    </div>
  );
}
