import { useState } from "react";
import { postJson, setToken } from "../api.js";

// Email + password login. The token is stored by setToken and sent as a Bearer header.
export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const data = await postJson("/api/auth/login", { email, password });
      setPassword("");
      setToken(data.access_token);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section>
      <h2>Log in</h2>
      <form onSubmit={submit} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button type="submit">Log in</button>
      </form>
      {error && <p style={{ color: "#b00020" }}>{error}</p>}
    </section>
  );
}
