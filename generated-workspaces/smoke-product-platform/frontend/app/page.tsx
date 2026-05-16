import { fetchProduct } from "./lib/api";

export default async function Home() {
  const product = await fetchProduct();
  const features = product.features ?? [];

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-16">
        <div className="max-w-3xl">
          <p className="text-sm uppercase tracking-[0.32em] text-cyan-300">AI generated SaaS</p>
          <h1 className="mt-5 text-5xl font-semibold tracking-tight md:text-7xl">{product.name}</h1>
          <p className="mt-6 text-lg leading-8 text-slate-300">{product.description}</p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {features.map((feature: string) => (
            <article key={feature} className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
              <div className="text-sm font-medium text-cyan-200">{feature}</div>
              <p className="mt-3 text-sm leading-6 text-slate-400">Built into the generated workspace and backed by the API.</p>
            </article>
          ))}
        </div>
        <div className="mt-10 rounded-lg border border-cyan-400/20 bg-cyan-400/10 p-5 text-sm text-cyan-50">
          Backend status: {product.status}. API base URL is configured through NEXT_PUBLIC_API_BASE_URL.
        </div>
      </section>
    </main>
  );
}
