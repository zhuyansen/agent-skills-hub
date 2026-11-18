// Types for enterpriseCopy.mjs, a plain module so the Node page generators can import it too.
export interface RoleItem {
  role: string;
  pain: string;
  win: string;
}
export interface Tier {
  name: string;
  price: string;
  unit: string;
  features: string[];
  cta: string;
  href?: string;
  highlight?: boolean;
}
export interface QA {
  q: string;
  a: string;
}

export interface EnterpriseCopy {
  meta: { title: string; description: string };
  hero: {
    badge: string;
    h1a: string;
    h1b: string;
    sub: string;
    ctaPrimary: string;
    ctaSecondary: string;
    note: string;
  };
  band: { label: string; footnote: string };
  bandFrameworks: { name: string; sub: string }[];
  signals: { stat: string; label: string; sub: string }[];
  problem: {
    h2: string;
    sub: string;
    items: { emoji: string; title: string; body: string }[];
  };
  solution: {
    h2: string;
    sub: string;
    items: { icon: string; title: string; body: string }[];
  };
  how: { h2: string; steps: { num: string; title: string; body: string }[] };
  roles: {
    h2: string;
    sub: string;
    blocker: string;
    gives: string;
    items: RoleItem[];
  };
  compliance: {
    h2: string;
    sub: string;
    items: { icon: string; title: string; body: string }[];
  };
  pricing: { h2: string; sub: string; tiers: Tier[]; footnote: string };
  creator: {
    h2: string;
    sub: string;
    benefits: string[];
    cta: string;
    note: string;
  };
  trust: {
    h2: string;
    sub: string;
    items: { title: string; body: string }[];
    orgsLabel: string;
    orgsNote: string;
  };
  faq: { h2: string; items: QA[] };
  form: {
    h2: string;
    sub: string;
    okTitle: string;
    okBody: string;
    fields: Record<string, string>;
    howFoundOptions: string[];
    teamSizes: string[];
    timelines: string[];
    budgets: string[];
    submit: string;
    submitting: string;
    privacy: string;
    errMissing: string;
    errIncompleteEmail: string;
    errGeneric: string;
  };
}

export declare const EN: EnterpriseCopy;
export declare const ZH: EnterpriseCopy;
export declare const ENTERPRISE_ORGS: string[];
