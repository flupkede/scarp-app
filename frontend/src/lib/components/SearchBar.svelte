<script lang="ts">
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';

	let { onSearch, loading, explanation, resultCount, onClear }: {
		onSearch: (query: string) => void;
		loading: boolean;
		explanation: string | null;
		resultCount: number | null;
		onClear: () => void;
	} = $props();

	let query = $state('');
	let focused = $state(false);

	// Rotating placeholder examples — show what the LLM search can do
	const EXAMPLES = [
		'near cruise ship routes',
		'top 10 unmonitored high-risk sites',
		'steep fjord walls with no coverage',
		'highest exposure near Whittier',
		'within 30 km of Barry Arm',
		'most susceptible slopes, top 5'
	];

	let exampleIndex = $state(0);
	const reducedMotion =
		typeof window !== 'undefined' &&
		window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	// Show the rotating overlay only while the field is empty, idle, and unfocused.
	let showRotating = $derived(!query && !focused && !loading && !reducedMotion);

	// Static fallback placeholder (reduced-motion / focused / loading states).
	const staticPlaceholder = `e.g. ${EXAMPLES[0]}`;

	onMount(() => {
		const interval = setInterval(() => {
			if (showRotating) {
				exampleIndex = (exampleIndex + 1) % EXAMPLES.length;
			}
		}, 3000);
		return () => clearInterval(interval);
	});

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (query.trim()) {
			onSearch(query.trim());
		}
	}
</script>

<div class="px-4 py-3 border-b border-stone-200">
	<form onsubmit={handleSubmit}>
		<div class="relative rounded-lg border border-stone-300 bg-white focus-within:ring-2 focus-within:ring-amber-400 focus-within:border-transparent">
			<input
				type="text"
				bind:value={query}
				onfocus={() => (focused = true)}
				onblur={() => (focused = false)}
				placeholder={showRotating ? '' : staticPlaceholder}
				disabled={loading}
				class="w-full rounded-lg bg-transparent px-3 py-2 text-sm text-ink placeholder:text-stone-400 focus:outline-none"
			/>

			<!-- Rotating example overlay — only when input is empty & idle -->
			{#if showRotating}
				{#key exampleIndex}
					<span
						class="ph-overlay"
						aria-hidden="true"
						in:fade={{ duration: 400 }}
						out:fade={{ duration: 400 }}
					>e.g. {EXAMPLES[exampleIndex]}</span>
				{/key}
			{/if}
			<button
				type="submit"
				disabled={loading || !query.trim()}
				class="absolute right-1 top-1 bottom-1 px-2.5 rounded-md bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center"
				aria-label="Search"
			>
				{#if loading}
					<svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
						<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
					</svg>
				{:else}
					<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="11" cy="11" r="7"/>
						<line x1="16.5" y1="16.5" x2="22" y2="22"/>
					</svg>
				{/if}
			</button>
		</div>
	</form>

	{#if explanation}
		<div class="mt-2 text-xs text-stone-600 italic">
			{explanation}
		</div>
		{#if resultCount !== null}
			<div class="mt-1 flex items-center justify-between">
				<span class="text-xs text-stone-500">Showing {resultCount} sites</span>
				<button
					onclick={onClear}
					class="text-xs text-amber-600 hover:text-amber-700 font-medium"
				>
					Clear filter
				</button>
			</div>
		{/if}
	{/if}
</div>

<style>
	/* Rotating example overlay — sits exactly over the input's text area,
	   mimics the native placeholder colour, and never blocks clicks/typing. */
	.ph-overlay {
		position: absolute;
		left: 0.75rem; /* matches input px-3 */
		top: 50%;
		transform: translateY(-50%);
		font-size: 0.875rem; /* text-sm */
		line-height: 1.25rem;
		color: #a8a29e; /* stone-400 */
		pointer-events: none;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: calc(100% - 3rem); /* leave room for the search button */
	}
</style>
