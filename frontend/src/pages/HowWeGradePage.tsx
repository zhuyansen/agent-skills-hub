import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { HowWeGradeBlocks } from "../components/HowWeGradeBlocks";
import { useI18n } from "../i18n/I18nContext";
import { CLASSES, HOW_WE_GRADE, pick, type Section } from "../lib/howWeGradeContent.mjs";
import {
  HOW_WE_GRADE_META,
  HOW_WE_GRADE_UPDATED,
  HOW_WE_GRADE_URL,
  type HowWeGradeLang,
} from "../lib/howWeGradeMeta.mjs";

interface LangProps {
  lang: HowWeGradeLang;
}

/** The static page (scripts/generate-how-we-grade-page.mjs) ships the English pair of these. */
function Meta({ lang }: LangProps) {
  const { title, description } = HOW_WE_GRADE_META[lang];
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={HOW_WE_GRADE_URL} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="article" />
      <meta property="og:url" content={HOW_WE_GRADE_URL} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
    </Helmet>
  );
}

function Crumbs({ lang }: LangProps) {
  return (
    <nav className={CLASSES.crumbs} aria-label="Breadcrumb">
      <Link to="/" className={CLASSES.crumbLink}>
        {pick(HOW_WE_GRADE.crumbs.home, lang)}
      </Link>
      <span className={CLASSES.crumbSep}>&gt;</span>
      <span className={CLASSES.crumbHere}>{pick(HOW_WE_GRADE.crumbs.here, lang)}</span>
    </nav>
  );
}

function PageHeader({ lang }: LangProps) {
  return (
    <header className={CLASSES.header}>
      <h1 className={CLASSES.h1}>{pick(HOW_WE_GRADE.h1, lang)}</h1>
      <p className={CLASSES.updated}>
        {pick(HOW_WE_GRADE.updated, lang)}
        <time dateTime={HOW_WE_GRADE_UPDATED}>{HOW_WE_GRADE_UPDATED}</time>
      </p>
    </header>
  );
}

function SectionView({ section, lang }: LangProps & { section: Section }) {
  return (
    <section id={section.id} className={CLASSES.section}>
      <h2>{pick(section.title, lang)}</h2>
      <HowWeGradeBlocks blocks={section.blocks} lang={lang} />
    </section>
  );
}

function Article({ lang }: LangProps) {
  return (
    <article className={CLASSES.article}>
      <HowWeGradeBlocks blocks={HOW_WE_GRADE.lead} lang={lang} />
      {HOW_WE_GRADE.sections.map((section) => (
        <SectionView key={section.id} section={section} lang={lang} />
      ))}
    </article>
  );
}

/** Opens at #section when a link points into the page (the badge opens the grade table), else at the top. */
function useScrollTarget(hash: string) {
  useEffect(() => {
    const target = hash ? document.getElementById(decodeURIComponent(hash.slice(1))) : null;
    if (target) target.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [hash]);
}

/** /how-we-grade/: how security grades, quality scores and rankings are made. */
export function HowWeGradePage() {
  const { lang } = useI18n();
  const { hash } = useLocation();
  useScrollTarget(hash);
  return (
    <div className={CLASSES.page}>
      <Meta lang={lang} />
      <SiteHeader />
      <main className={CLASSES.main}>
        <Crumbs lang={lang} />
        <PageHeader lang={lang} />
        <Article lang={lang} />
      </main>
      <SiteFooter />
    </div>
  );
}
