import { useContext, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { ExternalRelContext } from "../lib/externalRel";
import {
  CLASSES,
  inlineTokens,
  linkKind,
  pick,
  type Block,
  type InlineToken,
  type Lang,
  type NoteBlock,
  type TableBlock,
  type Text,
} from "../lib/proseContent.mjs";

/**
 * React renderer for the blocks of a long-form page: /how-we-grade/ (src/lib/howWeGradeContent.mjs)
 * and /agent-skills-directories/ (src/lib/directoriesContent.mjs). Its markup matches what
 * scripts/prose-page-html.mjs pre-renders, so swapping the static copy for this one changes
 * nothing on screen.
 */

interface LangProps {
  lang: Lang;
}

/** App paths go through the router, other addresses on this site load in full, other sites open in a new tab. */
function TextLink({ href, children }: { href: string; children: ReactNode }) {
  const rel = useContext(ExternalRelContext);
  const kind = linkKind(href);
  if (kind === "route") return <Link to={href}>{children}</Link>;
  if (kind === "page") return <a href={href}>{children}</a>;
  return (
    <a href={href} target="_blank" rel={rel}>
      {children}
    </a>
  );
}

function Token({ token }: { token: InlineToken }) {
  if (token.kind === "link") return <TextLink href={token.href}>{token.text}</TextLink>;
  if (token.kind === "strong") return <strong>{token.text}</strong>;
  if (token.kind === "em") return <em>{token.text}</em>;
  if (token.kind === "code") return <code>{token.text}</code>;
  if (token.kind === "br") return <br />;
  return <>{token.text}</>;
}

/** One line of the page text in `lang`, with its inline markup rendered. */
function Inline({ text, lang }: LangProps & { text: Text }) {
  const tokens = inlineTokens(pick(text, lang));
  return (
    <>
      {tokens.map((token, i) => (
        <Token key={i} token={token} />
      ))}
    </>
  );
}

function Row({ cells, head, lang }: LangProps & { cells: readonly Text[]; head?: boolean }) {
  const Cell = head ? "th" : "td";
  return (
    <tr>
      {cells.map((cell, i) => (
        <Cell key={i} scope={head ? "col" : undefined}>
          <Inline text={cell} lang={lang} />
        </Cell>
      ))}
    </tr>
  );
}

/** Wider than the screen, a table scrolls inside its own box; the page never scrolls sideways. */
function Table({ table, lang }: LangProps & { table: TableBlock }) {
  const width = table.minRem ? { minWidth: `${table.minRem}rem` } : undefined;
  const box = table.wide ? `${CLASSES.tableWrap} ${CLASSES.tableWide}` : CLASSES.tableWrap;
  return (
    <div className={box} role="region" aria-label={pick(table.label, lang)} tabIndex={0}>
      <table style={width}>
        <thead>
          <Row cells={table.head} head lang={lang} />
        </thead>
        <tbody>
          {table.rows.map((row, i) => (
            <Row key={i} cells={row} lang={lang} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function List({ items, lang }: LangProps & { items: readonly Text[] }) {
  return (
    <ul className={CLASSES.list}>
      {items.map((item, i) => (
        <li key={i}>
          <Inline text={item} lang={lang} />
        </li>
      ))}
    </ul>
  );
}

function Note({ note, lang }: LangProps & { note: NoteBlock }) {
  const title = pick(note.title, lang);
  return (
    <aside className={CLASSES.note} aria-label={title}>
      <p>
        <strong>{title}</strong>
      </p>
      <List items={note.items} lang={lang} />
    </aside>
  );
}

function BlockView({ block, lang }: LangProps & { block: Block }) {
  if (block.type === "p") return <p><Inline text={block.text} lang={lang} /></p>;
  if (block.type === "h3") {
    const anchor = block.id ? CLASSES.anchor : undefined;
    return <h3 id={block.id} className={anchor}><Inline text={block.text} lang={lang} /></h3>;
  }
  if (block.type === "ul") return <List items={block.items} lang={lang} />;
  if (block.type === "note") return <Note note={block} lang={lang} />;
  return <Table table={block} lang={lang} />;
}

export function HowWeGradeBlocks({ blocks, lang }: LangProps & { blocks: readonly Block[] }) {
  return (
    <>
      {blocks.map((block, i) => (
        <BlockView key={i} block={block} lang={lang} />
      ))}
    </>
  );
}
