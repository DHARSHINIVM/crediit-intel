import axios from "axios";

export const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
});

export async function fetchIssuers() {
  const res = await api.get("/issuers");
  return res.data;
}

export async function fetchFundamentals(issuer_id) {
  const res = await api.get("/fundamentals", { params: { issuer_id } });
  return res.data;
}

export async function fetchScore(issuer_id) {
  const res = await api.get(`/score/${issuer_id}`);
  return res.data;
}

export async function fetchEvents(issuer_id) {
  const res = await api.get("/events", { params: { issuer_id } });
  return res.data;
}

export async function fetchNews() {
  const res = await api.get("/news");
  return res.data;
}
