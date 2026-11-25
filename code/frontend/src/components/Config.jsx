import { useState } from "react";
import { putJson } from "../api.js";

// Feature switches. Shown only when the backend says the config is editable
// (APP_ENV local or test). In staging and production PUT /api/config is 404.
export default function Config({ config, onSaved }) {
  const [auth, setAuth] = useState(config.auth_enabled);
  const [users, setUsers] = useState(config.user_management_enabled);
  const [message, setMessage] = useState("");

  async function save(event) {
    event.preventDefault();
    setMessage("");
    try {
      const saved = await putJson("/api/config", {
        auth_enabled: auth,
        user_management_enabled: auth && users,
      });
      setMessage("Saved.");
      onSaved(saved);
    } catch (e) {
      setMessage(e.message);
    }
  }

  return (
    <section>
      <h2>Config</h2>
      <p>
        Environment: <strong>{config.app_env}</strong> · Session TTL: {config.session_ttl_minutes} min
      </p>
      <form onSubmit={save} style={{ display: "grid", gap: "0.5rem", justifyItems: "start" }}>
        <label>
          <input type="checkbox" checked={auth} onChange={(e) => setAuth(e.target.checked)} /> Login and sessions
          (the API requires <code>Authorization: Bearer</code>)
        </label>
        <label style={{ opacity: auth ? 1 : 0.5 }}>
          <input type="checkbox" checked={auth && users} disabled={!auth} onChange={(e) => setUsers(e.target.checked)} />{" "}
          User management (admins add and remove users)
        </label>
        <button type="submit">Save</button>
      </form>
      {auth && !config.auth_enabled && (
        <p>After saving you must log in, as the root admin from ADMIN_EMAIL / ADMIN_PASSWORD in .env.</p>
      )}
      {message && <p>{message}</p>}
    </section>
  );
}
