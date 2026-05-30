<svelte:head>
	<title>About — SCARP</title>
</svelte:head>

<div class="min-h-screen bg-paper">
	<div class="max-w-3xl mx-auto px-6 py-12">
		<a href="/" class="text-sm text-amber-700 hover:text-amber-800 mb-8 inline-block">← Back to map</a>

		<h1 class="text-4xl font-serif font-bold text-ink mb-8">The Problem</h1>

		<div class="prose prose-stone max-w-none">
			<p class="text-lg leading-relaxed">
				In 1958, a landslide in Lituya Bay, Alaska, generated the tallest tsunami wave ever recorded on Earth — 524 meters of runup that stripped old-growth forest from the slopes. In 2015, the Taan Fiord slide sent water 193 meters up a mountainside and leveled eight square miles of wilderness.
			</p>

			<p class="text-lg leading-relaxed">
				Since 2020, tsunamigenic landslides in Alaska's fjords have increased roughly tenfold. Glacial retreat removes the ice buttressing steep valley walls. Permafrost thaws. Rainfall intensifies. The slopes are failing, and they're failing into deep water — the recipe for megatsunamis.
			</p>

			<p class="text-lg leading-relaxed">
				In August 2025, a massive landslide at Tracy Arm generated a tsunami that came within 50 meters of the 1958 Lituya record. Nobody saw it coming. Bretwood "Hig" Higson, an independent geologist in Seldovia, Alaska, builds his own monitoring sensors for $300 in mason jars and installs them by hand. He cannot be everywhere. Nobody is systematically looking for the next one.
			</p>

			<h2 class="text-2xl font-serif font-bold text-ink mt-10 mb-4">The Approach</h2>

			<p>SCARP combines five data inputs to prioritize where to place the next sensor:</p>

			<ul class="space-y-2 mt-4">
				<li><strong>Susceptibility</strong> — USGS 10m DEM-derived slope stability model</li>
				<li><strong>Fjord wall proximity</strong> — steep terrain adjacent to deep water</li>
				<li><strong>Slide proximity</strong> — distance to known historical landslides</li>
				<li><strong>Exposure</strong> — buildings, roads, tourism, marine traffic</li>
				<li><strong>Monitoring gap</strong> — distance from existing seismic/weather stations</li>
			</ul>

			<p class="mt-4">Each candidate site is scored on a 0–1 scale. The 120 highest-scoring locations are ranked and mapped with influence radii showing the area each sensor would help monitor.</p>

			<h2 class="text-2xl font-serif font-bold text-ink mt-10 mb-4">Credits &amp; Ethics</h2>

			<ul class="space-y-2">
				<li>
					Inspired by <em>Lessons of a landslide detective</em> by Christian Elliott, <em>National Geographic</em>, June 2026
				</li>
				<li>Data: Alaska DGGS, USGS, NASA, OpenStreetMap contributors</li>
				<li>Imagery: USGS public domain</li>
				<li>
					Built for <strong>North Star AI Hackathon</strong>, 2025
				</li>
				<li>
					Code: <a href="https://github.com/flupkede/scarp" class="text-amber-700 hover:underline">github.com/flupkede/scarp</a>
				</li>
			</ul>

			<div class="mt-8 p-4 bg-stone-100 rounded-lg text-sm text-stone-600">
				<strong>Honest note:</strong> SCARP is a first-order prioritization tool, not a validated hazard model. It identifies data gaps and highlights where professional geologic assessment is most urgently needed. Rankings should be treated as guidance, not prediction.
			</div>
		</div>
	</div>
</div>
