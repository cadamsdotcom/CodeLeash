import { GreetingList } from '../components/GreetingList';
import { useInitialData } from '../hooks/useInitialData';
import { IndexPageData } from '../types/initial-data';

export default function Index() {
  const data = useInitialData<IndexPageData>();
  const greetings = data.greetings ?? [];

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-bg-grey">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-4 text-2xl font-bold text-brand-dark-grey">
          CodeLeash
        </h1>
        <GreetingList greetings={greetings} />
      </div>
    </div>
  );
}
