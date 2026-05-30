<script lang="ts">
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';
	import { getZoneStore } from '$lib/stores/zones.svelte';
	import { fetchZones, fetchSlides, fetchStations, fetchConfidence, type ZoneFeature } from '$lib/api';
	import MapComponent from '$lib/components/Map.svelte';
	import Splash from '$lib/components/Splash.svelte';
	import PriorityList from '$lib/components/PriorityList.svelte';
	import ZoneDetail from '$lib/components/ZoneDetail.svelte';
	import LayerToggle from '$lib/components/LayerToggle.svelte';
	import SearchBar from '$lib/components/SearchBar.svelte';

	const store = getZoneStore();

	// Data state
	let allSites = $state<ZoneFeature[]>([]);
	let top10Sites = $state<ZoneFeature[]>([]);
	let influenceData = $state<GeoJSON.FeatureCollection>({ type: 'FeatureCollection', features: [] });
	let slidesData = $state<GeoJSON.FeatureCollection>({ type: 'FeatureCollection', features: [] });
	let stationsData = $state<GeoJSON.FeatureCollection>({ type: 'FeatureCollection', features: [] });
	let confidenceData = $state<GeoJSON.FeatureCollection | null>(null);
	let dataReady = $state(false);
	let dataError = $state<string | null>(null);

	// Splash
	let showSplash = $state(true);
	const skipSplash = browser && new URLSearchParams(window.location.search).has('nosplash');

	// Selected site
	let selectedSite = $state<ZoneFeature | null>(null);
	let selectedNearbySlides = $state<any[]>([]);
	let selectedRegion = $state('');
	let selectedIsLowConfidence = $state(false);

	// Search
	let searchExplanation = $state<string | null>(null);
	let searchResultCount = $state<number | null>(null);
	let searchLoading = $state(false);

	// Map ref
	let mapComponent: any = null;

	// API base — shared, using the same logic as api.ts
	const API_BASE: string =
		import.meta.env.VITE_PUBLIC_API_URL !== undefined
			? import.meta.env.VITE_PUBLIC_API_URL
			: 'http://localhost:11000';

	// Layer state (reactive object shared with Map + LayerToggle)
	let layerState = $state({
		showSlides: true,
		showStations: true,
		showInfluence: true,
		showCandidates: true,
		showConfidence: false
	});

	onMount(async () => {
		if (skipSplash) showSplash = false;

		try {
			// Load data from API
			const [zones, slides, stations, confidence] = await Promise.all([
				fetchZones(120),
				fetchSlides(),
				fetchStations(),
				fetchConfidence() // null if not yet generated — handled gracefully
			]);

			allSites = zones.features;
			top10Sites = zones.features.filter((f) => f.properties.rank <= 10);
			slidesData = slides;
			stationsData = stations;
			confidenceData = confidence; // null → toggle hidden in LayerToggle

			// Load influence polygons from API
			try {
				const infRes = await fetch(`${API_BASE}/api/layers/influence`);
				if (infRes.ok) {
					influenceData = await infRes.json();
				} else {
					influenceData = generateInfluenceFromPoints(zones.features);
				}
			} catch {
				influenceData = generateInfluenceFromPoints(zones.features);
			}

			dataReady = true;
		} catch (e: any) {
			dataError = e.message || 'Failed to load data';
			console.error('Data load error:', e);
		}
	});

	function generateInfluenceFromPoints(sites: ZoneFeature[]): GeoJSON.FeatureCollection {
		const features = sites.map((site) => {
			const [lon, lat] = site.geometry.coordinates;
			const radiusKm = site.properties.influence_radius_km || 3;
			const segments = 32;
			const coords: [number, number][] = [];
			for (let i = 0; i <= segments; i++) {
				const angle = (i / segments) * 2 * Math.PI;
				const dLat = (radiusKm / 111) * Math.sin(angle);
				const dLon = (radiusKm / (111 * Math.cos((lat * Math.PI) / 180))) * Math.cos(angle);
				coords.push([lon + dLon, lat + dLat]);
			}
			return {
				type: 'Feature' as const,
				properties: { ...site.properties },
				geometry: {
					type: 'Polygon' as const,
					coordinates: [coords]
				}
			};
		});
		return { type: 'FeatureCollection', features };
	}

	/** Ray-casting point-in-polygon — works for simple (non-self-intersecting) rings. */
	function pointInPolygon(px: number, py: number, ring: number[][]): boolean {
		let inside = false;
		for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
			const xi = ring[i][0], yi = ring[i][1];
			const xj = ring[j][0], yj = ring[j][1];
			const intersect = ((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi);
			if (intersect) inside = !inside;
		}
		return inside;
	}

	function isInLowConfidenceZone(lon: number, lat: number): boolean {
		if (!confidenceData) return false;
		for (const feature of confidenceData.features) {
			if (feature.properties?.band !== 'low') continue;
			const geom = feature.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon;
			if (geom.type === 'Polygon') {
				if (pointInPolygon(lon, lat, geom.coordinates[0] as number[][])) return true;
			} else if (geom.type === 'MultiPolygon') {
				for (const poly of geom.coordinates) {
					if (pointInPolygon(lon, lat, poly[0] as number[][])) return true;
				}
			}
		}
		return false;
	}

	function handleSelectSite(id: string) {
		const site = allSites.find((f) => f.properties.id === id);
		if (site) {
			selectedSite = site;
			const [lon, lat] = site.geometry.coordinates;
			selectedRegion = regionFor(lon, lat);
			selectedIsLowConfidence = isInLowConfidenceZone(lon, lat);

			fetch(`${API_BASE}/api/zones/${id}/nearby_slides`)
				.then((r) => (r.ok ? r.json() : []))
				.then((slides) => { selectedNearbySlides = slides; })
				.catch(() => { selectedNearbySlides = []; });
		}
	}

	function handleSearch(query: string) {
		searchLoading = true;
		fetch(`${API_BASE}/api/search`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ query })
		})
			.then((r) => r.json())
			.then((data) => {
				searchExplanation = data.explanation || null;
				searchResultCount = data.features?.length ?? null;
				searchLoading = false;
			})
			.catch(() => {
				searchExplanation = 'Search unavailable';
				searchResultCount = null;
				searchLoading = false;
			});
	}

	function handleClearSearch() {
		searchExplanation = null;
		searchResultCount = null;
	}

	function regionFor(lon: number, lat: number): string {
		const FJORDS = [
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
		let minDist = Infinity;
		let closest = 'SE Alaska';
		for (const f of FJORDS) {
			const d = Math.sqrt((lon - f.lon) ** 2 + (lat - f.lat) ** 2);
			if (d < minDist) { minDist = d; closest = f.name; }
		}
		return closest;
	}
</script>

<div class="h-screen w-screen overflow-hidden flex flex-col bg-stone-50">
	<!-- Header bar -->
	<header class="h-10 bg-navy flex items-center px-4 justify-between flex-shrink-0 z-50">
		<div class="flex items-center gap-3">
			<h1 class="text-white font-serif font-bold text-lg tracking-wide">SCARP</h1>
			<span class="text-white/40 text-xs">Landslide monitoring placement</span>
		</div>
		<nav class="flex items-center gap-4">
			<a href="/story" class="text-white/50 hover:text-white/80 text-xs">Story</a>
			<a href="/about" class="text-white/50 hover:text-white/80 text-xs">About</a>
		</nav>
	</header>

	<!-- Main content -->
	<div class="flex-1 flex overflow-hidden relative">
		{#if !dataReady && !dataError}
			<div class="flex-1 flex items-center justify-center">
				<div class="text-center">
					<div class="animate-pulse text-2xl font-serif text-ink mb-2">Loading data...</div>
					<p class="text-sm text-stone-400">Fetching zones, slides, and stations</p>
				</div>
			</div>
		{:else if dataError}
			<div class="flex-1 flex items-center justify-center">
				<div class="text-center max-w-md">
					<div class="text-2xl font-serif text-red-700 mb-2">Data load failed</div>
					<p class="text-sm text-stone-600 mb-4">{dataError}</p>
					<p class="text-xs text-stone-400">Make sure the backend is running on port 11000 or set VITE_PUBLIC_API_URL</p>
				</div>
			</div>
		{:else}
			<!-- Sidebar -->
			<aside class="w-72 flex-shrink-0 bg-paper border-r border-stone-200 flex flex-col overflow-hidden z-20">
				<SearchBar
					onSearch={handleSearch}
					loading={searchLoading}
					explanation={searchExplanation}
					resultCount={searchResultCount}
					onClear={handleClearSearch}
				/>
				<div class="flex-1 overflow-hidden">
					<PriorityList sites={allSites} onSelect={handleSelectSite} />
				</div>
				<LayerToggle {layerState} hasConfidence={confidenceData !== null} />
			</aside>

			<!-- Map area — faint USGS Tracy Arm photo behind a floating ~90% map -->
			<div class="flex-1 relative flex items-center justify-center map-stage">
				<div class="map-frame">
					<MapComponent
						{layerState}
						sites={{ type: 'FeatureCollection', features: allSites }}
						top10={top10Sites.map((f) => ({
							type: 'Feature' as const,
							properties: f.properties,
							geometry: f.geometry
						}))}
						influenceGeojson={influenceData}
						slides={slidesData}
						stations={stationsData}
						confidence={confidenceData}
						onSelectSite={handleSelectSite}
					/>
				</div>

				{#if selectedSite}
					<ZoneDetail
						site={selectedSite}
						nearbySlides={selectedNearbySlides}
						regionLabel={selectedRegion}
						isLowConfidence={selectedIsLowConfidence}
						onClose={() => {
							selectedSite = null;
							selectedNearbySlides = [];
							selectedIsLowConfidence = false;
						}}
					/>
				{/if}
			</div>
		{/if}
	</div>
</div>

<!-- Splash overlay -->
{#if showSplash && !skipSplash}
	<Splash onDismiss={() => (showSplash = false)} />
{/if}

<style>
	/* Faint USGS Tracy Arm photo behind the floating map */
	.map-stage {
		background-color: #1c1917;
		background-image: linear-gradient(rgba(28, 25, 23, 0.82), rgba(28, 25, 23, 0.82)),
			url('/splash-tracy-arm.jpg');
		background-size: cover;
		background-position: center;
		padding: 1.25rem;
	}

	/* The map floats at ~90% of the stage, framed and lifted off the photo */
	.map-frame {
		width: 90%;
		height: 90%;
		border-radius: 0.75rem;
		overflow: hidden;
		box-shadow:
			0 10px 40px -8px rgba(0, 0, 0, 0.55),
			0 0 0 1px rgba(255, 255, 255, 0.06);
	}
</style>
