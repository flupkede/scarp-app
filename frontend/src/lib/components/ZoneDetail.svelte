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
		{ key: 'slope_factor', label: 'Steep slope', value: components.slope_factor },
		{ key: 'exposure', label: 'Exposure', value: components.exposure },
		{ key: 'coverage', label: 'Coverage', value: components.coverage }
	]);

	let rankColor = $derived(
		site.properties.rank <= 10
			? 'text-red-600'
			: site.properties.rank <= 30
				? 'text-orange-500'
				: 'text-amber-500'
	);
</script>

<div class="absolute top-0 right-0 h-full w-80 bg-paper shadow-2xl z-40 flex flex-col overflow-hidden border-l border-stone-200">
	<!-- Header -->
	<div class="px-4 py-4 border-b border-stone-200 flex items-start justify-between bg-paper">
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

		<!-- Nearby slides -->
		{#if nearbySlides.length > 0}
			<h4 class="font-serif font-semibold text-sm text-ink mt-5 mb-2 uppercase tracking-wide">
				Nearby known slides
			</h4>
			<div class="space-y-1.5">
				{#each nearbySlides.slice(0, 5) as slide, i}
					<div class="text-xs text-stone-600 flex justify-between">
						<span>{slide.name && slide.name !== 'nan' ? slide.name : `${slide.source || 'Unknown'} slide`}</span>
						<span class="text-stone-400">{slide.distance_km.toFixed(1)} km</span>
					</div>
				{/each}
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
