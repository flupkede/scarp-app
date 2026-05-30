<script lang="ts">
	import maplibregl from 'maplibre-gl';
	import 'maplibre-gl/dist/maplibre-gl.css';
	import { onMount } from 'svelte';

	let { sites, top10, influenceGeojson, slides, stations, confidence, onSelectSite, layerState }: {
		sites: GeoJSON.FeatureCollection;
		top10: GeoJSON.Feature[];
		influenceGeojson: GeoJSON.FeatureCollection;
		slides: GeoJSON.FeatureCollection;
		stations: GeoJSON.FeatureCollection;
		confidence: GeoJSON.FeatureCollection | null;
		onSelectSite: (id: string) => void;
		layerState: {
			showSlides: boolean;
			showStations: boolean;
			showInfluence: boolean;
			showCandidates: boolean;
			showConfidence: boolean;
		};
	} = $props();

	let mapContainer: HTMLDivElement;
	let map: maplibregl.Map | null = null;

	function toggleLayer(layerId: string, visible: boolean) {
		if (!map) return;
		try {
			if (map.getLayer(layerId)) {
				map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
			}
		} catch { /* layer may not exist yet */ }
	}

	$effect(() => { toggleLayer('slides-layer', layerState.showSlides); });
	$effect(() => { toggleLayer('stations-layer', layerState.showStations); });
	$effect(() => {
		toggleLayer('zones-fill', layerState.showInfluence);
		toggleLayer('zones-outline', layerState.showInfluence);
	});
	$effect(() => {
		toggleLayer('candidates-target', layerState.showCandidates);
		toggleLayer('candidates-dot', layerState.showCandidates);
	});
	$effect(() => {
		toggleLayer('confidence-low', layerState.showConfidence);
		toggleLayer('confidence-medium', layerState.showConfidence);
	});

	/** Generate a 32×32 diagonal-hatch ImageData for MapLibre fill-pattern. */
	function makeDiagonalHatch(): ImageData {
		const size = 32;
		const canvas = document.createElement('canvas');
		canvas.width = size;
		canvas.height = size;
		const ctx = canvas.getContext('2d')!;
		ctx.clearRect(0, 0, size, size);
		ctx.strokeStyle = 'rgba(100, 116, 139, 0.55)'; // slate-500 ~55%
		ctx.lineWidth = 1.5;
		// Diagonal lines NE↗ every 8 px, tiling seamlessly
		for (let d = -size; d < size * 2; d += 8) {
			ctx.beginPath();
			ctx.moveTo(d, size);
			ctx.lineTo(d + size, 0);
			ctx.stroke();
		}
		return ctx.getImageData(0, 0, size, size);
	}

	onMount(() => {
		if (!mapContainer) return;

		const m = new maplibregl.Map({
			container: mapContainer,
			style: {
				version: 8,
				sources: {
					'esri-topo': {
						type: 'raster',
						tiles: [
							'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'
						],
						tileSize: 256,
						attribution: 'Tiles &copy; Esri'
					}
				},
				layers: [
					{
						id: 'esri-topo-layer',
						type: 'raster',
						source: 'esri-topo'
						// NO raster-brightness-max or raster-saturation overrides — they dim tiles
					}
				]
			},
			center: [-135, 57],
			zoom: 5
		});

		m.addControl(new maplibregl.NavigationControl(), 'top-right');

		m.on('load', () => {
			// --- Diagonal hatch pattern for confidence layer ---
			m.addImage('diagonal-hatch', makeDiagonalHatch());

			// --- Sources ---

			// Influence areas (polygons) — candidates_influence
			m.addSource('zones', { type: 'geojson', data: influenceGeojson });

			// Candidate sites (points) — zones.geojson
			m.addSource('candidates', { type: 'geojson', data: sites });

			// Top 10 (points) — for labels + pulse
			m.addSource('top10', { type: 'geojson', data: { type: 'FeatureCollection', features: top10 } });

			// Slides
			m.addSource('slides', { type: 'geojson', data: slides });

			// Stations
			m.addSource('stations', { type: 'geojson', data: stations });

			// Confidence layer (optional — null if not generated yet)
			if (confidence) {
				m.addSource('confidence', { type: 'geojson', data: confidence });
			}

			// --- Layers (bottom to top) ---

			// 0. Confidence — medium band (very faint solid grey, below everything)
			if (confidence) {
				m.addLayer({
					id: 'confidence-medium',
					type: 'fill',
					source: 'confidence',
					filter: ['==', ['get', 'band'], 'medium'],
					layout: { visibility: layerState.showConfidence ? 'visible' : 'none' },
					paint: {
						'fill-color': '#94a3b8',
						'fill-opacity': 0.08
					}
				});

				// 0b. Confidence — low band (diagonal hatch, clearly "no data")
				m.addLayer({
					id: 'confidence-low',
					type: 'fill',
					source: 'confidence',
					filter: ['==', ['get', 'band'], 'low'],
					layout: { visibility: layerState.showConfidence ? 'visible' : 'none' },
					paint: {
						'fill-pattern': 'diagonal-hatch',
						'fill-opacity': 0.35
					}
				});
			}

			// 1. Influence area fill — rank gradient red→amber→yellow
			m.addLayer({
				id: 'zones-fill',
				type: 'fill',
				source: 'zones',
				paint: {
					'fill-color': [
						'case',
						['<=', ['get', 'rank'], 10], '#dc2626',
						['<=', ['get', 'rank'], 30], '#ea580c',
						['<=', ['get', 'rank'], 60], '#f59e0b',
						'#fbbf24'
					],
					'fill-opacity': 0.35
				}
			});

			// 2. Influence area outline
			m.addLayer({
				id: 'zones-outline',
				type: 'line',
				source: 'zones',
				paint: {
					'line-color': '#7c2d12',
					'line-width': 1,
					'line-opacity': 0.6
				}
			});

			// 3. Slide markers — small dark dots
			m.addLayer({
				id: 'slides-layer',
				type: 'circle',
				source: 'slides',
				paint: {
					'circle-color': '#1f2937',
					'circle-radius': 3,
					'circle-opacity': 0.4
				}
			});

			// 4. Station markers — blue filled circles
			m.addLayer({
				id: 'stations-layer',
				type: 'circle',
				source: 'stations',
				paint: {
					'circle-color': '#3b82f6',
					'circle-radius': 5,
					'circle-stroke-color': '#ffffff',
					'circle-stroke-width': 1
				}
			});

			// 5. Candidate target symbol — outer ring
			m.addLayer({
				id: 'candidates-target',
				type: 'circle',
				source: 'candidates',
				filter: ['>', ['get', 'rank'], 10],
				paint: {
					'circle-radius': 7,
					'circle-color': '#ffffff',
					'circle-stroke-color': '#1c1917',
					'circle-stroke-width': 1.5
				}
			});

			// 5b. Candidate target — inner dot
			m.addLayer({
				id: 'candidates-dot',
				type: 'circle',
				source: 'candidates',
				filter: ['>', ['get', 'rank'], 10],
				paint: {
					'circle-radius': 2,
					'circle-color': '#1c1917'
				}
			});

			// 6. Top 10 — larger target symbols with pulse ring
			m.addLayer({
				id: 'top10-ring',
				type: 'circle',
				source: 'top10',
				paint: {
					'circle-radius': 10,
					'circle-color': '#ffffff',
					'circle-stroke-color': '#1c1917',
					'circle-stroke-width': 2
				}
			});

			// 6b. Top 10 — middle ring
			m.addLayer({
				id: 'top10-mid',
				type: 'circle',
				source: 'top10',
				paint: {
					'circle-radius': 6,
					'circle-color': '#ffffff',
					'circle-stroke-color': '#1c1917',
					'circle-stroke-width': 1.5
				}
			});

			// 6c. Top 10 — center dot
			m.addLayer({
				id: 'top10-dot',
				type: 'circle',
				source: 'top10',
				paint: {
					'circle-radius': 3,
					'circle-color': '#1c1917'
				}
			});

			// 6d. Top 10 — pulsing outer glow
			m.addLayer({
				id: 'top10-pulse',
				type: 'circle',
				source: 'top10',
				paint: {
					'circle-radius': 14,
					'circle-color': '#dc2626',
					'circle-opacity': 0.3
				}
			});

			// 7. Labels — only top 10
			m.addLayer({
				id: 'zones-label',
				type: 'symbol',
				source: 'top10',
				layout: {
					'text-field': ['concat', '#', ['to-string', ['get', 'rank']]],
					'text-font': ['Inter Regular'],
					'text-size': 12,
					'text-offset': [0, 1.8],
					'text-anchor': 'top',
					'text-allow-overlap': false
				},
				paint: {
					'text-color': '#1c1917',
					'text-halo-color': '#ffffff',
					'text-halo-width': 1.5
				}
			});

			// --- Interactions ---

			const candidateLayers = ['candidates-target', 'candidates-dot', 'top10-ring', 'top10-mid', 'top10-dot'];
			for (const layerId of candidateLayers) {
				m.on('click', layerId, (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
					if (e.features && e.features.length > 0) {
						const id = e.features[0].properties?.id as string;
						if (id) {
							const coords = e.features[0].geometry as GeoJSON.Point;
							onSelectSite(id);
							m.flyTo({ center: coords.coordinates as [number, number], zoom: 9, duration: 1500 });
						}
					}
				});
				m.on('mouseenter', layerId, () => { m.getCanvas().style.cursor = 'pointer'; });
				m.on('mouseleave', layerId, () => { m.getCanvas().style.cursor = ''; });
			}

			// Hover on influence zone → tooltip
			const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10 });

			m.on('mouseenter', 'zones-fill', (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
				if (e.features && e.features.length > 0) {
					m.getCanvas().style.cursor = 'pointer';
					const props = e.features[0].properties;
					const coords = (e.features[0].geometry as GeoJSON.Point).coordinates as [number, number];
					popup.setLngLat(coords).setHTML(`<strong>#${props.rank}</strong> — Score: ${props.score?.toFixed(3)}`).addTo(m);
				}
			});
			m.on('mouseleave', 'zones-fill', () => {
				m.getCanvas().style.cursor = '';
				popup.remove();
			});

			// Click on slide marker → popup
			m.on('click', 'slides-layer', (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
				if (e.features && e.features.length > 0) {
					const props = e.features[0].properties;
					new maplibregl.Popup({ offset: 5 }).setLngLat(e.lngLat)
						.setHTML(`<strong>Slide</strong><br/>Source: ${props.source}`).addTo(m);
				}
			});

			// Click on station → popup
			m.on('click', 'stations-layer', (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
				if (e.features && e.features.length > 0) {
					const props = e.features[0].properties;
					new maplibregl.Popup({ offset: 5 }).setLngLat(e.lngLat)
						.setHTML(`<strong>${props.site_name}</strong><br/>Code: ${props.station_code} (${props.network})`).addTo(m);
				}
			});

			// Pulse animation for top 10
			let startTime = Date.now();
			function animatePulse() {
				if (!m || (m as any)._removed) return;
				const elapsed = (Date.now() - startTime) / 1000;
				const radius = 14 + 6 * Math.abs(Math.sin(elapsed));
				const opacity = 0.3 - 0.15 * Math.abs(Math.sin(elapsed));
				m.setPaintProperty('top10-pulse', 'circle-radius', radius);
				m.setPaintProperty('top10-pulse', 'circle-opacity', opacity);
				requestAnimationFrame(animatePulse);
			}
			animatePulse();
		});

		map = m;

		return () => { m.remove(); };
	});
</script>

<div class="relative w-full h-full">
	<div bind:this={mapContainer} class="absolute inset-0"></div>

	<!-- Legend -->
	<div class="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 text-xs pointer-events-none max-w-[200px]">
		<h4 class="font-serif font-semibold text-sm mb-2 text-ink">SENSOR PLACEMENT</h4>
		<div class="flex items-center gap-2 mb-1">
			<span class="inline-block w-4 h-4 rounded-full border-2 border-ink bg-white flex-shrink-0 relative">
				<span class="absolute inset-1 bg-ink rounded-full"></span>
			</span>
			<span>Recommended site</span>
		</div>
		<div class="flex items-center gap-2 mb-3">
			<span class="inline-block w-3 h-3 rounded-full bg-blue-500 border border-white flex-shrink-0"></span>
			<span>Existing monitoring</span>
		</div>

		<h4 class="font-serif font-semibold text-sm mb-2 text-ink">RISK (unmonitored)</h4>
		<div class="flex items-center gap-2 mb-1">
			<span class="inline-block w-4 h-3 rounded-sm flex-shrink-0" style="background: linear-gradient(to right, #dc2626, #f59e0b)"></span>
			<span>High → Lower priority</span>
		</div>

		{#if layerState.showConfidence}
			<div class="flex items-center gap-2 mt-2">
				<svg width="14" height="10" viewBox="0 0 14 10" class="flex-shrink-0">
					<rect width="14" height="10" fill="#94a3b8" opacity="0.15"/>
					<line x1="0" y1="10" x2="10" y2="0" stroke="#64748b" stroke-width="1.2" opacity="0.55"/>
					<line x1="4" y1="10" x2="14" y2="0" stroke="#64748b" stroke-width="1.2" opacity="0.55"/>
				</svg>
				<span>Data-limited area</span>
			</div>
		{/if}
	</div>
</div>
