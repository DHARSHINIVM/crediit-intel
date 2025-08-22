import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchIssuers, fetchScore } from "../api";

export default function IssuerList({ onSelect }) {
  const [issuers, setIssuers] = useState([]);
  const [scores, setScores] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      try {
        const data = await fetchIssuers();
        if (!mounted) return;
        setIssuers(data);
        // fetch scores in parallel (watch out for many issuers => throttle in production)
        const promises = data.map(i => fetchScore(i.id).then(r => ({ id: i.id, score: r.score })).catch(() => ({ id: i.id, score: null })));
        const results = await Promise.all(promises);
        if (!mounted) return;
        const map = {};
        results.forEach(x => map[x.id] = x.score);
        setScores(map);
      } catch (e) {
        console.error(e);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; }
  }, []);

  return (
    <div className="card">
      <h3>Issuers</h3>
      {loading && <div className="small">Loading...</div>}
      <div style={{marginTop:8}}>
        {issuers.map(issuer => (
          <div key={issuer.id} className="issuer-row">
            <div>
              <div style={{fontWeight:600}}>{issuer.name}</div>
              <div className="small">{issuer.ticker} • {issuer.country}</div>
            </div>
            <div style={{display:"flex",gap:8, alignItems:"center"}}>
              <div className="small">Score</div>
              <div className="score-badge">{scores[issuer.id] ? Math.round(scores[issuer.id]) : "—"}</div>
              <Link to={`/issuer/${issuer.id}`} className="link">Open</Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
