import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { HOW_WE_GRADE_LINK, HOW_WE_GRADE_PATH } from "../lib/howWeGradeMeta.mjs";

interface Props {
  className: string;
  /** Section of the page to open at, e.g. the grade table. */
  anchor?: string;
  /** Ends the label with " →", for a link that follows a sentence. */
  arrow?: boolean;
}

/** The small "How we grade" link to /how-we-grade/ (footer, security badge, analyzer). */
export function HowWeGradeLink({ className, anchor, arrow = false }: Props) {
  const { lang } = useI18n();
  const to = anchor ? `${HOW_WE_GRADE_PATH}#${anchor}` : HOW_WE_GRADE_PATH;
  return (
    <Link to={to} className={className}>
      {HOW_WE_GRADE_LINK[lang]}
      {arrow && " →"}
    </Link>
  );
}
