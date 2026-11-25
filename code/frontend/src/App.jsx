import { useEffect, useState } from "react";
import { getJson } from "./api.js";
import Items from "./components/Items.jsx";

export default function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    getJson("/api/health")
      .then((data) => setStatus(data.status))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 640, margin: "2rem auto", padding: "0 1rem" }}>
      <h1>Template</h1>
      <p>
        Backend: <strong>{status}</strong> · <a href="/docs">API docs (Swagger)</a>
      </p>
      {/* One component per resource. /new-resource adds more here. */}
      <Items />
    </main>
  );
}
