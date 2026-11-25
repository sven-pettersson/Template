import { useEffect, useState } from "react";
import { getJson, postJson } from "../api.js";

// List and create items. /new-resource copies this component as a pattern.
export default function Items() {
  const [items, setItems] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  const load = () => getJson("/api/items").then(setItems).catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  async function addItem(event) {
    event.preventDefault();
    setError("");
    try {
      await postJson("/api/items", { name, description: description || null });
      setName("");
      setDescription("");
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section>
      <h2>Items</h2>
      <form onSubmit={addItem} style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
        <input placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <button type="submit">Add item</button>
      </form>
      {error && <p style={{ color: "#b00020" }}>{error}</p>}
      {items.length === 0 ? (
        <p>No items yet.</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item.id}>
              <strong>{item.name}</strong>
              {item.description && ` – ${item.description}`}
              {item.embedding && ` (vector: ${item.embedding.length} dims)`}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
