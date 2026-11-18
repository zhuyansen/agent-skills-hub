/**
 * PostHog browser loader (single source of truth for SPA + all static pages).
 *
 * Set POSTHOG_KEY (phc_...) and POSTHOG_HOST (your Cloudflare Worker reverse proxy,
 * e.g. https://e.agentskillshub.top or https://ash-ph.<subdomain>.workers.dev).
 * While POSTHOG_KEY is empty, this loader no-ops cleanly with zero network calls.
 */
(function () {
  var POSTHOG_KEY = "phc_wCjMwyvaJQAHodWWKMeBWxoCmwo8puNJdyxKtomET8j5";
  var POSTHOG_HOST = "https://agentskillshub-posthog-proxy.m17551076169.workers.dev";
  if (!POSTHOG_KEY || !POSTHOG_HOST) return;
  if (window.posthog && window.posthog.__loaded) return;

  function pageType(p) {
    if (!p || p === "/" || p === "/zh/") return "home";
    if (p.indexOf("/best/") === 0) return "best_scenario";
    if (p.indexOf("/skill/") === 0) return "skill_detail";
    if (p.indexOf("/analyzer") === 0) return "analyzer";
    if (p.indexOf("/enterprise") === 0) return "enterprise";
    if (p.indexOf("/pro") === 0) return "pro";
    if (p.indexOf("/ci-gate") === 0) return "ci_gate";
    if (p.indexOf("/org-audit") === 0) return "org_audit";
    if (p.indexOf("/compare") === 0) return "compare";
    if (p.indexOf("/agent-skills-directories") === 0) return "directories";
    if (p.indexOf("/how-we-grade") === 0) return "how_we_grade";
    if (p.indexOf("/blog/") === 0) return "blog";
    if (p.indexOf("/book/") === 0) return "book";
    if (p.indexOf("/stats") === 0) return "stats";
    if (p.indexOf("/daily/") === 0) return "daily";
    if (p.indexOf("/author/") === 0) return "author";
    return "other";
  }

  !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(/\/+$/,"")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageViewId".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

  window.posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST.replace(/\/+$/, ""),
    ui_host: "https://us.posthog.com",
    person_profiles: "identified_only",
    persistence: "localStorage",
    capture_pageview: "history_change",
    capture_pageleave: true,
    autocapture: true,
    loaded: function (ph) {
      var pt = pageType(window.location.pathname);
      var sp = new URLSearchParams(window.location.search);
      var refHost = "";
      if (document.referrer) {
        try {
          var u = new URL(document.referrer);
          if (u.hostname !== window.location.hostname) refHost = u.hostname;
        } catch (e) {}
      }
      ph.register_once({
        entry_page_type: pt,
        entry_path: window.location.pathname,
        entry_source: sp.get("utm_source") || refHost || "(direct)",
        entry_medium: sp.get("utm_medium") || (refHost ? "referral" : "(none)")
      });
    },
    before_send: function (ev) {
      if (!ev) return ev;
      ev.properties = ev.properties || {};
      if (!ev.properties.page_type) ev.properties.page_type = pageType(window.location.pathname);
      if (!ev.properties.lang) ev.properties.lang = document.documentElement.lang || "en";
      return ev;
    }
  });
})();
