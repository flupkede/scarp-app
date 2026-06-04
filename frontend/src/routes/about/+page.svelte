<script lang="ts">
	import { page } from '$app/state';
</script>

<svelte:head>
	<title>About — SCARP</title>
	<meta name="description" content="Credits, data sources, and scientific methodology behind SCARP." />
</svelte:head>

<div class="min-h-screen bg-[#0f172a] text-stone-200">
	<!-- Header -->
	<header class="border-b border-white/10 px-6 py-4 flex items-center gap-4">
		<a href="/" class="text-white/60 hover:text-white text-sm transition-colors">&larr; Map</a>
		<h1 class="text-lg font-bold tracking-wide text-white">About SCARP</h1>
	</header>

	<div class="max-w-3xl mx-auto px-6 py-10 space-y-12">

		<!-- Summary -->
		<section>
			<h2 class="text-xl font-semibold text-amber-400 mb-3">What is SCARP?</h2>
			<p class="leading-relaxed text-stone-300">
				SCARP (Susceptibility-Coverage Analysis for Risk Prioritization) is a decision-support tool
				that helps geologists and communities decide <strong class="text-white">where to place the next
				landslide monitoring sensor</strong> in coastal Alaska. It combines published susceptibility data,
				terrain analysis, exposure proxies, and existing monitoring coverage into a single ranked map of
				priority sites.
			</p>
			<p class="leading-relaxed text-stone-300 mt-3">
				It is not a landslide detector. Detection systems already exist (NASA LHASA, USGS LASER).
				What does not exist is a <strong class="text-white">prioritization layer</strong> that answers:
				<em>"Given $300 and a mason jar, where do I put the next sensor?"</em>
			</p>
		</section>

		<!-- Methodology -->
		<section>
			<h2 class="text-xl font-semibold text-amber-400 mb-3">Scientific methodology</h2>
			<div class="space-y-4 text-sm text-stone-300">
				<div class="bg-white/5 rounded-lg p-4 border border-white/10">
					<h3 class="text-white font-semibold mb-1">1. Susceptibility</h3>
					<p>
						USGS/Alaska DGGS deep-seated landslide susceptibility raster (PIR 2025-3). Continuous grid at
						~500 m resolution covering SE and South-Central Alaska. Based on geology, slope, aspect,
						and seismic ground-motion models.
					</p>
				</div>
				<div class="bg-white/5 rounded-lg p-4 border border-white/10">
					<h3 class="text-white font-semibold mb-1">2. Volume potential</h3>
					<p>
						DEM-derived relief (500 m focal window) × slope from USGS 3DEP elevation data, both
						normalized 0–1 and multiplied. Steep, high-relief fjord walls produce the largest
						volume proxies — the primary failure surfaces for tsunamigenic landslides.
					</p>
				</div>
				<div class="bg-white/5 rounded-lg p-4 border border-white/10">
					<h3 class="text-white font-semibold mb-1">3. Slide proximity</h3>
					<p>
						Distance to nearest known landslide in the DGGS Alaska Landslide Inventory (DDS 23, 6,000+
						documented events). Inverse exponential decay with 5 km characteristic distance &mdash;
						past failures indicate future risk.
					</p>
				</div>
				<div class="bg-white/5 rounded-lg p-4 border border-white/10">
					<h3 class="text-white font-semibold mb-1">4. Exposure</h3>
					<p>
						Proxy from OpenStreetMap: buildings, roads, tourism POIs, ferry terminals. Log-weighted
						composite score on a 500 m grid. Captures people and infrastructure at risk.
					</p>
				</div>
				<div class="bg-white/5 rounded-lg p-4 border border-white/10">
					<h3 class="text-white font-semibold mb-1">5. Coverage gap</h3>
					<p>
						Existing monitoring stations (Alaska Earthquake Center + DGGS weather stations) buffered
						at 10 km. Sites <em>outside</em> the buffer receive a 1.8&times; gap multiplier &mdash;
						prioritizing the unmonitored.
					</p>
				</div>
				<div class="bg-white/5 rounded-lg p-4 border border-white/10">
					<h3 class="text-white font-semibold mb-1">Scoring &amp; ranking</h3>
					<p>
						Weighted-additive: each 500 m cell gets
						<code class="text-amber-300 bg-white/5 px-1 rounded">0.25&times;susceptibility + 0.25&times;fjord_wall + 0.20&times;proximity + 0.10&times;volume_proxy + 0.10&times;exposure + 0.10&times;coverage</code>.
						No single signal can zero out another.
						Top-percentile cells clustered into contiguous zones via local-maxima detection; ranked by aggregate score.
						Top 120 zones shown on this map.
					</p>
				</div>
			</div>
		</section>

		<!-- Data-limited areas -->
		<section>
			<h2 class="text-xl font-semibold text-amber-400 mb-3">Data confidence</h2>
			<p class="leading-relaxed text-stone-300">
				The diagonal-hatch overlay shows areas where the input data is thinnest &mdash; fewer than 3 of the
				6 scoring inputs have published coverage. The "low" band (heavier hatch) covers interior areas
				with no susceptibility or DEM data; the "medium" band covers areas with partial data. Rankings in
				these zones should be treated as provisional.
			</p>
		</section>

		<!-- Credits -->
		<section>
			<h2 class="text-xl font-semibold text-amber-400 mb-3">Credits &amp; data sources</h2>
			<div class="space-y-3 text-sm">
				<div class="flex gap-3 items-start">
					<span class="text-amber-400 font-bold w-28 flex-shrink-0">DGGS</span>
					<div>
						<p class="text-stone-200">Alaska Division of Geological &amp; Geophysical Surveys</p>
						<p class="text-stone-400">Landslide inventory (DDS 23), deep-seated susceptibility raster (PIR 2025-3),
						weather station network (DDS 25)</p>
						<a href="https://dggs.alaska.gov" class="text-amber-400/80 hover:text-amber-300 text-xs" target="_blank" rel="noopener">dggs.alaska.gov</a>
					</div>
				</div>
				<div class="flex gap-3 items-start">
					<span class="text-amber-400 font-bold w-28 flex-shrink-0">USGS</span>
					<div>
						<p class="text-stone-200">U.S. Geological Survey</p>
						<p class="text-stone-400">3DEP elevation data (1/3 arc-second), news-reported slide impacts SE Alaska 1990&ndash;2024,
						Tracy Arm 2025 field photos (public domain)</p>
						<a href="https://www.usgs.gov" class="text-amber-400/80 hover:text-amber-300 text-xs" target="_blank" rel="noopener">usgs.gov</a>
					</div>
				</div>
				<div class="flex gap-3 items-start">
					<span class="text-amber-400 font-bold w-28 flex-shrink-0">USFS</span>
					<div>
						<p class="text-stone-200">U.S. Forest Service &mdash; Tongass National Forest</p>
						<p class="text-stone-400">Tongass landslide areas (Ag Data Commons, 2024)</p>
						<a href="https://agdatacommons.nal.usda.gov/articles/dataset/25972363" class="text-amber-400/80 hover:text-amber-300 text-xs" target="_blank" rel="noopener">agdatacommons.nal.usda.gov</a>
					</div>
				</div>
				<div class="flex gap-3 items-start">
					<span class="text-amber-400 font-bold w-28 flex-shrink-0">NASA</span>
					<div>
						<p class="text-stone-200">NASA Earth Observatory</p>
						<p class="text-stone-400">Landsat before/after imagery of Tracy Arm post-tsunami landscape</p>
						<a href="https://science.nasa.gov/earth/earth-observatory/tracy-arms-post-tsunami-landscape/" class="text-amber-400/80 hover:text-amber-300 text-xs" target="_blank" rel="noopener">science.nasa.gov</a>
					</div>
				</div>
				<div class="flex gap-3 items-start">
					<span class="text-amber-400 font-bold w-28 flex-shrink-0">AEC</span>
					<div>
						<p class="text-stone-200">Alaska Earthquake Center</p>
						<p class="text-stone-400">Seismic monitoring station locations (FDSN network AK)</p>
						<a href="https://earthquake.alaska.edu" class="text-amber-400/80 hover:text-amber-300 text-xs" target="_blank" rel="noopener">earthquake.alaska.edu</a>
					</div>
				</div>
				<div class="flex gap-3 items-start">
					<span class="text-amber-400 font-bold w-28 flex-shrink-0">OSM</span>
					<div>
						<p class="text-stone-200">OpenStreetMap contributors</p>
						<p class="text-stone-400">Alaska extract &mdash; buildings, roads, tourism POIs (exposure proxy)</p>
						<a href="https://download.geofabrik.de/north-america/us/alaska.html" class="text-amber-400/80 hover:text-amber-300 text-xs" target="_blank" rel="noopener">geofabrik.de</a>
					</div>
				</div>
				<div class="flex gap-3 items-start">
					<span class="text-amber-400 font-bold w-28 flex-shrink-0">Esri</span>
					<div>
						<p class="text-stone-200">Esri World Topographic Map</p>
						<p class="text-stone-400">Basemap tiles (&copy; Esri, USGS, NPS)</p>
					</div>
				</div>
			</div>
		</section>

		<!-- Inspiring context -->
		<section>
			<h2 class="text-xl font-semibold text-amber-400 mb-3">Inspiration</h2>
			<p class="leading-relaxed text-stone-300">
				Bretwood &ldquo;Hig&rdquo; Higman is an independent geologist in Seldovia, Alaska, who has spent
				a decade documenting tsunamigenic landslides in Alaska&rsquo;s fjords. He builds $300 monitoring
				sensors in mason jars and installs them by hand. This tool exists because nobody is systematically
				looking for the next Barry Arm.
			</p>
			<div class="mt-4 space-y-2 text-sm">
				<a href="https://groundtruthalaska.org/landslides" class="block text-amber-400/80 hover:text-amber-300" target="_blank" rel="noopener">
					Ground Truth Alaska &mdash; Landslide program
				</a>
				<a href="https://www.nationalgeographic.com" class="block text-amber-400/80 hover:text-amber-300" target="_blank" rel="noopener">
					National Geographic &mdash; &ldquo;Lessons of a landslide detective&rdquo; (Christian Elliott, June 2026)
				</a>
				<a href="https://www.usgs.gov/programs/landslide-hazards/science/2025-tracy-arm-landslide-generated-tsunami" class="block text-amber-400/80 hover:text-amber-300" target="_blank" rel="noopener">
					USGS &mdash; 2025 Tracy Arm landslide and tsunami
				</a>
			</div>
		</section>

		<!-- Technical stack -->
		<section>
			<h2 class="text-xl font-semibold text-amber-400 mb-3">Technical stack</h2>
			<div class="grid grid-cols-2 gap-2 text-xs text-stone-400">
				<span class="text-stone-300">Backend</span><span>Python 3.12 &middot; FastAPI &middot; GeoPandas &middot; rasterio</span>
				<span class="text-stone-300">Frontend</span><span>SvelteKit 5 &middot; MapLibre GL JS v5 &middot; Skeleton UI v4</span>
				<span class="text-stone-300">Data pipeline</span><span>Python (prep scripts) &middot; GDAL &middot; scipy</span>
				<span class="text-stone-300">AI search</span><span>LLM-powered natural-language query (provider-swappable)</span>
				<span class="text-stone-300">License</span><span>MIT &mdash; open source</span>
			</div>
		</section>

		<!-- Footer -->
		<footer class="border-t border-white/10 pt-6 text-xs text-stone-500 text-center">
			<p>
				SCARP &middot; <a href="https://github.com/flupkede/scarp-app" class="text-amber-400/60 hover:text-amber-300" target="_blank" rel="noopener">github.com/flupkede/scarp-app</a>
				&middot; No copyrighted media embedded &middot; US Government works are public domain
			</p>
		</footer>

	</div>
</div>
