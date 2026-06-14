<script lang="ts">
	import maplibregl from 'maplibre-gl';
	import { onMount } from 'svelte';
	import { BASEMAPS, DEFAULT_BASEMAP_ID } from '$lib/basemaps';

	let {
		leftId = DEFAULT_BASEMAP_ID,
		rightId = 'usgs-historical-topo',
		center = [-135, 57] as [number, number],
		zoom = 7,
		onClose,
	}: {
		/** Basemap id shown on the left (current). */
		leftId?: string;
		/** Basemap id shown on the right (historical / comparison). */
		rightId?: string;
		center?: [number, number];
		zoom?: number;
		onClose: () => void;
	} = $props();

	let containerEl: HTMLDivElement;
	let leftEl: HTMLDivElement;
	let rightEl: HTMLDivElement;
	let leftMap: maplibregl.Map | null = null;
	let rightMap: maplibregl.Map | null = null;

	let sliderPct = $state(50);
	let dragging = false;
	let syncing = false; // guard against camera-sync loop

	function basemapStyle(id: string): maplibregl.StyleSpecification {
		const bm = BASEMAPS.find((b) => b.id === id) ?? BASEMAPS[0];
		return {
			version: 8,
			sources: {
				basemap: {
					type: 'raster',
					tiles: bm.tiles,
					tileSize: bm.tileSize,
					attribution: bm.attribution,
				},
			},
			layers: [{ id: 'basemap-layer', type: 'raster', source: 'basemap' }],
		};
	}

	function syncCamera(src: maplibregl.Map, tgt: maplibregl.Map) {
		if (syncing) return;
		syncing = true;
		tgt.jumpTo({
			center: src.getCenter(),
			zoom: src.getZoom(),
			bearing: src.getBearing(),
			pitch: src.getPitch(),
		});
		// reset guard after current event loop
		setTimeout(() => {
			syncing = false;
		}, 0);
	}

	let leftLabel = $derived(BASEMAPS.find((b) => b.id === leftId)?.shortName ?? 'Current');
	let rightLabel = $derived(BASEMAPS.find((b) => b.id === rightId)?.shortName ?? 'Historical');

	onMount(() => {
		leftMap = new maplibregl.Map({
			container: leftEl,
			style: basemapStyle(leftId),
			center,
			zoom,
			attributionControl: false,
		});
		rightMap = new maplibregl.Map({
			container: rightEl,
			style: basemapStyle(rightId),
			center,
			zoom,
			attributionControl: false,
		});

		leftMap.on('move', () => {
			if (rightMap) syncCamera(leftMap!, rightMap);
		});
		rightMap.on('move', () => {
			if (leftMap) syncCamera(rightMap!, leftMap);
		});

		function onMouseMove(e: MouseEvent) {
			if (!dragging || !containerEl) return;
			const rect = containerEl.getBoundingClientRect();
			sliderPct = Math.max(5, Math.min(95, ((e.clientX - rect.left) / rect.width) * 100));
		}
		function onTouchMove(e: TouchEvent) {
			if (!dragging || !containerEl) return;
			const rect = containerEl.getBoundingClientRect();
			sliderPct = Math.max(
				5,
				Math.min(95, ((e.touches[0].clientX - rect.left) / rect.width) * 100)
			);
		}
		function stopDrag() {
			dragging = false;
		}

		window.addEventListener('mousemove', onMouseMove);
		window.addEventListener('mouseup', stopDrag);
		window.addEventListener('touchmove', onTouchMove, { passive: true });
		window.addEventListener('touchend', stopDrag);

		return () => {
			window.removeEventListener('mousemove', onMouseMove);
			window.removeEventListener('mouseup', stopDrag);
			window.removeEventListener('touchmove', onTouchMove);
			window.removeEventListener('touchend', stopDrag);
			leftMap?.remove();
			rightMap?.remove();
		};
	});
</script>

<!-- Full overlay — sits on top of the main map -->
<div bind:this={containerEl} class="absolute inset-0 z-30 overflow-hidden">
	<!-- Left map (full size, underneath) -->
	<div bind:this={leftEl} class="absolute inset-0"></div>

	<!-- Right map (clipped to right side of the divider) -->
	<div
		bind:this={rightEl}
		class="absolute inset-0"
		style="clip-path: inset(0 0 0 {sliderPct}%)"
	></div>

	<!-- Divider handle -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="absolute top-0 bottom-0 w-1 bg-white/90 shadow-lg cursor-ew-resize z-10 select-none"
		style="left: calc({sliderPct}% - 2px)"
		onmousedown={(e) => {
			dragging = true;
			e.preventDefault();
		}}
		ontouchstart={(e) => {
			dragging = true;
			e.preventDefault();
		}}
	>
		<!-- Handle pill -->
		<div
			class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-7 h-7 bg-white rounded-full shadow-lg flex items-center justify-center text-stone-500 text-sm font-bold pointer-events-none"
		>
			↔
		</div>
	</div>

	<!-- Left label -->
	<div
		class="absolute top-3 left-3 bg-black/60 text-white text-xs px-2 py-1 rounded-md backdrop-blur-sm pointer-events-none select-none"
	>
		{leftLabel}
	</div>

	<!-- Right label (tracks the handle) -->
	<div
		class="absolute top-3 bg-black/60 text-white text-xs px-2 py-1 rounded-md backdrop-blur-sm pointer-events-none select-none"
		style="left: calc({sliderPct}% + 10px)"
	>
		{rightLabel}
	</div>

	<!-- Close button -->
	<button
		onclick={onClose}
		class="absolute top-3 right-3 bg-black/60 hover:bg-black/80 text-white text-xs px-3 py-1.5 rounded-md backdrop-blur-sm transition-colors z-20"
	>
		&#x2715; Close comparison
	</button>
</div>
