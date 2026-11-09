import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { SiteHeader } from "./SiteHeader";
import { SiteFooter } from "./SiteFooter";
import { HowWeGradeBlocks } from "./HowWeGradeBlocks";
import { ExternalRelContext } from "../lib/externalRel";
import {
  CLASSES,
  EXTERNAL_REL,
  pick,
  type Lang,
  type ProsePageText,
  type Section,
} from "../lib/proseContent.mjs";

/**
 * A long-form page of the site, /how-we-grade/ or /agent-skills-directories/, from its text in
 * `lang`. The static copy that crawlers read (scripts/prose-page-html.mjs) has the same markup,
 * with the English pair of the meta tags.
 */

export interface ProsePageMeta {
  title: string;
  description: string;
  url: string;
}

interface Props {
  lang: Lang;
  meta: ProsePageMeta;
  text: ProsePageText;
  /** The date after the page's "updated" label. */
  date: string;
  /** rel of links to other sites. */
  rel?: string;
}

interface TextProps {
  text: ProsePageText;
  lang: Lang;
}

function Meta({ meta }: { meta: ProsePageMeta }) {
  const { title, description, url } = meta;
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={url} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="article" />
      <meta property="og:url" content={url} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
    </Helmet>
  );
}

function Crumbs({ text, lang }: TextProps) {
  return (
    <nav className={CLASSES.crumbs} aria-label="Breadcrumb">
      <Link to="/" className={CLASSES.crumbLink}>
        {pick(text.crumbs.home, lang)}
      </Link>
      <span className={CLASSES.crumbSep}>&gt;</span>
      <span className={CLASSES.crumbHere}>{pick(text.crumbs.here, lang)}</span>
    </nav>
  );
}

function PageHeader({ text, lang, date }: TextProps & { date: string }) {
  return (
    <header className={CLASSES.header}>
      <h1 className={CLASSES.h1}>{pick(text.h1, lang)}</h1>
      <p className={CLASSES.updated}>
        {pick(text.updated, lang)}
        <time dateTime={date}>{date}</time>
      </p>
    </header>
  );
}

function SectionView({ section, lang }: { section: Section; lang: Lang }) {
  return (
    <section id={section.id} className={CLASSES.section}>
      <h2>{pick(section.title, lang)}</h2>
      <HowWeGradeBlocks blocks={section.blocks} lang={lang} />
    </section>
  );
}

function Article({ text, lang }: TextProps) {
  return (
    <article className={CLASSES.article}>
      <HowWeGradeBlocks blocks={text.lead} lang={lang} />
      {text.sections.map((section) => (
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

export function ProsePage({ lang, meta, text, date, rel = EXTERNAL_REL }: Props) {
  const { hash } = useLocation();
  useScrollTarget(hash);
  return (
    <ExternalRelContext.Provider value={rel}>
      <div className={CLASSES.page}>
        <Meta meta={meta} />
        <SiteHeader />
        <main className={CLASSES.main}>
          <Crumbs text={text} lang={lang} />
          <PageHeader text={text} lang={lang} date={date} />
          <Article text={text} lang={lang} />
        </main>
        <SiteFooter />
      </div>
    </ExternalRelContext.Provider>
  );
}
