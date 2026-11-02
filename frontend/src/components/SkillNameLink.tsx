import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface Props {
  repo: string;
  children: ReactNode;
}

/** A skill's name as a real link to its page. The cards around it navigate on
 *  click too, but a div's click handler gives Google no URL to follow; this
 *  anchor does. It inherits the card's text styles (Tailwind's preflight sets
 *  color and text-decoration to inherit on <a>), and it stops the click so the
 *  card's own handler doesn't navigate a second time. */
export function SkillNameLink({ repo, children }: Props) {
  return (
    <Link to={`/skill/${repo}/`} onClick={(e) => e.stopPropagation()}>
      {children}
    </Link>
  );
}
