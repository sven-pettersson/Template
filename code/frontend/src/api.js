// Small fetch helpers shared by the components.
// When logged in, every request sends `Authorization: Bearer <token>`.

const TOKEN_KEY = "token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event("auth-changed"));
}

async function request(method, path, body) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 401 && token) setToken(null); // expired or logged out
  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? `: ${data.detail}` : "";
    } catch {
      // no JSON body
    }
    throw new Error(`${method} ${path} failed (${res.status})${detail}`);
  }
  return res.status === 204 ? null : res.json();
}

export const getJson = (path) => request("GET", path);
export const postJson = (path, body) => request("POST", path, body);
export const putJson = (path, body) => request("PUT", path, body);
export const deleteJson = (path) => request("DELETE", path);
