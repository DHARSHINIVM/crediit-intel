import React from "react";

export default function ScoreCard({ issuer, scoreInfo }) {
  if (!scoreInfo) return <div className="card">No score available</div>;
  const { score, shap = [], features = {} } = scoreInfo;
  const top = shap.slice(0, 5);
  return (
    <div className="card">
      <h3>{issuer.name} — Score {Math.round(score)}</h3>
      <div className="small">Ticker: {issuer.ticker} • Country: {issuer.country}</div>

      <div style={{marginTop:10}}>
        <strong>Top feature impacts</strong>
        <ul className="list">
          {top.map(s => (
            <li key={s.feature} className="small event-item">
              <div style={{display:"flex", justifyContent:"space-between"}}>
                <div>{s.feature}</div>
                <div>{s.shap_value.toFixed(2)}</div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
