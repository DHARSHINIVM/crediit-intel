import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchFundamentals, fetchScore, fetchEvents, fetchNews } from "../api";
import ScoreCard from "../components/ScoreCard";
import ScoreChart from "../components/ScoreChart";
import FeatureBarChart from "../components/FeatureBarChart";
import { formatISO, parseISO } from "date-fns";

/**
 * Client-side scoring fallback:
 * We mirror the Day-3 heuristic used in ML to create a synthetic "score" per fundamentals row.
 * The backend /score returns the latest score + SHAP for the latest snapshot.
 */
function synth_score_from_row(fund, avg_sentiment = 0.0) {
  // replicate same formula as ml._synthesize_label_from_row (approximate)
  const debt_to_ebitda = (fund.total_debt || 0) / (fund.ebitda || 1e-6);
  const ebitda_margin = (fund.ebitda || 0) / (fund.revenue || 1e-6);
  // revenue growth not available on single row; caller will supply prevRevenue
  const growth = fund._growth || 0;
  const base = 600.0;
  const debt_penalty = 100.0 * Math.min(debt_to_ebitda, 10.0) / 10.0;
  const growth_bonus = 150.0 * Math.max(Math.min(growth, 1.0), -1.0);
  const margin_bonus = 100.0 * Math.max(Math.min(ebitda_margin, 1.0), -1.0);
  const sentiment_bonus = 100.0 * Math.max(Math.min(avg_sentiment, 1.0), -1.0);
  let score = base - debt_penalty + growth_bonus + margin_bonus + sentiment_bonus;
  score = Math.max(300.0, Math.min(850.0, score));
  return score;
}

export default function IssuerDetail() {
  const { id } = useParams();
  const issuerId = Number(id);
  const [fundamentals, setFundamentals] = useState([]);
  const [scoreInfo, setScoreInfo] = useState(null);
  const [events, setEvents] = useState([]);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function loadAll() {
      setLoading(true);
      try {
        const [funds, scoreRes, evts, allNews] = await Promise.all([
          fetchFundamentals(issuerId),
          fetchScore(issuerId).catch(() => null),
          fetchEvents(issuerId).catch(() => []),
          fetchNews().catch(() => [])
        ]);
        if (!mounted) return;
        setFundamentals(funds || []);
        setScoreInfo(scoreRes);
        setEvents(evts || []);
        // filter news that is linked to events or contain ticker (best-effort)
        setNews(allNews || []);
      } catch (e) {
        console.error(e);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadAll();
    return () => { mounted = false; }
  }, [issuerId]);

  // Build time-series: compute score per fundamentals report_date using prev row to get revenue_growth
  const tsData = React.useMemo(() => {
    if (!fundamentals || fundamentals.length === 0) return [];
    // sort ascending by report_date
    const sorted = [...fundamentals].sort((a,b) => new Date(a.report_date) - new Date(b.report_date));
    const out = [];
    for (let i=0;i<sorted.length;i++){
      const cur = {...sorted[i]};
      const prev = sorted[i-1];
      const prev_rev = prev ? (prev.revenue || 0) : null;
      let growth = 0;
      if (prev_rev !== null) {
        const denom = Math.abs(prev_rev) > 1e-6 ? prev_rev : 1e-6;
        growth = ((cur.revenue || 0) - prev_rev) / denom;
      }
      cur._growth = growth;
      // average sentiment: compute average of events' sentiment around this date (simple heuristic)
      // find events within +/- 30 days
      const relatedEvents = (events || []).filter(ev => {
        if (!ev.timestamp) return false;
        const evDate = new Date(ev.timestamp);
        const repDate = new Date(cur.report_date);
        const diffDays = Math.abs((evDate - repDate) / (1000*60*60*24));
        return diffDays <= 30;
      });
      const sentiments = relatedEvents.map(e => e.sentiment).filter(s => typeof s === "number");
      const avg_sentiment = sentiments.length ? (sentiments.reduce((a,b)=>a+b,0)/sentiments.length) : 0.0;
      const sc = synth_score_from_row(cur, avg_sentiment);
      out.push({ date: cur.report_date, score: Math.round(sc), revenue: cur.revenue, total_debt: cur.total_debt });
    }
    return out;
  }, [fundamentals, events]);

  return (
    <div className="container" style={{marginTop:16}}>
      <div style={{display:"flex", gap:12}}>
        <div style={{flex:1}}>
          {loading && <div className="card small">Loading...</div>}
          {!loading && scoreInfo && (
            <ScoreCard issuer={{ id: issuerId, name: scoreInfo.issuer.name, ticker: scoreInfo.issuer.ticker, country: scoreInfo.issuer.country }} scoreInfo={scoreInfo} />
          )}
          <div style={{height:12}}/>
          <div className="card">
            <h3>Charts</h3>
            <div className="charts-row">
              <ScoreChart data={tsData} />
              <FeatureBarChart shap={scoreInfo ? scoreInfo.shap : []} />
            </div>
          </div>

          <div style={{height:12}}/>
          <div className="card">
            <h3>Related Events</h3>
            {events.length === 0 && <div className="small">No events found</div>}
            <ul className="list">
              {events.map(ev => (
                <li key={ev.id} className="event-item">
                  <div style={{display:"flex", justifyContent:"space-between"}}>
                    <div>
                      <div style={{fontWeight:600}}>{ev.event_type}</div>
                      <div className="small">{ev.description}</div>
                    </div>
                    <div className="small">{ev.sentiment ? ev.sentiment.toFixed(2) : "—"}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div style={{width:360}}>
          <div className="card">
            <h3>Recent News</h3>
            <ul className="list">
              {news.slice(0,8).map(n => (
                <li key={n.id} className="event-item">
                  <a href={n.link} target="_blank" rel="noreferrer" className="link" style={{fontWeight:600}}>{n.title}</a>
                  <div className="small">{n.published_at ? new Date(n.published_at).toLocaleString() : ""}</div>
                </li>
              ))}
            </ul>
          </div>
          <div style={{height:12}} />
          <div className="card">
            <h3>Controls</h3>
            <div className="small">Date-range & issuer filters will be added here (optional)</div>
          </div>
        </div>
      </div>
    </div>
  );
}
