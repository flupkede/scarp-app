<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		goto('/story', { replaceState: true });
	});
</script>

<svelte:head>
	<title>About — SCARP</title>
	<meta http-equiv="refresh" content="0; url=/story" />
</svelte:head>

<noscript>
	<meta http-equiv="refresh" content="0; url=/story" />
	<p>Redirecting to <a href="/story">/story</a>…</p>
</noscript>
