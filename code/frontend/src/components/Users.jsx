import { useEffect, useState } from "react";
import { deleteJson, getJson, postJson } from "../api.js";

// User management for admins. Same pattern as Items.jsx.
export default function Users({ me }) {
  const [users, setUsers] = useState([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [error, setError] = useState("");

  const load = () => getJson("/api/users").then(setUsers).catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  async function addUser(event) {
    event.preventDefault();
    setError("");
    try {
      await postJson("/api/users", { email, password, is_admin: isAdmin });
      setEmail("");
      setPassword("");
      setIsAdmin(false);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function removeUser(user) {
    if (!window.confirm(`Delete ${user.email}?`)) return;
    setError("");
    try {
      await deleteJson(`/api/users/${user.id}`);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section>
      <h2>Users</h2>
      <form onSubmit={addUser} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input
          type="password"
          placeholder="Password (min 8)"
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <label>
          <input type="checkbox" checked={isAdmin} onChange={(e) => setIsAdmin(e.target.checked)} /> Admin
        </label>
        <button type="submit">Add user</button>
      </form>
      {error && <p style={{ color: "#b00020" }}>{error}</p>}
      <ul>
        {users.map((user) => (
          <li key={user.id}>
            <strong>{user.email}</strong>
            {user.is_root ? " (root admin)" : user.is_admin ? " (admin)" : ""}{" "}
            {!user.is_root && user.id !== me?.id && (
              <button type="button" onClick={() => removeUser(user)}>
                Delete
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
