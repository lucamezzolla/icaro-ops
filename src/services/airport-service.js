export async function loadStarterAirports() {
  const response = await fetch("./data/airports-seed.json");

  if (!response.ok) {
    throw new Error(`Unable to load starter airports: ${response.status}`);
  }

  return response.json();
}
