export async function fetchProduct() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  try {
    const response = await fetch(`${baseUrl}/api/product`, { cache: "no-store" });
    if (!response.ok) throw new Error("API unavailable");
    return response.json();
  } catch {
    return {
      name: "Generated Product",
      description: "The frontend is running. Start the FastAPI backend to load live product data.",
      status: "offline fallback",
      features: ["Product dashboard", "API integration", "Deployable codebase"],
    };
  }
}
