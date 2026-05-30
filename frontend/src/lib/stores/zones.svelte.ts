/**
 * Zones store — Svelte 5 runes state management.
 * Holds all candidate sites, the selected site, top-10, and search state.
 */
import {
	fetchZones,
	fetchNearbySlides,
	searchZones,
	type ZoneFeature,
	type NearbySlide,
	type SearchResponse
} from '$lib/api';

// --- Fjord/region lookup (hardcoded centroids, spec §8) ---
interface FjordRef {
	name: string;
	lon: number;
	lat: number;
}

const FJORDS: FjordRef[] = [
	{ name: 'Lituya Bay', lon: -137.7, lat: 58.65 },
	{ name: 'Barry Arm', lon: -148.15, lat: 61.15 },
	{ name: 'Tracy Arm', lon: -133.55, lat: 57.85 },
	{ name: 'Portage Lake', lon: -148.85, lat: 60.78 },
	{ name: 'Pedersen Bay', lon: -149.3, lat: 60.05 },
	{ name: 'Glacier Bay', lon: -136.5, lat: 58.65 },
	{ name: 'Icy Bay', lon: -141.5, lat: 60.1 },
	{ name: 'Yakutat Bay', lon: -139.8, lat: 59.6 },
	{ name: 'Turnagain Arm', lon: -149.7, lat: 60.9 },
	{ name: 'Sitka', lon: -135.3, lat: 57.05 },
	{ name: 'Seward', lon: -149.45, lat: 60.1 },
	{ name: 'Haines', lon: -135.45, lat: 59.25 },
	{ name: 'Skagway', lon: -135.3, lat: 59.45 },
	{ name: 'Juneau', lon: -134.4, lat: 58.3 },
	{ name: 'Valdez', lon: -146.35, lat: 61.15 },
	{ name: 'Whittier', lon: -148.7, lat: 60.8 },
	{ name: 'Ketchikan', lon: -131.65, lat: 55.35 }
];

function getRegionLabel(lon: number, lat: string | number): string {
	const latNum = typeof lat === 'string' ? parseFloat(lat) : lat;
	let minDist = Infinity;
	let closest = 'SE Alaska';
	for (const fjord of FJORDS) {
		const d = Math.sqrt((lon - fjord.lon) ** 2 + (latNum - fjord.lat) ** 2);
		if (d < minDist) {
			minDist = d;
			closest = fjord.name;
		}
	}
	return closest;
}

// --- Store state ---

let allSites = $state<ZoneFeature[]>([]);
let top10 = $state<ZoneFeature[]>([]);
let selectedId = $state<string | null>(null);
let selectedSite = $state<ZoneFeature | null>(null);
let nearbySlides = $state<NearbySlide[]>([]);
let loading = $state(false);
let error = $state<string | null>(null);
let searchResult = $state<SearchResponse | null>(null);
let searchLoading = $state(false);

// --- Computed ---

function regionFor(lon: number, lat: number): string {
	return getRegionLabel(lon, lat);
}

// --- Actions ---

async function loadSites(): Promise<void> {
	loading = true;
	error = null;
	try {
		const collection = await fetchZones(120);
		allSites = collection.features;
		top10 = allSites.filter((f) => f.properties.rank <= 10);
	} catch (e: unknown) {
		error = e instanceof Error ? e.message : 'Failed to load sites';
	} finally {
		loading = false;
	}
}

async function selectSite(id: string): Promise<void> {
	const site = allSites.find((f) => f.properties.id === id) ?? null;
	selectedId = id;
	selectedSite = site;
	nearbySlides = [];
	if (site) {
		try {
			nearbySlides = await fetchNearbySlides(id);
		} catch {
			// Graceful — nearby slides are optional
		}
	}
}

function clearSelection(): void {
	selectedId = null;
	selectedSite = null;
	nearbySlides = [];
}

async function search(query: string): Promise<void> {
	searchLoading = true;
	try {
		searchResult = await searchZones(query);
	} catch {
		searchResult = null;
	} finally {
		searchLoading = false;
	}
}

function clearSearch(): void {
	searchResult = null;
}

export function getZoneStore() {
	return {
		get allSites() {
			return allSites;
		},
		get top10() {
			return top10;
		},
		get selectedId() {
			return selectedId;
		},
		get selectedSite() {
			return selectedSite;
		},
		get nearbySlides() {
			return nearbySlides;
		},
		get loading() {
			return loading;
		},
		get error() {
			return error;
		},
		get searchResult() {
			return searchResult;
		},
		get searchLoading() {
			return searchLoading;
		},
		regionFor,
		loadSites,
		selectSite,
		clearSelection,
		search,
		clearSearch
	};
}
