"use client";

import { useState } from "react";
import { updatePreferences } from "@/lib/api";

export default function SettingsForm({
  initialPreferences,
  categories = [],
  sources = [],
}) {
  const [prefs, setPrefs] = useState(
    initialPreferences || {
      selected_categories: categories.map((c) => c.slug),
      mute_keywords: [],
      theme: "system",
      digest_hour: 7,
      show_thumbnails: false,
      notify_high_importance: false,
    }
  );
  const [muteText, setMuteText] = useState((prefs.mute_keywords || []).join(", "));
  const [status, setStatus] = useState("");

  function toggleCategory(slug) {
    setPrefs((p) => {
      const set = new Set(p.selected_categories || []);
      if (set.has(slug)) set.delete(slug);
      else set.add(slug);
      const selected = Array.from(set);
      return { ...p, selected_categories: selected, category_order: selected };
    });
  }

  async function onSave(e) {
    e.preventDefault();
    const mute_keywords = muteText
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const body = {
      selected_categories: prefs.selected_categories,
      category_order: prefs.category_order || prefs.selected_categories,
      mute_keywords,
      theme: prefs.theme,
      digest_hour: Number(prefs.digest_hour) || 7,
      show_thumbnails: Boolean(prefs.show_thumbnails),
      notify_high_importance: Boolean(prefs.notify_high_importance),
    };
    try {
      const updated = await updatePreferences(body);
      setPrefs(updated);
      setStatus("Saved.");
    } catch (err) {
      setStatus(err.message || "Save failed");
    }
  }

  return (
    <form onSubmit={onSave} style={{ maxWidth: "36rem" }}>
      <section style={{ marginBottom: "1.75rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem" }}>Categories</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginTop: "0.75rem" }}>
          {categories.map((c) => (
            <label key={c.slug} style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
              <input
                type="checkbox"
                checked={(prefs.selected_categories || []).includes(c.slug)}
                onChange={() => toggleCategory(c.slug)}
              />
              {c.name}
            </label>
          ))}
        </div>
      </section>

      <section style={{ marginBottom: "1.75rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem" }}>Mute keywords</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          Comma-separated. Applied server-side — muted items never appear in the feed.
        </p>
        <input
          className="search"
          style={{ width: "100%", marginTop: "0.5rem" }}
          value={muteText}
          onChange={(e) => setMuteText(e.target.value)}
          placeholder="crypto, celebrity, spoiler"
        />
      </section>

      <section style={{ marginBottom: "1.75rem", display: "grid", gap: "0.75rem" }}>
        <label>
          Digest hour (UTC-ish local machine hour stored as int){" "}
          <input
            className="search"
            type="number"
            min={0}
            max={23}
            value={prefs.digest_hour ?? 7}
            onChange={(e) => setPrefs((p) => ({ ...p, digest_hour: e.target.value }))}
            style={{ width: "5rem", marginLeft: "0.5rem" }}
          />
        </label>
        <label>
          Theme{" "}
          <select
            className="search"
            value={prefs.theme || "system"}
            onChange={(e) => setPrefs((p) => ({ ...p, theme: e.target.value }))}
            style={{ marginLeft: "0.5rem" }}
          >
            <option value="system">system</option>
            <option value="light">light</option>
            <option value="dark">dark</option>
          </select>
        </label>
      </section>

      <section style={{ marginBottom: "1.75rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem" }}>Sources</h2>
        <ul style={{ color: "var(--muted)", paddingLeft: "1.1rem" }}>
          {sources.map((s) => (
            <li key={s.name}>
              {s.display_name || s.name} · {s.category} · {s.enabled ? "on" : "off"}
            </li>
          ))}
        </ul>
      </section>

      <button className="btn btn-accent" type="submit">
        Save preferences
      </button>
      {status ? <p style={{ color: "var(--muted)", marginTop: "0.75rem" }}>{status}</p> : null}
    </form>
  );
}
