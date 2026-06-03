<script lang="ts">
	/**
	 * Loading-driven splash overlay.
	 * Shows while data is being fetched, fades out when dataReady becomes true.
	 * No timer — purely driven by the loading state of the app.
	 */
	let { dataReady, onDismiss }: { dataReady: boolean; onDismiss: () => void } = $props();

	let fadeOut = $state(false);
	let visible = $state(true);
	const reducedMotion =
		typeof window !== 'undefined'
			? window.matchMedia('(prefers-reduced-motion: reduce)').matches
			: false;

	const FADE_OUT_MS = 500;

	// When dataReady flips to true, begin fade-out.
	$effect(() => {
		if (dataReady) {
			if (reducedMotion) {
				visible = false;
				onDismiss();
			} else {
				fadeOut = true;
				setTimeout(() => {
					visible = false;
					onDismiss();
				}, FADE_OUT_MS);
			}
		}
	});
</script>

{#if visible}
	<div
		class="splash-root fixed inset-0 z-50 flex items-center justify-center {reducedMotion
			? ''
			: fadeOut
				? 'splash-out'
				: 'splash-in'}"
	>
		<!-- Dark solid background -->
		<div class="absolute inset-0 bg-stone-900"></div>

		<!-- Content: centered, elegant -->
		<div class="relative z-10 text-center px-8 max-w-xl">
			<h1 class="text-5xl sm:text-6xl font-serif font-extrabold text-white mb-8 tracking-wide">
				SCARP
			</h1>
			<p class="text-sm sm:text-base text-white/80 font-serif leading-relaxed mb-2">
				Ranked monitoring-priority map for tsunamigenic landslides in Southeast Alaska.
			</p>
			<p class="text-sm sm:text-base text-white/80 font-serif leading-relaxed mb-8">
				Identifying where a single sensor would save the most lives — using only public data.
			</p>

			<!-- Loading indicator -->
			<div class="flex items-center justify-center gap-2 text-amber-500">
				<div class="loading-dot animate-pulse">●</div>
				<span class="text-sm font-medium uppercase tracking-widest">Loading</span>
				<div class="loading-dot animate-pulse" style="animation-delay: 0.2s">●</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.splash-root {
		will-change: opacity;
	}

	.splash-in {
		animation: splashIn 0.6s ease-out both;
	}

	.splash-out {
		animation: splashOut 0.5s ease-in both;
		pointer-events: none;
	}

	@keyframes splashIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes splashOut {
		from {
			opacity: 1;
		}
		to {
			opacity: 0;
		}
	}

	.loading-dot {
		animation: pulse 1.5s ease-in-out infinite;
	}
</style>
