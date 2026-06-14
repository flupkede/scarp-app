/**
 * Scarp API client — typed fetch wrapper.
 * API base URL from Vite env var VITE_PUBLIC_API_URL, defaults to localhost:8000 for dev.
 */

/**
 * API base URL — empty string in production (same-origin via SWA /api proxy),
 * localhost:8000 in dev.  We check for undefined explicitly because the
 * production value is "" (falsy), and `||` would swallow it.
 */
const API_BASE: string =
	import.meta.env.VITE_PUBLIC_API_URL !== undefined
		? import.meta.env.VITE_PUBLIC_API_URL
		: 'http://localhost:8000';

/** Per-zone glacier-dynamics context (ITS_LIVE), attached by the glacier pipeline. */
export interface GlacierContext {
	has_velocity_data: boolean;
	glacier_v_mean: number | null;
	glacier_v_max: number | null;
	glacier_v_trend: number | null;
	glacier_obs_count: number;
	nearest_named_glacier: string | null;
	dist_to_named_glacier_km: number | null;
	nearest_active_ice: string | null;
	dist_to_active_ice_km: number | null;
	glacier_proximity: number;
	glacier_dynamics: number;
	glacier_signal: number;
}

export interface ZoneFeature {
	type: 'Feature';
	properties: {
		id: string;
		rank: number;
		score: number;
		influence_radius_km: number;
		components: {
			susceptibility: number;
			fjord_wall: number;
			volume_proxy: number;
			proximity: number;
			exposure: number;
			coverage: number;
			glacier: number;
			coast_dist_km: number;
		};
		/** Present once the glacier pipeline has run; undefined otherwise. */
		glacier?: GlacierContext;
		/** Distance (km) to the nearest curated Hig inventory slide; set by 55_hig_proximity. */
		nearest_hig_slide_km?: number;
		/** Name of that nearest Hig slide. */
		nearest_hig_slide?: string;
	};
	geometry: GeoJSON.Point;
}

export interface ZoneCollection {
	type: 'FeatureCollection';
	features: ZoneFeature[];
}

export interface SlideFeature {
	type: 'Feature';
	properties: {
		id: number;
		name: string;
		source: string;
	};
	geometry: GeoJSON.Point;
}

export interface StationFeature {
	type: 'Feature';
	properties: {
		network: string;
		station_code: string;
		site_name: string;
	};
	geometry: GeoJSON.Point;
}

export interface NearbySlide {
	id: number;
	name: string;
	source: string;
	distance_km: number;
	geometry: GeoJSON.Point;
}

export interface SearchResponse {
	type: 'FeatureCollection';
	features: ZoneFeature[];
	explanation: string;
}

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
	const url = `${API_BASE}${path}`;
	const res = await fetch(url, init);
	if (!res.ok) {
		throw new Error(`API ${res.status}: ${res.statusText} — ${url}`);
	}
	return res.json();
}

export async function fetchZones(limit = 120): Promise<ZoneCollection> {
	return fetchJSON<ZoneCollection>(`/api/zones?limit=${limit}`);
}

export async function fetchZoneById(id: string): Promise<ZoneFeature> {
	return fetchJSON<ZoneFeature>(`/api/zones/${id}`);
}

export async function fetchNearbySlides(id: string): Promise<NearbySlide[]> {
	return fetchJSON<NearbySlide[]>(`/api/zones/${id}/nearby_slides`);
}

export async function fetchSlides(): Promise<GeoJSON.FeatureCollection> {
	return fetchJSON<GeoJSON.FeatureCollection>('/api/layers/slides');
}

export async function fetchStations(): Promise<GeoJSON.FeatureCollection> {
	return fetchJSON<GeoJSON.FeatureCollection>('/api/layers/stations');
}

export async function searchZones(query: string): Promise<SearchResponse> {
	return fetchJSON<SearchResponse>('/api/search', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ query })
	});
}

/**
 * Fetch the data-confidence layer. Returns null if the file isn't generated yet
 * (404) — the toggle is hidden in that case; no console errors.
 */
export async function fetchConfidence(): Promise<GeoJSON.FeatureCollection | null> {
	const url = `${API_BASE}/api/layers/confidence`;
	try {
		const res = await fetch(url);
		if (res.status === 404) return null;
		if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
		return res.json();
	} catch {
		return null;
	}
}

/**
 * Fetch the ITS_LIVE glacier velocity layer. Returns null if not generated yet
 * (404) — the toggle is hidden in that case; no console errors.
 */
export async function fetchGlacierVelocity(): Promise<GeoJSON.FeatureCollection | null> {
	const url = `${API_BASE}/api/layers/glacier_velocity`;
	try {
		const res = await fetch(url);
		if (res.status === 404) return null;
		if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
		return res.json();
	} catch {
		return null;
	}
}

/** Fetch an optional layer that 404s until its pipeline has run; null on 404/error. */
async function fetchOptionalLayer(path: string): Promise<GeoJSON.FeatureCollection | null> {
	try {
		const res = await fetch(`${API_BASE}${path}`);
		if (res.status === 404) return null;
		if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
		return res.json();
	} catch {
		return null;
	}
}

/** Hig's curated landslide inventory (centroids). */
export async function fetchHigLandslides(): Promise<GeoJSON.FeatureCollection | null> {
	return fetchOptionalLayer('/api/layers/hig_landslides');
}

/** Hig's mapped slide footprints (body/source/deposit polygons). */
export async function fetchHigPolygons(): Promise<GeoJSON.FeatureCollection | null> {
	return fetchOptionalLayer('/api/layers/hig_polygons');
}

/** Hig's survey circles (where he ground-truthed). */
export async function fetchHigSurveyCircles(): Promise<GeoJSON.FeatureCollection | null> {
	return fetchOptionalLayer('/api/layers/hig_survey_circles');
}

/** One glacier's annual velocity series + metadata. */
export interface GlacierTimeseriesPoint {
	point_id: string;
	is_named_glacier: boolean;
	v_mean: number;
	trend_m_yr_per_year: number;
	annual: Array<{ year: number; v_median: number; n: number }>;
	episodes: Array<{ year: number; delta_v: number; direction: 'accelerate' | 'decelerate' }>;
	retreat_tail: boolean;
}

/** Full timeseries dict keyed by point_id. */
export type GlacierTimeseries = Record<string, GlacierTimeseriesPoint>;

/**
 * Fetch the ITS_LIVE glacier velocity timeseries (light charts payload).
 * Returns null if not generated yet (404) — chart hidden in that case.
 * Note: this endpoint returns a plain JSON object, NOT a FeatureCollection.
 */
export async function fetchGlacierTimeseries(): Promise<GlacierTimeseries | null> {
	try {
		const res = await fetch(`${API_BASE}/api/layers/glacier_timeseries`);
		if (res.status === 404) return null;
		if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
		return res.json();
	} catch {
		return null;
	}
}
