import React from "react";
import IssuerList from "../components/IssuerList";

export default function Dashboard() {
  return (
    <div className="container" style={{marginTop: 12}}>
      <div style={{display:"flex", gap:16}}>
        <div style={{flex:1}}>
          <IssuerList />
        </div>
        <div style={{width:360}}>
          <div className="card">
            <h3>Filters</h3>
            <div className="small">(Coming) Filter by issuer, date range, etc.</div>
          </div>
          <div style={{height:16}} />
          <div className="card">
            <h3>Quick actions</h3>
            <div className="small">Manual ingest, retrain, and more (add endpoints in backend)</div>
          </div>
        </div>
      </div>
    </div>
  );
}
