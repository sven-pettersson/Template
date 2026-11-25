import { useEffect, useState } from "react";
import { getJson, getToken, postJson, setToken } from "./api.js";
import Config from "./components/Config.jsx";
import Items from "./components/Items.jsx";
import Login from "./components/Login.jsx";
import Users from "./components/Users.jsx";

export default function App() {
  const [status, setStatus] = useState("checking...");
  const [config, setConfig] = useState(null);
  const [me, setMe] = useState(null);
  const [token, setTokenState] = useState(getToken());
  const [tab, setTab] = useState("items");

  useEffect(() => {
    getJson("/api/health")
      .then((data) => setStatus(data.status))
      .catch(() => setStatus("unreachable"));
    getJson("/api/config").then(setConfig).catch(() => setConfig(null));
    const onAuthChanged = () => setTokenState(getToken());
    window.addEventListener("auth-changed", onAuthChanged);
    return () => window.removeEventListener("auth-changed", onAuthChanged);
  }, []);

  // Who is logged in? Only asked when login is on and we have a token.
  useEffect(() => {
    if (!config?.auth_enabled || !token) {
      setMe(null);
      return;
    }
    getJson("/api/auth/me").then(setMe).catch(() => setMe(null));
  }, [config?.auth_enabled, token]);

  async function logout() {
    try {
      await postJson("/api/auth/logout");
    } catch {
      // the session may already be gone
    }
    setToken(null);
    setTab("items");
  }

  const loginRequired = config?.auth_enabled && !me;
  const tabs = [
    { id: "login", label: "Log in", show: loginRequired },
    { id: "items", label: "Items", show: !loginRequired },
    { id: "users", label: "Users", show: config?.user_management_enabled && me?.is_admin },
    { id: "config", label: "Config", show: config?.editable },
  ].filter((t) => t.show);
  const current = tabs.some((t) => t.id === tab) ? tab : tabs[0]?.id;

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 640, margin: "2rem auto", padding: "0 1rem" }}>
      <h1>Template</h1>
      <p>
        Backend: <strong>{status}</strong> · <a href="/docs">API docs (Swagger)</a>
        {me && (
          <>
            {" "}
            · {me.email}{" "}
            <button type="button" onClick={logout}>
              Log out
            </button>
          </>
        )}
      </p>

      {tabs.length > 1 && (
        <nav style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          {tabs.map((t) => (
            <button key={t.id} type="button" onClick={() => setTab(t.id)} disabled={t.id === current}>
              {t.label}
            </button>
          ))}
        </nav>
      )}

      {current === "login" && <Login />}
      {/* One component per resource. /new-resource adds more here. */}
      {current === "items" && <Items />}
      {current === "users" && <Users me={me} />}
      {current === "config" && <Config key={JSON.stringify(config)} config={config} onSaved={setConfig} />}
    </main>
  );
}
