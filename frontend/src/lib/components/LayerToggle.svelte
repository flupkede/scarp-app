<script lang="ts">
	let { layerState, hasConfidence = false, hasGlacier = false, hasHig = false }: {
		layerState: {
			showSlides: boolean;
			showStations: boolean;
			showInfluence: boolean;
			showCandidates: boolean;
			showConfidence: boolean;
			showGlacier: boolean;
			showHigInventory: boolean;
			showSurveyCircles: boolean;
		} | null;
		/** Whether confidence.geojson has been generated yet. If false, toggle is hidden. */
		hasConfidence?: boolean;
		/** Whether glacier_velocity.geojson has been generated yet. If false, toggle is hidden. */
		hasGlacier?: boolean;
		/** Whether the Hig inventory layers have been generated yet. If false, toggles hidden. */
		hasHig?: boolean;
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
			<span class="inline-block w-3 h-3 rounded-full bg-amber-700 opacity-50"></span>
			Known slides (public, 39k)
		</label>

		{#if hasHig}
			<label class="flex items-center gap-2 text-xs text-ink cursor-pointer">
				<input
					type="checkbox"
					checked={layerState?.showHigInventory ?? false}
					onchange={() => toggle('showHigInventory')}
					class="rounded border-stone-300 text-amber-500 focus:ring-amber-400"
				/>
				<span class="inline-block w-3 h-3 rounded-full" style="background: #7f1d1d"></span>
				Hig inventory (1.5k)
			</label>
			<label class="flex items-center gap-2 text-xs text-ink cursor-pointer">
				<input
					type="checkbox"
					checked={layerState?.showSurveyCircles ?? false}
					onchange={() => toggle('showSurveyCircles')}
					class="rounded border-stone-300 text-amber-500 focus:ring-amber-400"
				/>
				<span class="inline-block w-3 h-3 rounded-full border-2 bg-transparent" style="border-color: #475569"></span>
				Survey circles
			</label>
		{/if}

		{#if hasGlacier}
			<label class="flex items-center gap-2 text-xs text-ink cursor-pointer">
				<input
					type="checkbox"
					checked={layerState?.showGlacier ?? false}
					onchange={() => toggle('showGlacier')}
					class="rounded border-stone-300 text-amber-500 focus:ring-amber-400"
				/>
				<span class="inline-block w-3 h-3 rounded-full" style="background: #0ea5e9"></span>
				Glacier velocity
			</label>
		{/if}

		{#if hasConfidence}
			<label class="flex items-center gap-2 text-xs text-ink cursor-pointer">
				<input
					type="checkbox"
					checked={layerState?.showConfidence ?? false}
					onchange={() => toggle('showConfidence')}
					class="rounded border-stone-300 text-amber-500 focus:ring-amber-400"
				/>
				<!-- Diagonal hatch swatch -->
				<svg width="12" height="12" viewBox="0 0 12 12" class="flex-shrink-0">
					<rect width="12" height="12" fill="#9ca3af" opacity="0.2"/>
					<line x1="0" y1="12" x2="12" y2="0" stroke="#6b7280" stroke-width="1.5" opacity="0.5"/>
					<line x1="-6" y1="12" x2="6" y2="0" stroke="#6b7280" stroke-width="1.5" opacity="0.5"/>
					<line x1="6" y1="12" x2="18" y2="0" stroke="#6b7280" stroke-width="1.5" opacity="0.5"/>
				</svg>
				Data confidence
			</label>
		{/if}
	</div>

	{#if hasConfidence && layerState?.showConfidence}
		<p class="mt-2 text-[10px] text-stone-400 leading-snug">
			▨ grey hatch = monitoring/data gap (we're blind here)
		</p>
	{/if}
</div>
