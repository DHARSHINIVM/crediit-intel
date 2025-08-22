import React from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import IssuerDetail from "./pages/IssuerDetail";
import Header from "./components/Header";

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <div className="container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/issuer/:id" element={<IssuerDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
