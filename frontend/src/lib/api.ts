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
			slope_factor: number;
			proximity: number;
			exposure: number;
			coverage: number;
			coast_dist_km: number;
		};
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
