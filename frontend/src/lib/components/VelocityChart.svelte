<script lang="ts">
	import type { GlacierTimeseriesPoint } from '$lib/api';

	let { data }: { data: GlacierTimeseriesPoint } = $props();

	// SVG viewport
	const W = 280;
	const H = 100;
	const PAD = { top: 10, right: 8, bottom: 18, left: 40 };

	let annual = $derived(data.annual);
	let episodes = $derived(data.episodes);

	// X / Y domains
	let xMin = $derived(annual.length ? annual[0].year : 2013);
	let xMax = $derived(annual.length ? annual[annual.length - 1].year : 2024);
	let rawYMin = $derived(annual.length ? Math.min(...annual.map((d) => d.v_median)) : 0);
	let rawYMax = $derived(annual.length ? Math.max(...annual.map((d) => d.v_median)) : 500);
	let yPad = $derived(Math.max(10, (rawYMax - rawYMin) * 0.12));
	let yMin = $derived(rawYMin - yPad);
	let yMax = $derived(rawYMax + yPad);

	function sx(year: number): number {
		const range = xMax - xMin || 1;
		return PAD.left + ((year - xMin) / range) * (W - PAD.left - PAD.right);
	}
	function sy(v: number): number {
		const range = yMax - yMin || 1;
		return H - PAD.bottom - ((v - yMin) / range) * (H - PAD.top - PAD.bottom);
	}

	// Polyline path
	let linePath = $derived(
		annual.length < 2
			? ''
			: annual
					.map((d, i) => `${i === 0 ? 'M' : 'L'}${sx(d.year).toFixed(1)},${sy(d.v_median).toFixed(1)}`)
					.join(' ')
	);

	// Trend line endpoints
	let midYear = $derived((xMin + xMax) / 2);
	let trendY1 = $derived(sy(data.v_mean + data.trend_m_yr_per_year * (xMin - midYear)));
	let trendY2 = $derived(sy(data.v_mean + data.trend_m_yr_per_year * (xMax - midYear)));

	// Y-axis ticks (2–3 round values)
	let yTicks = $derived.by((): number[] => {
		if (!annual.length) return [];
		const lo = Math.floor(yMin / 100) * 100;
		const hi = Math.ceil(yMax / 100) * 100;
		const step = Math.max(100, Math.ceil((hi - lo) / 3 / 100) * 100);
		const ticks: number[] = [];
		for (let v = lo; v <= hi + 1; v += step) ticks.push(v);
		return ticks;
	});

	// X-axis ticks (every 2–3 years)
	let xTicks = $derived.by((): number[] => {
		if (!annual.length) return [];
		const span = xMax - xMin;
		const step = span <= 6 ? 1 : span <= 12 ? 2 : 3;
		const ticks: number[] = [];
		for (let y = xMin; y <= xMax; y += step) ticks.push(y);
		return ticks;
	});

	let trendLabel = $derived(
		`${data.trend_m_yr_per_year >= 0 ? '+' : ''}${data.trend_m_yr_per_year.toFixed(2)} m/yr·yr`
	);
</script>

<div class="mt-4">
	<h5 class="text-[10px] text-stone-500 uppercase tracking-wide mb-1 flex items-center gap-2">
		<span>Annual velocity — {data.point_id}</span>
		{#if data.retreat_tail}
			<span class="text-amber-600 normal-case">(data gap — possible retreat)</span>
		{/if}
	</h5>

	<svg viewBox="0 0 {W} {H}" class="w-full" style="height:100px" aria-label="Glacier velocity chart">
		<!-- Gridlines + Y ticks -->
		{#each yTicks as tick}
			<line
				x1={PAD.left}
				y1={sy(tick)}
				x2={W - PAD.right}
				y2={sy(tick)}
				stroke="#e5e7eb"
				stroke-width="0.5"
			/>
			<text
				x={PAD.left - 3}
				y={sy(tick)}
				text-anchor="end"
				dominant-baseline="middle"
				font-size="7"
				fill="#9ca3af">{tick}</text
			>
		{/each}

		<!-- Trend line (dashed slate) -->
		{#if annual.length >= 2}
			<line
				x1={sx(xMin)}
				y1={trendY1}
				x2={sx(xMax)}
				y2={trendY2}
				stroke="#94a3b8"
				stroke-width="0.8"
				stroke-dasharray="3 2"
			/>
		{/if}

		<!-- Velocity line -->
		{#if linePath}
			<path d={linePath} fill="none" stroke="#0ea5e9" stroke-width="1.5" stroke-linejoin="round" />
		{/if}

		<!-- Data dots -->
		{#each annual as d}
			<circle cx={sx(d.year)} cy={sy(d.v_median)} r="2" fill="#0ea5e9" />
		{/each}

		<!-- Episode markers (vertical dashed lines) -->
		{#each episodes as ep}
			{@const color = ep.direction === 'accelerate' ? '#dc2626' : '#3b82f6'}
			<line
				x1={sx(ep.year)}
				y1={PAD.top}
				x2={sx(ep.year)}
				y2={H - PAD.bottom}
				stroke={color}
				stroke-width="1"
				stroke-dasharray="2 2"
				opacity="0.75"
			/>
		{/each}

		<!-- X-axis ticks -->
		{#each xTicks as year}
			<text
				x={sx(year)}
				y={H - PAD.bottom + 7}
				text-anchor="middle"
				font-size="7"
				fill="#9ca3af">{year}</text
			>
		{/each}

		<!-- Y-axis unit label -->
		<text
			transform={`rotate(-90,${PAD.left - 30},${H / 2})`}
			x={PAD.left - 30}
			y={H / 2}
			text-anchor="middle"
			font-size="7"
			fill="#9ca3af">m/yr</text
		>
	</svg>

	<!-- Legend row -->
	<div class="flex items-center gap-3 text-[10px] text-stone-400 mt-0.5 flex-wrap">
		<span><span style="color:#0ea5e9">—</span> velocity</span>
		<span><span style="color:#94a3b8">– –</span> trend ({trendLabel})</span>
		{#if episodes.length}
			<span>
				<span style="color:#dc2626">|</span> accel
				<span style="color:#3b82f6">|</span> decel
			</span>
		{/if}
	</div>
</div>
