export default function Loading() {
  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-12">
      <div className="animate-pulse space-y-3">
        <div className="h-24 bg-line/40" />
        <div className="h-40 bg-line/40" />
      </div>
    </main>
  );
}