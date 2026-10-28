// Cards are ordered by a float "position". Dropping between two cards gives the midpoint,
// so only the moved card is updated: no renumbering of everything else.
export function positionBetween(prev, next) {
  if (prev && next) return (prev.position + next.position) / 2;
  if (prev) return prev.position + 1;
  if (next) return next.position - 1;
  return 1;
}
