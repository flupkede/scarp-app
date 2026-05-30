<script lang="ts">
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';
	import { getZoneStore } from '$lib/stores/zones.svelte';
	import { fetchZones, fetchSlides, fetchStations, searchZones, type ZoneFeature } from '$lib/api';
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
	let dataReady = $state(false);
	let dataError = $state<string | null>(null);

	// Splash
	let showSplash = $state(true);
	const skipSplash = browser && new URLSearchParams(window.location.search).has('nosplash');

	// Selected site
	let selectedSite = $state<ZoneFeature | null>(null);
	let selectedNearbySlides = $state<any[]>([]);
	let selectedRegion = $state('');

	// Search
	let searchExplanation = $state<string | null>(null);
	let searchResultCount = $state<number | null>(null);
	let searchLoading = $state(false);

	// Map ref
	let mapComponent: any = null;

	// Layer state (reactive object shared with Map + LayerToggle)
	let layerState = $state({
		showSlides: true,
		showStations: true,
		showInfluence: true,
		showCandidates: true
	});

	onMount(async () => {
		if (skipSplash) showSplash = false;

		try {
			// Load data from API
			const [zones, slides, stations] = await Promise.all([
				fetchZones(120),
				fetchSlides(),
				fetchStations()
			]);

			allSites = zones.features;
			top10Sites = zones.features.filter((f) => f.properties.rank <= 10);
			slidesData = slides;
			stationsData = stations;

			// Load influence polygons from API too
			// The API /api/zones returns points; influence polygons come from /api/layers/influence
			// For now, build them from the same source
			try {
				const API_BASE = import.meta.env.VITE_PUBLIC_API_URL || 'http://localhost:8000';
				const infRes = await fetch(`${API_BASE}/api/layers/influence`);
				if (infRes.ok) {
					influenceData = await infRes.json();
				} else {
					// Fallback: generate circle polygons from points (3km radius)
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
		// Simple circle generation: 32-sided polygon at ~3km radius
		// Approximate: 1 degree lat ≈ 111km, 1 degree lon ≈ 111km * cos(lat)
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

	function handleSelectSite(id: string) {
		const site = allSites.find((f) => f.properties.id === id);
		if (site) {
			selectedSite = site;
			const coords = site.geometry.coordinates;
			selectedRegion = regionFor(coords[0], coords[1]);

			// Fetch nearby slides
			const API_BASE = import.meta.env.VITE_PUBLIC_API_URL || 'http://localhost:8000';
			fetch(`${API_BASE}/api/zones/${id}/nearby_slides`)
				.then((r) => (r.ok ? r.json() : []))
				.then((slides) => {
					selectedNearbySlides = slides;
				})
				.catch(() => {
					selectedNearbySlides = [];
				});
		}
	}

	function handleSearch(query: string) {
		searchLoading = true;
		const API_BASE = import.meta.env.VITE_PUBLIC_API_URL || 'http://localhost:8000';
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

	// Region lookup (same as in store, duplicated to avoid import issues)
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
			if (d < minDist) {
				minDist = d;
				closest = f.name;
			}
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
		<a href="/about" class="text-white/50 hover:text-white/80 text-xs">About</a>
	</header>

	<!-- Main content -->
	<div class="flex-1 flex overflow-hidden relative">
		{#if !dataReady && !dataError}
			<!-- Loading state -->
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
					<p class="text-xs text-stone-400">Make sure the backend is running on port 8000 or set VITE_PUBLIC_API_URL</p>
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
				<LayerToggle {layerState} />
			</aside>

			<!-- Map area -->
			<div class="flex-1 relative">
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
					onSelectSite={handleSelectSite}
				/>

				<!-- Detail panel (slide in from right) -->
				{#if selectedSite}
					<ZoneDetail
						site={selectedSite}
						nearbySlides={selectedNearbySlides}
						regionLabel={selectedRegion}
						onClose={() => {
							selectedSite = null;
							selectedNearbySlides = [];
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
