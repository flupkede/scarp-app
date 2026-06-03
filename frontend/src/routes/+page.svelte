<script lang="ts">
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

	// Splash — only show while data is loading
	let showSplash = $state(true);

	// Sidebar toggle for mobile
	let sidebarOpen = $state(false);

	// Global Escape listener for sidebar overlay
	$effect(() => {
		if (!sidebarOpen) return;
		function onKey(e: KeyboardEvent) {
			if (e.key === 'Escape') sidebarOpen = false;
		}
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});

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
		showSlides: false,
		showStations: true,
		showInfluence: true,
		showCandidates: true,
		showConfidence: true
	});

	onMount(async () => {
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
		sidebarOpen = false;
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
	<header class="h-11 flex items-center px-4 justify-between flex-shrink-0 z-50" style="background:#0f172a">
		<div class="flex items-center gap-3">
			{#if dataReady && !dataError}
				<button
					class="sm:hidden text-white/70 hover:text-white p-1 -ml-1"
					onclick={() => (sidebarOpen = !sidebarOpen)}
					aria-label="Toggle menu"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						{#if sidebarOpen}
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
						{:else}
							<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/>
						{/if}
					</svg>
				</button>
			{/if}
			<h1 class="text-white font-serif font-bold text-lg tracking-wide">SCARP</h1>
			<span class="hidden sm:inline text-white/40 text-xs">Landslide sensor placement</span>
		</div>
		<nav class="flex items-center gap-3">
			<a href="/story" class="text-white/60 hover:text-white text-xs px-2 py-1 rounded hover:bg-white/10 transition-colors">Story</a>
			<a href="/about" class="text-white/60 hover:text-white text-xs px-2 py-1 rounded hover:bg-white/10 transition-colors">About</a>
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
			<!-- Mobile backdrop -->
			{#if sidebarOpen}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<button
					class="fixed inset-0 bg-black/40 z-20 sm:hidden cursor-default"
					onclick={() => (sidebarOpen = false)}
					aria-label="Close menu"
				></button>
			{/if}

			<!-- Sidebar: fixed overlay on mobile, inline on desktop -->
			<aside
				class="sidebar w-72 flex-shrink-0 bg-paper border-r border-stone-200 flex flex-col overflow-hidden z-20
					fixed top-11 left-0 bottom-0 transition-transform duration-200
					{sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
					sm:static sm:translate-x-0"
			>
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

			<!-- Map area — full 100% -->
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
					confidence={confidenceData}
					onSelectSite={handleSelectSite}
				/>

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

<!-- Splash overlay — only visible while loading -->
{#if showSplash}
	<Splash {dataReady} onDismiss={() => (showSplash = false)} />
{/if}
