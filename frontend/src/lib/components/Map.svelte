<script lang="ts">
	import maplibregl from 'maplibre-gl';
	import 'maplibre-gl/dist/maplibre-gl.css';
	import { onMount } from 'svelte';
	import { BASEMAPS, DEFAULT_BASEMAP_ID } from '$lib/basemaps';

	let { sites, top10, influenceGeojson, slides, stations, confidence, glacierVelocity, higLandslides, higPolygons, higSurveyCircles, onSelectSite, onCameraChange, layerState, basemapId = DEFAULT_BASEMAP_ID }: {
		sites: GeoJSON.FeatureCollection;
		top10: GeoJSON.Feature[];
		influenceGeojson: GeoJSON.FeatureCollection;
		slides: GeoJSON.FeatureCollection;
		stations: GeoJSON.FeatureCollection;
		confidence: GeoJSON.FeatureCollection | null;
		glacierVelocity: GeoJSON.FeatureCollection | null;
		higLandslides: GeoJSON.FeatureCollection | null;
		higPolygons: GeoJSON.FeatureCollection | null;
		higSurveyCircles: GeoJSON.FeatureCollection | null;
		onSelectSite: (id: string) => void;
		/** Optional: fires after each camera move with current center/zoom. */
		onCameraChange?: (center: [number, number], zoom: number) => void;
		layerState: {
			showSlides: boolean;
			showStations: boolean;
			showInfluence: boolean;
			showCandidates: boolean;
			showConfidence: boolean;
			showGlacier: boolean;
			showHigInventory: boolean;
			showSurveyCircles: boolean;
			zonesOpacity: number;
			glacierOpacity: number;
		};
		basemapId?: string;
	} = $props();

	let mapContainer: HTMLDivElement;
	let map: maplibregl.Map | null = null;
	let mapLoaded = $state(false);

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
	$effect(() => { toggleLayer('glacier-velocity-layer', layerState.showGlacier); });
	$effect(() => {
		toggleLayer('hig-polygons-fill', layerState.showHigInventory);
		toggleLayer('hig-landslides-layer', layerState.showHigInventory);
	});
	$effect(() => {
		toggleLayer('survey-circles-fill', layerState.showSurveyCircles);
		toggleLayer('survey-circles-outline', layerState.showSurveyCircles);
	});

	// --- Basemap switching ---
	$effect(() => {
		if (!mapLoaded || !map) return;
		const bm = BASEMAPS.find((b) => b.id === basemapId);
		if (!bm) return;
		(map.getSource('basemap') as any).setTiles(bm.tiles);
	});

	// --- Layer opacity (only when the layer is visible — avoids unnecessary style recalc) ---
	$effect(() => {
		if (!mapLoaded || !map || !layerState.showInfluence) return;
		if (map.getLayer('zones-fill')) {
			map.setPaintProperty('zones-fill', 'fill-opacity', layerState.zonesOpacity);
		}
	});
	$effect(() => {
		if (!mapLoaded || !map || !layerState.showGlacier) return;
		if (map.getLayer('glacier-velocity-layer')) {
			map.setPaintProperty('glacier-velocity-layer', 'circle-opacity', layerState.glacierOpacity);
		}
	});

	/** Generate a 32×32 diagonal-hatch ImageData for MapLibre fill-pattern. */
	function makeDiagonalHatch(): ImageData {
		const size = 32;
		const canvas = document.createElement('canvas');
		canvas.width = size;
		canvas.height = size;
		const ctx = canvas.getContext('2d')!;
		ctx.clearRect(0, 0, size, size);
		ctx.strokeStyle = 'rgba(51, 65, 85, 0.9)'; // slate-700 ~90% — heavier/darker
		ctx.lineWidth = 2.5;
		// Diagonal lines NE↗ every 6 px, tiling seamlessly
		for (let d = -size; d < size * 2; d += 6) {
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
					basemap: (() => {
						const initialBm = BASEMAPS.find((b) => b.id === basemapId) ?? BASEMAPS[0];
						return {
							type: 'raster' as const,
							tiles: initialBm.tiles,
							tileSize: initialBm.tileSize,
							attribution: initialBm.attribution
						};
					})()
				},
				layers: [
					{
						id: 'basemap-layer',
						type: 'raster',
						source: 'basemap'
					}
				]
			},
			center: [-135, 57],
			zoom: 5
		});

		m.addControl(new maplibregl.NavigationControl(), 'top-right');

		// Notify parent of camera position after each pan/zoom (for Compare overlay)
		m.on('moveend', () => {
			if (onCameraChange) {
				const c = m.getCenter();
				onCameraChange([c.lng, c.lat], m.getZoom());
			}
		});

		// Surface any MapLibre error to the console (blank-map diagnostics)
		m.on('error', (e: { error?: Error }) => {
			console.error('[MapLibre error]', e?.error?.message ?? e);
		});

		// Ensure the map sizes correctly once the flex layout has settled
		m.on('load', () => {
			requestAnimationFrame(() => m.resize());
		});

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

			// Glacier velocity points (optional — null if glacier pipeline hasn't run)
			if (glacierVelocity) {
				m.addSource('glacier-velocity', { type: 'geojson', data: glacierVelocity });
			}

			// Hig inventory layers (optional — null if inventory pipeline hasn't run)
			if (higPolygons) {
				m.addSource('hig-polygons', { type: 'geojson', data: higPolygons });
			}
			if (higLandslides) {
				m.addSource('hig-landslides', { type: 'geojson', data: higLandslides });
			}
			if (higSurveyCircles) {
				m.addSource('survey-circles', { type: 'geojson', data: higSurveyCircles });
			}

			// --- Layers (bottom to top) ---

			// 0. Confidence — medium band (light hatch: "data thinner here")
			if (confidence) {
				m.addLayer({
					id: 'confidence-medium',
					type: 'fill',
					source: 'confidence',
					filter: ['==', ['get', 'band'], 'medium'],
					layout: { visibility: layerState.showConfidence ? 'visible' : 'none' },
					paint: {
						'fill-pattern': 'diagonal-hatch',
						'fill-opacity': 0.4
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
						'fill-opacity': 0.7
					}
				});
			}

			// 0c. Glacier velocity points (ITS_LIVE) — ice-blue, sized + shaded by speed
			if (glacierVelocity) {
				m.addLayer({
					id: 'glacier-velocity-layer',
					type: 'circle',
					source: 'glacier-velocity',
					layout: { visibility: layerState.showGlacier ? 'visible' : 'none' },
					paint: {
						'circle-radius': [
							'interpolate', ['linear'], ['get', 'v_mean'],
							0, 4, 50, 8, 200, 14
						],
						'circle-color': [
							'interpolate', ['linear'], ['get', 'v_mean'],
							0, '#bae6fd', 50, '#0ea5e9', 200, '#0c4a6e'
						],
						'circle-opacity': 0.75,
						'circle-stroke-color': '#ffffff',
						'circle-stroke-width': 0.5
					}
				});
			}

			// 0d. Survey circles (where Hig ground-truthed) — slate outline, faint fill
			if (higSurveyCircles) {
				m.addLayer({
					id: 'survey-circles-fill',
					type: 'fill',
					source: 'survey-circles',
					layout: { visibility: layerState.showSurveyCircles ? 'visible' : 'none' },
					paint: { 'fill-color': '#475569', 'fill-opacity': 0.06 }
				});
				m.addLayer({
					id: 'survey-circles-outline',
					type: 'line',
					source: 'survey-circles',
					layout: { visibility: layerState.showSurveyCircles ? 'visible' : 'none' },
					paint: { 'line-color': '#475569', 'line-width': 1, 'line-opacity': 0.5 }
				});
			}

			// 0e. Hig inventory — mapped slide footprints (faint maroon fill)
			if (higPolygons) {
				m.addLayer({
					id: 'hig-polygons-fill',
					type: 'fill',
					source: 'hig-polygons',
					layout: { visibility: layerState.showHigInventory ? 'visible' : 'none' },
					paint: { 'fill-color': '#7f1d1d', 'fill-opacity': 0.25 }
				});
			}

			// 0f. Hig inventory — curated landslide centroids (maroon dots)
			if (higLandslides) {
				m.addLayer({
					id: 'hig-landslides-layer',
					type: 'circle',
					source: 'hig-landslides',
					layout: { visibility: layerState.showHigInventory ? 'visible' : 'none' },
					paint: {
						'circle-radius': 3,
						'circle-color': '#7f1d1d',
						'circle-opacity': 0.7,
						'circle-stroke-color': '#ffffff',
						'circle-stroke-width': 0.5
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

			// 3. Slide markers — historical context only: tiny faint amber dots, hidden by default
			m.addLayer({
				id: 'slides-layer',
				type: 'circle',
				source: 'slides',
				layout: { visibility: layerState.showSlides ? 'visible' : 'none' },
				paint: {
					'circle-color': '#b45309',
					'circle-radius': 1.5,
					'circle-opacity': 0.25
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

			// 5. Candidate target symbol — white/black outer ring (recommended site)
			m.addLayer({
				id: 'candidates-target',
				type: 'circle',
				source: 'candidates',
				filter: ['>', ['get', 'rank'], 10],
				paint: {
					'circle-radius': 5,
					'circle-color': '#ffffff',
					'circle-stroke-color': '#1c1917',
					'circle-stroke-width': 1.5
				}
			});

			// 5b. Candidate target — black inner dot
			m.addLayer({
				id: 'candidates-dot',
				type: 'circle',
				source: 'candidates',
				filter: ['>', ['get', 'rank'], 10],
				paint: {
					'circle-radius': 1.5,
					'circle-color': '#1c1917'
				}
			});

			// 6. Top 10 — simple red dot
			m.addLayer({
				id: 'top10-dot',
				type: 'circle',
				source: 'top10',
				paint: {
					'circle-radius': 5,
					'circle-color': '#dc2626',
					'circle-stroke-color': '#ffffff',
					'circle-stroke-width': 1.5
				}
			});

			// 6b. Top 10 — pulsing outer glow
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

			const candidateLayers = ['candidates-target', 'candidates-dot', 'top10-dot'];
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

			// Click on glacier velocity point → popup (speed + trend)
			m.on('click', 'glacier-velocity-layer', (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
				if (e.features && e.features.length > 0) {
					const props = e.features[0].properties;
					const vMean = Number(props.v_mean);
					const trend = Number(props.v_trend_m_yr_per_year);
					const speedStr = Number.isFinite(vMean) ? `${vMean.toFixed(0)} m/yr` : 'n/a';
					const trendStr = Number.isFinite(trend)
						? `${trend > 0 ? '+' : ''}${trend.toFixed(2)} m/yr·yr ` +
							`(${trend < 0 ? 'slowing' : trend > 0 ? 'accelerating' : 'steady'})`
						: 'n/a';
					new maplibregl.Popup({ offset: 5 }).setLngLat(e.lngLat)
						.setHTML(
							`<strong>${props.point_id}</strong><br/>` +
							`Mean speed: ${speedStr}<br/>` +
							`Trend: ${trendStr}`
						).addTo(m);
				}
			});
			m.on('mouseenter', 'glacier-velocity-layer', () => { m.getCanvas().style.cursor = 'pointer'; });
			m.on('mouseleave', 'glacier-velocity-layer', () => { m.getCanvas().style.cursor = ''; });

			// Click on a Hig inventory landslide → popup (type, class, volume, year)
			m.on('click', 'hig-landslides-layer', (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
				if (e.features && e.features.length > 0) {
					const p = e.features[0].properties;
					const vol = Number(p.volume_preferred);
					const volStr = Number.isFinite(vol) && vol > 0
						? `${(vol / 1e6).toFixed(1)} M m³`
						: 'n/a';
					new maplibregl.Popup({ offset: 5 }).setLngLat(e.lngLat)
						.setHTML(
							`<strong>${p.unique_name ?? 'Landslide'}</strong><br/>` +
							`Type: ${p.landslide_type ?? 'n/a'}${p.landslide_class ? ' / ' + p.landslide_class : ''}<br/>` +
							`Volume: ${volStr}${p.year_text ? '<br/>Year: ' + p.year_text : ''}`
						).addTo(m);
				}
			});
			m.on('mouseenter', 'hig-landslides-layer', () => { m.getCanvas().style.cursor = 'pointer'; });
			m.on('mouseleave', 'hig-landslides-layer', () => { m.getCanvas().style.cursor = ''; });

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
			mapLoaded = true;
		});

		map = m;

		return () => { m.remove(); };
	});
</script>

<div class="relative w-full h-full">
	<div bind:this={mapContainer} class="h-full w-full"></div>

	<!-- Legend -->
	<div class="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 text-xs pointer-events-none max-w-[200px]">
		<h4 class="font-serif font-semibold text-sm mb-2 text-ink">SENSOR PLACEMENT</h4>
		<div class="flex items-center gap-2 mb-1">
			<span class="inline-block w-3 h-3 rounded-full bg-red-600 flex-shrink-0"></span>
			<span>Top 10 urgent</span>
		</div>
		<div class="flex items-center gap-2 mb-1">
			<span class="inline-block w-3 h-3 rounded-full border-2 border-ink bg-white flex-shrink-0"></span>
			<span>Recommended site</span>
		</div>
		<div class="flex items-center gap-2 mb-3">
			<span class="inline-block w-3 h-3 rounded-full bg-blue-500 flex-shrink-0"></span>
			<span>Existing monitoring</span>
		</div>

		<h4 class="font-serif font-semibold text-sm mb-2 text-ink">RISK (unmonitored)</h4>
		<div class="flex items-center gap-2 mb-1">
			<span class="inline-block w-3 h-3 rounded-sm flex-shrink-0" style="background: #dc2626"></span>
			<span>Super urgent (top 10)</span>
		</div>
		<div class="flex items-center gap-2 mb-1">
			<span class="inline-block w-3 h-3 rounded-sm flex-shrink-0" style="background: #ea580c"></span>
			<span>Urgent (11–30)</span>
		</div>
		<div class="flex items-center gap-2 mb-1">
			<span class="inline-block w-3 h-3 rounded-sm flex-shrink-0" style="background: #f59e0b"></span>
			<span>Elevated (31–60)</span>
		</div>
		<div class="flex items-center gap-2 mb-1">
			<span class="inline-block w-3 h-3 rounded-sm flex-shrink-0" style="background: #fbbf24"></span>
			<span>Moderate (61+)</span>
		</div>

		{#if layerState.showConfidence}
			<div class="flex items-center gap-2 mt-2">
				<svg width="14" height="10" viewBox="0 0 14 10" class="flex-shrink-0">
					<line x1="-2" y1="10" x2="8" y2="0" stroke="#334155" stroke-width="2" opacity="0.9"/>
					<line x1="2" y1="10" x2="12" y2="0" stroke="#334155" stroke-width="2" opacity="0.9"/>
					<line x1="6" y1="10" x2="16" y2="0" stroke="#334155" stroke-width="2" opacity="0.9"/>
				</svg>
				<span>Data-limited area</span>
			</div>
		{/if}
	</div>
</div>
