import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

export function CardView({ card, dragging }) {
  return (
    <div className={`card${dragging ? " card-overlay" : ""}`}>
      <div className="card-title">{card.title}</div>
      {card.description && <div className="card-desc">{card.description}</div>}
    </div>
  );
}

export default function CardItem({ card, onOpen }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: `c${card.id}` });
  const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.35 : 1 };
  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}
         onClick={() => onOpen(card)} data-testid={`card-${card.title}`}>
      <CardView card={card} />
    </div>
  );
}
