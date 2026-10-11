import SettingsForm from "@/components/SettingsForm";
import { getCategories, getPreferences, getSources } from "@/lib/api";

export default async function SettingsPage() {
  let preferences = null;
  let categories = [];
  let sources = [];
  try {
    [preferences, categories, sources] = await Promise.all([
      getPreferences(),
      getCategories(),
      getSources(),
    ]);
  } catch {
    // empty defaults in form
  }

  return (
    <div>
      <h1 className="page-title">Settings</h1>
      <p className="page-sub">
        Categories, mute keywords, digest hour, theme. Everything stays on this machine.
      </p>
      <SettingsForm
        initialPreferences={preferences}
        categories={categories}
        sources={sources}
      />
    </div>
  );
}
