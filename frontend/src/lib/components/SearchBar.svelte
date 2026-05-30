<script lang="ts">
	let { onSearch, loading, explanation, resultCount, onClear }: {
		onSearch: (query: string) => void;
		loading: boolean;
		explanation: string | null;
		resultCount: number | null;
		onClear: () => void;
	} = $props();

	let query = $state('');

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
				placeholder="e.g. near cruise ship routes"
				disabled={loading}
				class="w-full rounded-lg bg-transparent px-3 py-2 text-sm text-ink placeholder:text-stone-400 focus:outline-none"
			/>
			<button
				type="submit"
				disabled={loading || !query.trim()}
				class="absolute right-1 top-1 bottom-1 px-3 rounded-md bg-amber-500 text-white text-xs font-semibold hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed"
			>
				{loading ? '...' : 'Search'}
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
