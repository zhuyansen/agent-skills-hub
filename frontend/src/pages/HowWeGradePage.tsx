import { ProsePage } from "../components/ProsePage";
import { useI18n } from "../i18n/I18nContext";
import { HOW_WE_GRADE } from "../lib/howWeGradeContent.mjs";
import { HOW_WE_GRADE_META, HOW_WE_GRADE_UPDATED, HOW_WE_GRADE_URL } from "../lib/howWeGradeMeta.mjs";

/** /how-we-grade/: how security grades, quality scores and rankings are made. */
export function HowWeGradePage() {
  const { lang } = useI18n();
  const meta = { ...HOW_WE_GRADE_META[lang], url: HOW_WE_GRADE_URL };
  return <ProsePage lang={lang} meta={meta} text={HOW_WE_GRADE} date={HOW_WE_GRADE_UPDATED} />;
}
