// /Public/js/config.js
import { getDefaultAvatarIcon } from './ui.js';

export const defaults = {
  FLOWBOT_PREFERRED_NAME: "FlowBot",
  SUPPORT_EMAIL: "support@permitflow.bettini.us",
  DEFAULT_LANGUAGE: "en-US",
  ALTERNATE_AVATARS: [] // backend will populate
};

export async function loadSiteProperties() {
  try {
    const res = await fetch("/site-properties");
    const data = await res.json();
    const props = { ...defaults, ...data };

    // Ensure ALTERNATE_AVATARS is valid
    if (!Array.isArray(props.ALTERNATE_AVATARS) || props.ALTERNATE_AVATARS.length === 0) {
      props.ALTERNATE_AVATARS = defaults.ALTERNATE_AVATARS;
    }

    // Store globally for UI helpers
    window.siteProps = props;
    return props;
  } catch (err) {
    console.error("Error loading site properties:", err);
    window.siteProps = defaults;
    return defaults;
  }
}