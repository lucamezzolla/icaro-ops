const STORAGE_KEY = "icaro-ops.state.v1";

function readState() {
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY)) ?? {};
  } catch {
    return {};
  }
}

function writeState(state) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export const gameState = {
  hasAirline() {
    return Boolean(readState().airline);
  },

  getAirline() {
    return readState().airline;
  },

  createAirline(airline) {
    const state = readState();
    state.airline = airline;
    state.lastSimulatedAtUtc = new Date().toISOString();
    writeState(state);
  },

  reset() {
    window.localStorage.removeItem(STORAGE_KEY);
  }
};
