import React from "react";
import { Link } from "react-router-dom";

export default function Header() {
  return (
    <div className="container" style={{marginTop: 16}}>
      <div className="header">
        <div className="logo">Credit Intelligence</div>
        <div style={{marginLeft: 12}} className="small">Real-time explainable credit platform</div>
        <div style={{marginLeft: "auto"}}>
          <Link to="/" className="link">Dashboard</Link>
        </div>
      </div>
    </div>
  );
}
