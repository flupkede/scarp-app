<svelte:head>
	<title>The Story — SCARP</title>
	<meta name="description" content="Why Alaska's fjords are failing faster, and why nobody sees it coming." />
</svelte:head>

<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	// Slide refs for scroll navigation
	let slideEls: HTMLElement[] = $state([]);
	let currentSlide = $state(0);
	let container: HTMLElement | undefined = $state();

	const TOTAL_SLIDES = 7;

	// Before/After slider
	let sliderPos = $state(50); // percent
	let sliderDragging = $state(false);
	let sliderEl: HTMLElement | undefined = $state();

	function startDrag(e: MouseEvent | TouchEvent) {
		sliderDragging = true;
		e.preventDefault();
	}

	function onDrag(e: MouseEvent | TouchEvent) {
		if (!sliderDragging || !sliderEl) return;
		const rect = sliderEl.getBoundingClientRect();
		const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
		const pct = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
		sliderPos = pct;
	}

	function stopDrag() {
		sliderDragging = false;
	}

	function scrollToSlide(index: number) {
		const el = slideEls[index];
		if (el) {
			el.scrollIntoView({ behavior: 'smooth' });
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'ArrowDown' || e.key === ' ') {
			e.preventDefault();
			if (currentSlide < TOTAL_SLIDES - 1) scrollToSlide(currentSlide + 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			if (currentSlide > 0) scrollToSlide(currentSlide - 1);
		}
	}

	function updateCurrentSlide() {
		if (!container) return;
		const scrollTop = container.scrollTop;
		const height = container.clientHeight;
		const idx = Math.round(scrollTop / height);
		currentSlide = Math.max(0, Math.min(TOTAL_SLIDES - 1, idx));
	}

	onMount(() => {
		window.addEventListener('keydown', handleKeydown);
		window.addEventListener('mousemove', onDrag);
		window.addEventListener('mouseup', stopDrag);
		window.addEventListener('touchmove', onDrag, { passive: false });
		window.addEventListener('touchend', stopDrag);
		return () => {
			window.removeEventListener('keydown', handleKeydown);
			window.removeEventListener('mousemove', onDrag);
			window.removeEventListener('mouseup', stopDrag);
			window.removeEventListener('touchmove', onDrag);
			window.removeEventListener('touchend', stopDrag);
		};
	});
</script>

<!-- Back to map — fixed top-left -->
<a href="/" class="back-btn" aria-label="Back to map">
	<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
		<path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
	</svg>
	Map
</a>

<!-- Progress dots — fixed right edge -->
<nav class="progress-dots" aria-label="Story navigation">
	{#each Array(TOTAL_SLIDES) as _, i}
		<button
			class="dot"
			class:active={currentSlide === i}
			onclick={() => scrollToSlide(i)}
			aria-label="Go to slide {i + 1}"
		></button>
	{/each}
</nav>

<!-- Scroll container -->
<div
	class="story-container"
	bind:this={container}
	onscroll={updateCurrentSlide}
	role="region"
	aria-label="Story slides"
>

	<!-- Slide 0: Cover -->
	<section
		class="slide slide-cover"
		bind:this={slideEls[0]}
		aria-label="Cover"
	>
		<!-- 
			USGS Tracy Arm 2025 landslide photo (public domain, US Gov work).
			Source: https://www.usgs.gov/programs/landslide-hazards/science/2025-tracy-arm-landslide-generated-tsunami
			Replace this placeholder with the downloaded image placed at /static/tracy-arm-cover.jpg
		-->
		<div class="cover-bg">
			<div class="cover-overlay"></div>
			<div class="cover-content">
				<div class="cover-badge">August 2025 · Tracy Arm, Alaska</div>
				<blockquote class="cover-quote">
					In 1958, Lituya Bay saw the highest wave ever recorded&thinsp;—&thinsp;524&nbsp;m.
					In August 2025, Tracy Arm made the second-highest ever&thinsp;—&thinsp;481&nbsp;m.
					<em>Nobody saw it coming.</em>
				</blockquote>
				<a href="#slide-1" onclick={(e) => { e.preventDefault(); scrollToSlide(1); }} class="scroll-hint">
					<span>The story</span>
					<svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
						<path d="M10 4v12M4 10l6 6 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</a>
			</div>
		</div>
		<div class="cover-source-credit">
			Photo placeholder · USGS public domain · <a href="https://www.usgs.gov/programs/landslide-hazards/science/2025-tracy-arm-landslide-generated-tsunami" target="_blank" rel="noopener">source</a>
		</div>
	</section>

	<!-- Slide 1: Before / After -->
	<section
		class="slide slide-beforeafter"
		bind:this={slideEls[1]}
		id="slide-1"
		aria-label="Before and after Tracy Arm"
	>
		<!-- Background image with dark overlay -->
		<div class="slide-bg" aria-hidden="true"></div>
		<div class="slide-bg-overlay" aria-hidden="true"></div>

		<div class="slide-inner" style="position:relative;z-index:1;">
			<h2 class="slide-heading slide-heading--light">Before &amp; After</h2>
			<p class="slide-subhead slide-subhead--light">Tracy Arm Fjord · 26 July 2025 vs. 19 August 2025</p>

			<!-- Before/After drag slider -->
			<div
				class="ba-slider"
				bind:this={sliderEl}
				onmousedown={startDrag}
				ontouchstart={startDrag}
				role="slider"
				aria-label="Before/after comparison slider"
				aria-valuenow={Math.round(sliderPos)}
				aria-valuemin={0}
				aria-valuemax={100}
				tabindex="0"
				onkeydown={(e) => {
					if (e.key === 'ArrowLeft') sliderPos = Math.max(0, sliderPos - 2);
					if (e.key === 'ArrowRight') sliderPos = Math.min(100, sliderPos + 2);
				}}
			>
				<!-- AFTER image: NASA Landsat 19 Aug 2025 — post-landslide (brown scar visible) -->
				<img class="ba-img ba-img--after" src="/tracy-arm-after.jpg" alt="After: Tracy Arm 19 August 2025 — landslide scar and stripped forest visible" draggable="false" />
				<span class="ba-label ba-label--right">After · 19 Aug 2025</span>

				<!-- BEFORE image: NASA Landsat 26 Jul 2025 — intact green forest -->
				<img class="ba-img ba-img--before" src="/tracy-arm-before.jpg" alt="Before: Tracy Arm 26 July 2025 — intact green forest on fjord wall" draggable="false"
					style="clip-path: inset(0 {100 - sliderPos}% 0 0);" />
				<span class="ba-label ba-label--left" style="opacity: {sliderPos > 12 ? 1 : 0}">Before · 26 Jul 2025</span>

				<!-- Divider handle -->
				<div class="ba-handle" style="left:{sliderPos}%">
					<div class="ba-handle-line"></div>
					<div class="ba-handle-circle">
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
							<path d="M7 10l-3-3m0 0l3-3M4 7h12M13 10l3 3m0 0l-3 3M16 13H4" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
					</div>
				</div>
			</div>

			<p class="slide-body slide-body--light">
				The August 2025 landslide stripped an estimated <strong>3.2&nbsp;km²</strong> of forest from the fjord wall in seconds. The debris entered deep water — the precise condition that amplifies a local rockfall into a regional tsunami.
			</p>
			<p class="slide-body--credit-light">
				NASA Landsat · public domain ·
				<a href="https://science.nasa.gov/earth/earth-observatory/tracy-arms-post-tsunami-landscape/" target="_blank" rel="noopener">NASA Earth Observatory →</a>
			</p>
		</div>
	</section>

	<!-- Slide 2: Hig & the mason jars -->
	<section
		class="slide slide-hig"
		bind:this={slideEls[2]}
		aria-label="Hig and the mason jar sensors"
	>
		<!-- Background image with dark overlay -->
		<div class="slide-bg" aria-hidden="true"></div>
		<div class="slide-bg-overlay slide-bg-overlay--amber" aria-hidden="true"></div>

		<div class="slide-inner" style="position:relative;z-index:1;">
			<div class="mason-jar-icon" aria-hidden="true">
				<!-- Mason jar SVG — original artwork, no copyright -->
				<svg width="72" height="96" viewBox="0 0 72 96" fill="none" xmlns="http://www.w3.org/2000/svg">
					<rect x="18" y="8" width="36" height="6" rx="2" fill="#92400e"/>
					<rect x="14" y="14" width="44" height="4" rx="2" fill="#78350f"/>
					<path d="M10 18h52l-4 64H14L10 18z" fill="#fef9c3" fill-opacity="0.7" stroke="#92400e" stroke-width="2"/>
					<!-- liquid level -->
					<path d="M13 50h46l-2 32H15L13 50z" fill="#86efac" fill-opacity="0.5"/>
					<!-- sensor wire -->
					<line x1="36" y1="18" x2="36" y2="82" stroke="#1c1917" stroke-width="1.5" stroke-dasharray="4 3"/>
					<circle cx="36" cy="72" r="4" fill="#ef4444"/>
					<!-- label lines -->
					<rect x="20" y="34" width="32" height="3" rx="1.5" fill="#d6d3d1" fill-opacity="0.6"/>
					<rect x="22" y="40" width="28" height="3" rx="1.5" fill="#d6d3d1" fill-opacity="0.6"/>
				</svg>
			</div>

			<h2 class="slide-heading slide-heading--light">$300 &amp; a mason jar</h2>

			<p class="slide-body slide-body--large slide-body--light">
				Bretwood "Hig" Higman is an independent PhD geologist based in Seldovia, Alaska. He builds his own monitoring sensors — accelerometers sealed in mason jars — for roughly $300&nbsp;each. He installs them by hand, often by kayak, on the unstable slopes above Alaska's fjords.
			</p>
			<p class="slide-body slide-body--light">
				He cannot be everywhere. No federal or state agency is systematically surveilling these slopes. The U.S. National Landslide Preparedness Act was triggered partly by Hig's 2020 discovery at Barry Arm — a 500-million-cubic-meter mass that could generate a wave reaching Anchorage. Most of the slides that have happened since were not on any watchlist.
			</p>
			<p class="slide-body slide-body--credit slide-body--credit-light">
				— <em>Lessons of a landslide detective</em>, Christian Elliott, <em>National Geographic</em>, June 2026
			</p>
		</div>
	</section>

	<!-- Slide 3: Science quotes (dark) -->
	<section
		class="slide slide-quotes"
		bind:this={slideEls[3]}
		aria-label="Science findings"
	>
		<div class="slide-inner">
			<h2 class="slide-heading slide-heading--light">What the data shows</h2>

			<div class="quotes-grid">
				<figure class="science-quote">
					<blockquote>
						Examined eight large rock-slope failures in deglaciating southern Alaska; six accelerated as the supporting glacier retreated. The authors call for "broader and more systematic paraglacial hazard monitoring in a warming world."
					</blockquote>
					<figcaption>Walden et al., <em>Natural Hazards and Earth System Sciences</em>, 2025 (Higman co-author)</figcaption>
				</figure>

				<figure class="science-quote">
					<blockquote>
						"No systematic landslide warning threshold currently exists at either local scales for towns within southeast Alaska or the regional scale," despite the area's high susceptibility to slope failures.
					</blockquote>
					<figcaption>Patton et al., <em>Natural Hazards and Earth System Sciences</em>, 2023</figcaption>
				</figure>
			</div>

			<p class="quotes-footer">
				Accelerating failures. Rising visitor numbers. No systematic early-warning network.
			</p>
		</div>
	</section>

	<!-- Slide 4: Live map -->
	<section
		class="slide slide-map"
		bind:this={slideEls[4]}
		aria-label="Live priority map"
	>
		<div class="slide-inner slide-inner--map">
			<h2 class="slide-heading">The map Hig doesn't have yet</h2>
			<p class="slide-subhead">120 priority sensor sites, ranked by susceptibility × exposure × monitoring gap</p>

			<div class="map-embed-frame">
				<a href="/" class="map-embed-link">
					<div class="map-embed-placeholder">
						<svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
							<path d="M8 12l12-4 8 4 12-4v28l-12 4-8-4-12 4V12z" stroke="#f59e0b" stroke-width="2" stroke-linejoin="round" fill="none"/>
							<circle cx="20" cy="24" r="4" fill="#f59e0b" fill-opacity="0.6"/>
							<circle cx="32" cy="20" r="3" fill="#dc2626" fill-opacity="0.7"/>
						</svg>
						<span class="map-embed-cta">Open the live map →</span>
					</div>
				</a>
			</div>

			<ul class="map-stats">
				<li><strong>120</strong> candidate sites scored</li>
				<li><strong>5</strong> data layers fused</li>
				<li><strong>Southeast Alaska</strong> scope (SEAK)</li>
			</ul>
		</div>
	</section>

	<!-- Slide 5: Data-lag finding -->
	<section
		class="slide slide-finding"
		bind:this={slideEls[5]}
		aria-label="Key finding: data lag"
	>
		<div class="slide-inner">
			<div class="finding-number" aria-hidden="true">#61</div>

			<h2 class="slide-heading">Tracy Arm ranked 61st</h2>

			<p class="slide-body slide-body--large">
				When we run our scoring model today, Tracy Arm sits at rank&nbsp;61. The geology is nearly perfect: steep unstable rock, glacial retreat, 200&nbsp;m of water below. But our public data here is thin.
			</p>
			<p class="slide-body">
				Landslide inventory coverage in Southeast Alaska has an order-of-magnitude gap between fjords with road access and those reachable only by floatplane or boat. Tracy Arm had never been surveyed by the DGGS inventory crew before 2025.
			</p>

			<div class="finding-callout">
				<strong>The lesson:</strong> The sites we don't know about are ranked lower not because they're safer — but because nobody looked. SCARP flags these data-limited zones explicitly, so Hig knows where the gap is the problem.
			</div>
		</div>
	</section>

	<!-- Slide 6: Credits -->
	<section
		class="slide slide-credits"
		bind:this={slideEls[6]}
		aria-label="Credits and data sources"
	>
		<div class="slide-inner">
			<h2 class="slide-heading">Credits &amp; Sources</h2>

			<div class="credits-grid">
				<div class="credit-group">
					<h3 class="credit-group-title">Data</h3>
					<ul class="credit-list">
						<li>
							<a href="https://dggs.alaska.gov/pubs/id/31697" target="_blank" rel="noopener">Alaska DGGS</a>
							— Landslide inventory + susceptibility raster
						</li>
						<li>
							<a href="https://www.usgs.gov/data/news-reported-landslide-impacts-southeast-alaska-1990-2024" target="_blank" rel="noopener">USGS</a>
							— SEAK news-reported slides, DEMs, Tracy Arm field data
						</li>
						<li>
							<a href="https://science.nasa.gov/earth/earth-observatory/tracy-arms-post-tsunami-landscape/" target="_blank" rel="noopener">NASA Landsat / Earth Observatory</a>
							— before/after imagery
						</li>
						<li>
							<a href="https://www.openstreetmap.org" target="_blank" rel="noopener">OpenStreetMap contributors</a>
							— roads, buildings, tourism POIs
						</li>
						<li>
							<a href="https://agdatacommons.nal.usda.gov/articles/dataset/25972363" target="_blank" rel="noopener">USFS</a>
							— Tongass National Forest landslide areas
						</li>
					</ul>
				</div>

				<div class="credit-group">
					<h3 class="credit-group-title">Inspiration</h3>
					<ul class="credit-list">
						<li>
							<em>Lessons of a landslide detective</em> — Christian Elliott,
							<a href="https://www.nationalgeographic.com" target="_blank" rel="noopener">National Geographic</a>, June 2026
						</li>
						<li>
							<a href="https://groundtruthalaska.org/landslides" target="_blank" rel="noopener">Ground Truth Alaska</a>
							— Hig's nonprofit + field data
						</li>
						<li>
							<a href="http://www.sitkalandslide.org" target="_blank" rel="noopener">Sitka Sound Landslide Warning System</a>
							— rainfall-triggered model reference
						</li>
					</ul>
				</div>

				<div class="credit-group">
					<h3 class="credit-group-title">Built by</h3>
					<ul class="credit-list">
						<li>Filip + OpenCode · North Star AI Hackathon 2025</li>
						<li>
							<a href="https://github.com/flupkede/scarp" target="_blank" rel="noopener">github.com/flupkede/scarp</a>
							· MIT License
						</li>
					</ul>
				</div>
			</div>

			<div class="credits-disclaimer">
				SCARP is a first-order prioritization tool, not a validated hazard model. Rankings indicate where professional geologic assessment is most urgently needed, not certainty of failure.
			</div>

			<div class="credits-nav">
				<a href="/" class="btn-primary">Open the map</a>
				<a href="/about" class="btn-secondary">About this project</a>
			</div>
		</div>
	</section>

</div>

<style>
	/* ── Layout ── */
	.story-container {
		height: 100vh;
		overflow-y: scroll;
		scroll-snap-type: y mandatory;
		scroll-behavior: smooth;
	}

	.slide {
		height: 100vh;
		scroll-snap-align: start;
		overflow: hidden;
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}

	.slide-inner {
		max-width: 720px;
		margin: 0 auto;
		padding: 3rem 2rem;
		width: 100%;
	}

	/* ── Back button ── */
	.back-btn {
		position: fixed;
		top: 1rem;
		left: 1rem;
		z-index: 100;
		display: inline-flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.4rem 0.75rem 0.4rem 0.5rem;
		background: rgba(28, 25, 23, 0.65);
		backdrop-filter: blur(8px);
		color: rgba(248, 250, 252, 0.85);
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-decoration: none;
		border-radius: 999px;
		border: 1px solid rgba(248, 250, 252, 0.15);
		transition: background 0.2s, color 0.2s;
	}

	.back-btn:hover {
		background: rgba(28, 25, 23, 0.9);
		color: #fcd34d;
	}

	/* ── Progress dots ── */
	.progress-dots {
		position: fixed;
		right: 1.5rem;
		top: 50%;
		transform: translateY(-50%);
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		z-index: 100;
	}

	.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: rgba(120, 53, 15, 0.25);
		border: none;
		cursor: pointer;
		transition: background 0.2s, transform 0.2s;
		padding: 0;
	}

	.dot.active {
		background: #92400e;
		transform: scale(1.4);
	}

	.dot:hover:not(.active) {
		background: rgba(120, 53, 15, 0.5);
	}

	/* ── Typography ── */
	.slide-heading {
		font-family: 'Georgia', 'Times New Roman', serif;
		font-size: clamp(1.75rem, 4vw, 2.75rem);
		font-weight: 700;
		color: #1c1917;
		margin-bottom: 0.75rem;
		line-height: 1.15;
	}

	.slide-heading--light {
		color: #fef9c3;
	}

	.slide-subhead {
		font-size: 1rem;
		color: #78716c;
		margin-bottom: 2rem;
		letter-spacing: 0.01em;
	}

	.slide-body {
		font-size: 1.0625rem;
		line-height: 1.75;
		color: #292524;
		margin-bottom: 1rem;
	}

	.slide-body--large {
		font-size: 1.1875rem;
	}

	.slide-body--credit {
		font-size: 0.875rem;
		color: #78716c;
		margin-top: 1.5rem;
	}

	/* ── Slide 0: Cover ── */
	.slide-cover {
		background: #0f172a;
	}

	.cover-bg {
		position: absolute;
		inset: 0;
		background: url('/splash-tracy-arm.jpg') center / cover no-repeat, linear-gradient(160deg, #0f172a 0%, #1e293b 40%, #292524 100%);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.cover-overlay {
		position: absolute;
		inset: 0;
		background: linear-gradient(to bottom, rgba(15,23,42,0.3) 0%, rgba(15,23,42,0.75) 100%);
	}

	.cover-content {
		position: relative;
		z-index: 1;
		max-width: 680px;
		padding: 2rem;
		text-align: center;
	}

	.cover-badge {
		display: inline-block;
		font-size: 0.75rem;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: #fbbf24;
		background: rgba(251, 191, 36, 0.12);
		border: 1px solid rgba(251, 191, 36, 0.3);
		border-radius: 999px;
		padding: 0.25rem 0.875rem;
		margin-bottom: 1.5rem;
	}

	.cover-quote {
		font-family: 'Georgia', 'Times New Roman', serif;
		font-size: clamp(1.1rem, 3vw, 1.6rem);
		line-height: 1.5;
		color: #f8fafc;
		font-style: normal;
		margin: 0 0 2rem;
	}

	.cover-quote em {
		font-style: italic;
		color: #fcd34d;
	}

	.scroll-hint {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #94a3b8;
		font-size: 0.875rem;
		text-decoration: none;
		transition: color 0.2s;
	}

	.scroll-hint:hover {
		color: #f8fafc;
	}

	.cover-source-credit {
		position: absolute;
		bottom: 1rem;
		left: 0;
		right: 0;
		text-align: center;
		font-size: 0.7rem;
		color: rgba(248, 250, 252, 0.35);
		z-index: 1;
	}

	.cover-source-credit a {
		color: rgba(248, 250, 252, 0.5);
	}

	/* ── Shared: background image slides ── */
	.slide-bg {
		position: absolute;
		inset: 0;
		background: url('/splash-tracy-arm.jpg') center / cover no-repeat;
		z-index: 0;
	}

	.slide-bg-overlay {
		position: absolute;
		inset: 0;
		background: linear-gradient(to bottom, rgba(15,23,42,0.72) 0%, rgba(15,23,42,0.82) 100%);
		z-index: 0;
	}

	.slide-bg-overlay--amber {
		background: linear-gradient(to bottom, rgba(28,10,0,0.70) 0%, rgba(28,10,0,0.85) 100%);
	}

	/* Light text variants for image-backed slides */
	.slide-subhead--light {
		color: rgba(248,250,252,0.65);
	}

	.slide-body--light {
		color: rgba(248,250,252,0.88);
	}

	.slide-body--credit-light {
		font-size: 0.8rem;
		color: rgba(248,250,252,0.45);
		margin-top: 0.75rem;
	}

	.slide-body--credit-light a {
		color: #fcd34d;
		text-decoration: none;
	}

	.slide-body--credit-light a:hover { text-decoration: underline; }

	/* ── Slide 1: Before/After ── */
	.slide-beforeafter {
		background: #0f172a; /* fallback if image fails */
	}

	/* ── Before/After slider ── */
	.ba-slider {
		position: relative;
		width: 100%;
		aspect-ratio: 16/7;
		overflow: hidden;
		border-radius: 6px;
		cursor: col-resize;
		user-select: none;
		margin-bottom: 1.25rem;
		box-shadow: 0 4px 24px rgba(0,0,0,0.5);
	}

	/* Both images fill the slider absolutely */
	.ba-img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		pointer-events: none;
		display: block;
	}

	.ba-img--after {
		z-index: 1;
	}

	.ba-img--before {
		z-index: 2;
		/* clip-path is set inline via Svelte binding */
	}

	.ba-label {
		position: absolute;
		bottom: 0.5rem;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: white;
		background: rgba(0,0,0,0.55);
		padding: 0.2rem 0.5rem;
		border-radius: 3px;
		pointer-events: none;
		z-index: 5;
		transition: opacity 0.15s;
	}

	.ba-label--left { left: 0.5rem; }
	.ba-label--right { right: 0.5rem; }

	.ba-handle {
		position: absolute;
		top: 0;
		bottom: 0;
		transform: translateX(-50%);
		width: 3px;
		z-index: 10;
		pointer-events: none;
		transition: none;
	}

	.ba-handle-line {
		position: absolute;
		inset: 0;
		background: white;
		opacity: 0.9;
	}

	.ba-handle-circle {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 40px;
		height: 40px;
		border-radius: 50%;
		background: white;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 2px 8px rgba(0,0,0,0.4);
	}

	.ba-handle-circle svg {
		color: #1c1917;
	}

	/* ── Slide 2: Hig ── */
	.slide-hig {
		background: #1c0a00; /* fallback if image fails */
	}

	.mason-jar-icon {
		margin-bottom: 1.25rem;
	}

	/* ── Slide 3: Quotes ── */
	.slide-quotes {
		background: #0f172a;
	}

	.quotes-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin: 2rem 0;
	}

	.science-quote {
		background: rgba(248, 250, 252, 0.05);
		border-left: 3px solid #f59e0b;
		padding: 1.25rem 1.25rem 1rem;
		margin: 0;
		border-radius: 0 4px 4px 0;
	}

	.science-quote blockquote {
		font-size: 0.9375rem;
		line-height: 1.65;
		color: #e2e8f0;
		font-style: italic;
		margin: 0 0 0.75rem;
	}

	.science-quote figcaption {
		font-size: 0.75rem;
		color: #94a3b8;
	}

	.quotes-footer {
		text-align: center;
		font-size: 1rem;
		color: #fcd34d;
		font-weight: 600;
		letter-spacing: 0.01em;
	}

	/* ── Slide 4: Map ── */
	.slide-map {
		background: #1c1917;
	}

	.slide-map .slide-heading { color: #fef9c3; }
	.slide-map .slide-subhead { color: #a8a29e; }

	.slide-inner--map {
		text-align: center;
	}

	.map-embed-frame {
		margin: 1.5rem auto;
		max-width: 480px;
		border: 2px solid rgba(245, 158, 11, 0.4);
		border-radius: 8px;
		overflow: hidden;
	}

	.map-embed-link {
		display: block;
		text-decoration: none;
	}

	.map-embed-placeholder {
		height: 240px;
		background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		transition: background 0.2s;
	}

	.map-embed-placeholder:hover {
		background: linear-gradient(135deg, #1e3a5f 0%, #1c2d4a 100%);
	}

	.map-embed-cta {
		font-size: 1rem;
		font-weight: 600;
		color: #f59e0b;
	}

	.map-stats {
		display: flex;
		justify-content: center;
		gap: 2.5rem;
		list-style: none;
		padding: 0;
		margin: 1rem 0 0;
		font-size: 0.9rem;
		color: #a8a29e;
	}

	.map-stats strong {
		display: block;
		font-size: 1.5rem;
		color: #fef9c3;
		font-family: 'Georgia', serif;
	}

	/* ── Slide 5: Finding ── */
	.slide-finding {
		background: #f5f0eb;
	}

	.finding-number {
		font-family: 'Georgia', 'Times New Roman', serif;
		font-size: clamp(4rem, 12vw, 8rem);
		font-weight: 700;
		color: #fde68a;
		line-height: 1;
		margin-bottom: 0.25rem;
		-webkit-text-stroke: 2px #92400e;
	}

	.finding-callout {
		margin-top: 1.5rem;
		padding: 1rem 1.25rem;
		background: #fef3c7;
		border-left: 4px solid #f59e0b;
		border-radius: 0 4px 4px 0;
		font-size: 0.9375rem;
		line-height: 1.6;
		color: #1c1917;
	}

	/* ── Slide 6: Credits ── */
	.slide-credits {
		background: #1c1917;
		overflow-y: auto;
	}

	.slide-credits .slide-heading { color: #fef9c3; }

	.credits-grid {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		gap: 1.5rem;
		margin: 1.5rem 0;
	}

	.credit-group-title {
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: #a8a29e;
		margin-bottom: 0.75rem;
		font-weight: 600;
	}

	.credit-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.credit-list li {
		font-size: 0.8125rem;
		line-height: 1.5;
		color: #d6d3d1;
	}

	.credit-list a {
		color: #fcd34d;
		text-decoration: none;
	}

	.credit-list a:hover { text-decoration: underline; }

	.credits-disclaimer {
		margin-top: 1rem;
		padding: 0.875rem 1rem;
		background: rgba(248, 250, 252, 0.05);
		border-radius: 4px;
		font-size: 0.8125rem;
		line-height: 1.6;
		color: #78716c;
	}

	.credits-nav {
		display: flex;
		gap: 1rem;
		margin-top: 1.5rem;
		justify-content: center;
	}

	.btn-primary {
		display: inline-block;
		padding: 0.6rem 1.5rem;
		background: #f59e0b;
		color: #1c1917;
		font-weight: 600;
		border-radius: 4px;
		text-decoration: none;
		font-size: 0.9rem;
		transition: background 0.15s;
	}

	.btn-primary:hover { background: #d97706; }

	.btn-secondary {
		display: inline-block;
		padding: 0.6rem 1.5rem;
		background: transparent;
		color: #d6d3d1;
		font-weight: 500;
		border-radius: 4px;
		border: 1px solid #44403c;
		text-decoration: none;
		font-size: 0.9rem;
		transition: border-color 0.15s, color 0.15s;
	}

	.btn-secondary:hover {
		border-color: #78716c;
		color: #fef9c3;
	}

	/* ── Responsive ── */
	@media (max-width: 640px) {
		.quotes-grid {
			grid-template-columns: 1fr;
		}

		.credits-grid {
			grid-template-columns: 1fr;
		}

		.progress-dots {
			right: 0.75rem;
		}

		.map-stats {
			flex-direction: column;
			gap: 0.75rem;
			align-items: center;
		}
	}
</style>
