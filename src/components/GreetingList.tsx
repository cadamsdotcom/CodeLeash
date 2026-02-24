interface Greeting {
  id: string;
  message: string;
  created_at: string;
}

interface GreetingListProps {
  greetings: Greeting[];
}

export function GreetingList({ greetings }: GreetingListProps) {
  if (greetings.length === 0) {
    return <p className="text-brand-mid-grey">No greetings yet.</p>;
  }
  return (
    <ul className="space-y-2">
      {greetings.map(g => (
        <li
          key={g.id}
          className="rounded bg-brand-bg-grey p-3 text-brand-dark-grey"
        >
          {g.message}
        </li>
      ))}
    </ul>
  );
}
