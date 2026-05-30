<script lang="ts">
	let { layerState }: {
		layerState: {
			showSlides: boolean;
			showStations: boolean;
			showInfluence: boolean;
			showCandidates: boolean;
		} | null;
	} = $props();

	function toggle(key: string) {
		if (!layerState) return;
		const k = key as keyof typeof layerState;
		(layerState as any)[k] = !(layerState as any)[k];
	}
</script>

<div class="px-4 py-3 border-t border-stone-200">
	<h4 class="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Layers</h4>
	<div class="space-y-1.5">
		<label class="flex items-center gap-2 text-xs text-ink cursor-pointer">
			<input
				type="checkbox"
				checked={layerState?.showInfluence ?? true}
				onchange={() => toggle('showInfluence')}
				class="rounded border-stone-300 text-amber-500 focus:ring-amber-400"
			/>
			<span class="inline-block w-3 h-2 rounded-sm" style="background: #ea580c"></span>
			Risk zones
		</label>
		<label class="flex items-center gap-2 text-xs text-ink cursor-pointer">
			<input
				type="checkbox"
				checked={layerState?.showCandidates ?? true}
				onchange={() => toggle('showCandidates')}
				class="rounded border-stone-300 text-amber-500 focus:ring-amber-400"
			/>
			<span class="inline-block w-3 h-3 rounded-full border border-ink bg-white relative">
				<span class="absolute inset-0.5 bg-ink rounded-full"></span>
			</span>
			Candidates
		</label>
		<label class="flex items-center gap-2 text-xs text-ink cursor-pointer">
			<input
				type="checkbox"
				checked={layerState?.showStations ?? true}
				onchange={() => toggle('showStations')}
				class="rounded border-stone-300 text-amber-500 focus:ring-amber-400"
			/>
			<span class="inline-block w-3 h-3 rounded-full bg-blue-500"></span>
			Stations
		</label>
		<label class="flex items-center gap-2 text-xs text-ink cursor-pointer">
			<input
				type="checkbox"
				checked={layerState?.showSlides ?? true}
				onchange={() => toggle('showSlides')}
				class="rounded border-stone-300 text-amber-500 focus:ring-amber-400"
			/>
			<span class="inline-block w-3 h-3 rounded-full bg-stone-800 opacity-40"></span>
			Known slides
		</label>
	</div>
</div>
