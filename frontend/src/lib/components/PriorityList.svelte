<script lang="ts">
	import type { ZoneFeature } from '$lib/api';

	let { sites, onSelect }: {
		sites: ZoneFeature[];
		onSelect: (id: string) => void;
	} = $props();

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

	function regionFor(lon: number, lat: number): string {
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

<div class="flex flex-col h-full overflow-hidden">
	<div class="px-4 py-3 border-b border-stone-200">
		<h2 class="font-serif font-semibold text-lg text-ink">120 priority sites</h2>
		<p class="text-xs text-stone-500 mt-0.5">Ranked by landslide + tsunami risk</p>
	</div>

	<div class="flex-1 overflow-y-auto">
		{#each sites as site (site.properties.id)}
			{@const coords = site.geometry.coordinates}
			{@const region = regionFor(coords[0], coords[1])}
			<button
				class="w-full text-left px-4 py-3 border-b border-stone-100 hover:bg-amber-50 transition-colors group"
				onclick={() => onSelect(site.properties.id)}
			>
				<div class="flex items-center gap-2">
					<span class="text-xs font-mono text-amber-700 font-bold w-8">
						#{site.properties.rank}
					</span>
					<span class="text-sm font-semibold text-ink">
						Score {site.properties.score.toFixed(3)}
					</span>
				</div>
				<div class="mt-0.5 text-xs text-stone-500 pl-10">
					{region}
				</div>
				<div class="mt-0.5 text-[10px] text-stone-400 pl-10 group-hover:text-amber-600">
					→ fly to site
				</div>
			</button>
		{/each}
	</div>
</div>
