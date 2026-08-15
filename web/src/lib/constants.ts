export const APP_VERSION = "1.2.0";
export const REPO_URL = "https://github.com/rZk1809/FloatChat";
export const AUTHOR = "Rohith Ganesh Kanchi";

export const OCEAN_REGIONS = [
  {
    name: "Bay of Bengal",
    coords: "5-25°N, 80-100°E",
    lat: { min: 5, max: 25 },
    lon: { min: 80, max: 100 },
    color: "cyan",
    desc: "Critical for Indian monsoon dynamics and freshwater flux from major rivers",
    profiles: 1842,
    avgSurfaceTemp: 28.4,
    avgSalinity: 33.1,
  },
  {
    name: "Arabian Sea",
    coords: "5-25°N, 60-80°E",
    lat: { min: 5, max: 25 },
    lon: { min: 60, max: 80 },
    color: "blue",
    desc: "Warm pool region with high salinity and strong evaporation; key for NW monsoon",
    profiles: 1574,
    avgSurfaceTemp: 27.8,
    avgSalinity: 36.4,
  },
  {
    name: "Indian Ocean",
    coords: "60°S-30°N, 20-120°E",
    lat: { min: -60, max: 30 },
    lon: { min: 20, max: 120 },
    color: "teal",
    desc: "Full basin coverage including seasonal thermocline and monsoon upwelling zones",
    profiles: 987,
    avgSurfaceTemp: 25.2,
    avgSalinity: 35.2,
  },
  {
    name: "Southern Ocean",
    coords: "80-40°S, global",
    lat: { min: -80, max: -40 },
    lon: { min: -180, max: 180 },
    color: "indigo",
    desc: "Deep water formation, Antarctic bottom water production, and carbon sink dynamics",
    profiles: 519,
    avgSurfaceTemp: 6.1,
    avgSalinity: 34.7,
  },
] as const;

export const EXAMPLE_QUERIES = [
  "What is a T-S diagram and how does FloatChat generate them?",
  "Explain the temperature profile of the Bay of Bengal",
  "How does the multi-agent RAG system work?",
  "What patterns did clustering reveal in the ARGO data?",
  "What is the thermocline depth in the Arabian Sea?",
  "Compare Bay of Bengal and Arabian Sea salinity profiles",
  "What anomalies did Isolation Forest detect?",
  "How does XGBoost predict ocean temperature?",
] as const;

export const ML_METRICS = [
  { model: "XGBoost Temperature Prediction", metric: "R² Score", value: "0.97", bar: 97 },
  { model: "K-Means Clustering (k=4)", metric: "Silhouette Score", value: "0.71", bar: 71 },
  { model: "Isolation Forest Anomaly", metric: "Contamination", value: "5%", bar: 95 },
  { model: "ARIMA Time Series", metric: "MAPE", value: "< 3%", bar: 97 },
] as const;

export const DATASET_STATS = {
  totalProfiles: 4922,
  totalRegions: 4,
  totalAgents: 4,
  totalVisualizations: 17,
  dateRange: { start: "2000-01", end: "2025-06" },
  depthMax: 2000,
} as const;
