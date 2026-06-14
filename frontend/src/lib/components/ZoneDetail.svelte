<script lang="ts">
	import type { ZoneFeature, NearbySlide } from '$lib/api';

	let { site, nearbySlides, regionLabel, isLowConfidence = false, onClose }: {
		site: ZoneFeature;
		nearbySlides: NearbySlide[];
		regionLabel: string;
		/** True when the site falls within a low-confidence data band. */
		isLowConfidence?: boolean;
		onClose: () => void;
	} = $props();

	let components = $derived(site.properties.components);

	let componentItems = $derived([
		{ key: 'susceptibility', label: 'Susceptibility', value: components.susceptibility },
		{ key: 'fjord_wall', label: 'Fjord wall', value: components.fjord_wall },
		{ key: 'proximity', label: 'Proximity', value: components.proximity },
		{ key: 'volume_proxy', label: 'Volume potential', value: components.volume_proxy },
		{ key: 'glacier', label: 'Glacier dynamics', value: components.glacier ?? 0 },
		{ key: 'exposure', label: 'Exposure', value: components.exposure },
		{ key: 'coverage', label: 'Coverage', value: components.coverage }
	]);

	// Glacier context (ITS_LIVE) — present once the glacier pipeline has run.
	let glacier = $derived(site.properties.glacier);

	let rankColor = $derived(
		site.properties.rank <= 10
			? 'text-red-600'
			: site.properties.rank <= 30
				? 'text-orange-500'
				: 'text-amber-500'
	);

	/** Return the nearest named fjord/region for a slide coordinate. */
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
	function nearestFjord(lon: number, lat: number): string {
		let minDist = Infinity;
		let closest = 'SE Alaska';
		for (const f of FJORDS) {
			const d = Math.sqrt((lon - f.lon) ** 2 + (lat - f.lat) ** 2);
			if (d < minDist) { minDist = d; closest = f.name; }
		}
		return closest;
	}

	/** Map a raw source code to a short badge label + an explanatory tooltip. */
	function sourceBadge(source: string | undefined): { label: string; title: string } {
		switch ((source || '').toLowerCase()) {
			case 'dggs':
				return {
					label: 'DGGS',
					title: 'Alaska Division of Geological & Geophysical Surveys — state landslide inventory'
				};
			case 'usgs':
				return {
					label: 'USGS',
					title: 'U.S. Geological Survey — federal landslide records'
				};
			case 'usfs':
				return {
					label: 'USFS',
					title: 'U.S. Forest Service — Tongass National Forest landslide mapping'
				};
			default:
				return {
					label: 'OTHER',
					title: 'Other / unattributed data source'
				};
		}
	}
</script>

<div class="absolute top-0 right-0 h-full w-full sm:w-80 shadow-2xl z-40 flex flex-col overflow-hidden" style="background: rgba(255,255,255,0.65); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-left: 1px solid rgba(255,255,255,0.3);">
	<!-- Header -->
	<div class="px-4 py-4 flex items-start justify-between" style="border-bottom: 1px solid rgba(120,113,108,0.15);">
		<div>
			<h3 class="font-serif font-bold text-lg text-ink">
				SITE #{site.properties.rank} <span class="text-stone-500 text-sm">— {regionLabel}</span>
			</h3>
			<p class="text-xs text-stone-500 mt-1">ID: {site.properties.id}</p>
		</div>
		<button
			onclick={onClose}
			class="text-stone-400 hover:text-ink text-xl leading-none p-1"
			aria-label="Close"
		>
			&times;
		</button>
	</div>

	<!-- Low-confidence warning -->
	{#if isLowConfidence}
		<div class="mx-4 mt-3 px-3 py-2 bg-stone-100 border border-stone-300 rounded text-xs text-stone-600 flex gap-2 items-start">
			<span class="text-lg leading-none mt-0.5">▨</span>
			<span>This site sits in a <strong>data-limited area</strong>. Public data coverage here is thin — treat this ranking as provisional.</span>
		</div>
	{/if}

	<!-- Scores -->
	<div class="px-4 py-3 border-b border-stone-200 {isLowConfidence ? '' : 'mt-3'}">
		<div class="grid grid-cols-3 gap-2 text-center">
			<div>
				<div class="text-xs text-stone-500 uppercase tracking-wide">Score</div>
				<div class="text-lg font-bold {rankColor}">{site.properties.score.toFixed(3)}</div>
			</div>
			<div>
				<div class="text-xs text-stone-500 uppercase tracking-wide">Rank</div>
				<div class="text-lg font-bold text-ink">{site.properties.rank} / 120</div>
			</div>
			<div>
				<div class="text-xs text-stone-500 uppercase tracking-wide">Radius</div>
				<div class="text-lg font-bold text-ink">{site.properties.influence_radius_km} km</div>
			</div>
		</div>
	</div>

	<!-- Component breakdown -->
	<div class="flex-1 overflow-y-auto px-4 py-3">
		<h4 class="font-serif font-semibold text-sm text-ink mb-3 uppercase tracking-wide">Why this site?</h4>

		<div class="space-y-2">
			{#each componentItems as item}
				<div>
					<div class="flex justify-between text-xs mb-0.5">
						<span class="text-stone-600">{item.label}</span>
						<span class="font-mono text-ink">{item.value.toFixed(2)}</span>
					</div>
					<div class="h-2 bg-stone-200 rounded-full overflow-hidden">
						<div
							class="h-full bg-amber-500 rounded-full"
							style="width: {item.value * 100}%"
						></div>
					</div>
				</div>
			{/each}
		</div>

		<div class="mt-3 text-xs text-stone-500">
			Coast distance: {components.coast_dist_km.toFixed(1)} km
		</div>

		<!-- Glacier context (ITS_LIVE) -->
		{#if glacier}
			<h4 class="font-serif font-semibold text-sm text-ink mt-5 mb-2 uppercase tracking-wide">
				Glacier dynamics
			</h4>
			<div class="space-y-1.5 text-xs text-stone-600">
				{#if glacier.nearest_active_ice}
					<div class="flex justify-between gap-2">
						<span>Nearest active ice</span>
						<span class="font-mono text-ink text-right">
							{glacier.dist_to_active_ice_km?.toFixed(1)}&nbsp;km
						</span>
					</div>
				{/if}
				{#if glacier.nearest_named_glacier}
					<div class="flex justify-between gap-2">
						<span>Nearest named glacier</span>
						<span class="text-ink text-right truncate">{glacier.nearest_named_glacier}</span>
					</div>
				{/if}
				{#if glacier.has_velocity_data && glacier.glacier_v_mean != null}
					<div class="flex justify-between gap-2">
						<span>Ice velocity here</span>
						<span class="font-mono text-ink">{glacier.glacier_v_mean.toFixed(0)} m/yr</span>
					</div>
					{#if glacier.glacier_v_trend != null}
						<div class="flex justify-between gap-2">
							<span>Velocity trend</span>
							<span class="font-mono {glacier.glacier_v_trend < 0 ? 'text-blue-600' : 'text-red-600'}">
								{glacier.glacier_v_trend > 0 ? '+' : ''}{glacier.glacier_v_trend.toFixed(2)} m/yr·yr
								{glacier.glacier_v_trend < 0 ? ' (slowing)' : glacier.glacier_v_trend > 0 ? ' (accelerating)' : ''}
							</span>
						</div>
					{/if}
				{:else}
					<div class="text-stone-400 italic">No ITS_LIVE velocity at this site — context inferred from nearby ice.</div>
				{/if}
			</div>
		{/if}

		<!-- Nearby slides -->
		{#if nearbySlides.length > 0}
			<h4 class="font-serif font-semibold text-sm text-ink mt-5 mb-2 uppercase tracking-wide">
				Nearby known slides
			</h4>
			<div class="space-y-1.5">
				{#each nearbySlides.slice(0, 5) as slide, i}
					{@const badge = sourceBadge(slide.source)}
					<div class="text-xs text-stone-600 flex justify-between items-center gap-2">
						<span class="flex items-center gap-1.5 min-w-0">
							<span
								class="inline-block flex-shrink-0 px-1.5 py-0.5 rounded-md border border-black text-black text-[9px] font-bold leading-none tracking-wide cursor-help"
								title={badge.title}
							>{badge.label}</span>
							<span class="truncate">{slide.name && slide.name !== 'nan' ? slide.name : nearestFjord(slide.geometry.coordinates[0], slide.geometry.coordinates[1]) + ' area'}</span>
						</span>
						<span class="text-stone-400 flex-shrink-0">{slide.distance_km.toFixed(1)} km</span>
					</div>
				{/each}
			</div>
			<div class="mt-2 flex items-center gap-2 text-[10px] text-stone-500">
				<span
					class="inline-block px-1.5 py-0.5 rounded-md border border-black text-black font-bold leading-none tracking-wide cursor-help"
					title="The organisation that recorded each known landslide"
				>SOURCE</span>
				<span>as data source</span>
			</div>
		{:else}
			<p class="text-xs text-stone-400 mt-4 italic">No nearby slides found (backend query pending)</p>
		{/if}

		<!-- Coordinates -->
		<div class="mt-4 pt-3 border-t border-stone-200 text-xs text-stone-400">
			{site.geometry.coordinates[1].toFixed(4)}°N, {Math.abs(site.geometry.coordinates[0]).toFixed(4)}°W
		</div>
	</div>
</div>
