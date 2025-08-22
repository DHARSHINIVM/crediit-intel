import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function FeatureBarChart({ shap }) {
  // shap: [{ feature, shap_value }, ...]
  const data = shap.map(s => ({ name: s.feature, value: Math.abs(s.shap_value), signed: s.shap_value }));
  return (
    <div className="card chart-box">
      <h4>Feature importance (SHAP)</h4>
      <div style={{height:260}}>
        <ResponsiveContainer>
          <BarChart layout="vertical" data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" />
            <Tooltip formatter={(v, name, props) => [props.payload.signed, "SHAP"]} />
            <Bar dataKey="value" fill="#111827" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
