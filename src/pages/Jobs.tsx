import Seo from '@/components/Seo';
import { useEffect, useState } from 'react';
import { listJobs, deleteJob } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useNavigate } from 'react-router-dom';

interface JobMeta { job_id: string; status: string; count: number }

const Jobs = () => {
  const [jobs, setJobs] = useState<JobMeta[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 20;
  const navigate = useNavigate();
  const load = () => {
    setLoading(true);
    listJobs(page, limit).then(r => { setJobs(r.jobs || []); setTotal(r.total || (r.jobs||[]).length); }).finally(()=> setLoading(false));
  };
  useEffect(()=>{ load(); }, [page]);
  return (
    <div>
      <Seo title="Jobs" description="Generated question jobs" />
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Jobs</h1>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={load}>{loading? 'Refreshing...' : 'Refresh'}</Button>
        </div>
      </div>
      <Card>
  <CardHeader><CardTitle>Job Runs</CardTitle></CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Job ID</th>
                <th>Status</th>
                <th>Items</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map(j => (
                <tr key={j.job_id} className="border-b last:border-none">
                  <td className="py-2 font-mono text-xs">{j.job_id}</td>
                  <td>{j.status}</td>
                  <td>{j.count}</td>
                  <td className="flex gap-2 py-1">
                    <Button size="sm" variant="outline" onClick={()=> navigate(`/review?job_id=${j.job_id}`)}>Review</Button>
                    <Button size="sm" variant="outline" onClick={()=> navigate(`/templates?job_id=${j.job_id}`)}>Export</Button>
                    <Button size="sm" variant="destructive" onClick={async ()=>{ await deleteJob(j.job_id); load(); }}>Delete</Button>
                  </td>
                </tr>
              ))}
              {jobs.length===0 && !loading && (
                <tr><td colSpan={4} className="py-4 text-center text-muted-foreground">No jobs yet</td></tr>
              )}
            </tbody>
          </table>
          <div className="flex items-center justify-between mt-4 text-xs">
            <span>Page {page} • {(jobs.length)} shown of {total}</span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" disabled={page===1 || loading} onClick={()=> setPage(p=> Math.max(1,p-1))}>Prev</Button>
              <Button size="sm" variant="outline" disabled={(page*limit)>= total || loading} onClick={()=> setPage(p=> p+1)}>Next</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Jobs;