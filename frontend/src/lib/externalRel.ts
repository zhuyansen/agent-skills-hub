import { createContext } from "react";
import { EXTERNAL_REL } from "./proseContent.mjs";

/**
 * The rel a prose link to another site gets (src/components/HowWeGradeBlocks.tsx). A page
 * that does not vouch for the sites it links, such as the directory comparison, provides
 * NOFOLLOW_REL around its text.
 */
export const ExternalRelContext = createContext(EXTERNAL_REL);
