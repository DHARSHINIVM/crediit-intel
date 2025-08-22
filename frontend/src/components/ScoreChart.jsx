import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { format } from "date-fns";

export default function ScoreChart({ data }) {
  // data: [{ date: '2024-12-31', score: 700 }, ...]
  return (
    <div className="card chart-box">
      <h4>Score Time Series</h4>
      <div style={{height:260}}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tickFormatter={(d) => format(new Date(d), "MM/yy")} />
            <YAxis domain={[300, 850]} />
            <Tooltip labelFormatter={(l) => format(new Date(l), "yyyy-MM-dd")} />
            <Line type="monotone" dataKey="score" stroke="#2563eb" strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
