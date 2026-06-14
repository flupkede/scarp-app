<script lang="ts">
	import { BASEMAPS } from '$lib/basemaps';

	let {
		currentId = 'esri-topo',
		onSelect,
	}: {
		currentId?: string;
		onSelect: (id: string) => void;
	} = $props();

	let open = $state(false);

	const available = BASEMAPS.filter((b) => b.available);
	let currentLabel = $derived(BASEMAPS.find((b) => b.id === currentId)?.shortName ?? 'Basemap');
</script>

<div class="absolute bottom-8 right-4 z-10 text-xs select-none">
	{#if open}
		<!-- Click-outside backdrop -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<button
			class="fixed inset-0 z-0 cursor-default"
			onclick={() => (open = false)}
			aria-label="Close basemap picker"
		></button>
	{/if}

	<!-- Flyout panel -->
	{#if open}
		<div class="relative z-10 mb-1.5 bg-white rounded-lg shadow-xl border border-stone-200 p-2 w-44">
			<p class="text-[10px] text-stone-400 uppercase tracking-wider mb-1.5 px-0.5">Basemap</p>
			<div class="grid grid-cols-2 gap-1">
				{#each available as bm}
					<button
						onclick={() => {
							onSelect(bm.id);
							open = false;
						}}
						class="px-2 py-1.5 rounded text-left leading-tight transition-colors
							{currentId === bm.id
								? 'bg-amber-500 text-white font-semibold'
								: 'bg-stone-100 hover:bg-stone-200 text-stone-700'}"
						title={bm.name}
					>
						{bm.shortName}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Toggle button -->
	<button
		onclick={() => (open = !open)}
		class="flex items-center gap-1.5 bg-white/90 backdrop-blur-sm rounded-lg shadow border border-stone-200 px-2.5 py-1.5 text-stone-700 hover:bg-white transition-colors"
		title="Switch basemap"
	>
		<!-- Grid icon -->
		<svg
			class="w-3.5 h-3.5 flex-shrink-0"
			viewBox="0 0 16 16"
			fill="none"
			stroke="currentColor"
			stroke-width="1.5"
		>
			<rect x="1" y="1" width="6" height="6" rx="1" />
			<rect x="9" y="1" width="6" height="6" rx="1" />
			<rect x="1" y="9" width="6" height="6" rx="1" />
			<rect x="9" y="9" width="6" height="6" rx="1" />
		</svg>
		<span class="text-[11px]">{currentLabel}</span>
	</button>
</div>
