<script lang="ts">
	let { onDismiss }: { onDismiss: () => void } = $props();

	let visible = $state(true);
	let fadeOut = $state(false);
	const reducedMotion =
		typeof window !== 'undefined'
			? window.matchMedia('(prefers-reduced-motion: reduce)').matches
			: false;

	// Fade timing — fast in/out so the map reveals quickly.
	const FADE_OUT_MS = 400; // whole overlay (photo + text) fades out together
	const HOLD_MS = 2600; // reading time before auto-dismiss begins

	function dismiss() {
		if (fadeOut) return; // already dismissing
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

	// Auto-dismiss after the hold window.
	setTimeout(dismiss, HOLD_MS);
</script>

{#if visible}
	<!--
		The ENTIRE overlay (background photo + gradient + content) fades in and out
		as one layer via `.splash-root`, so the map underneath is revealed in a
		smooth crossfade instead of the photo cutting away abruptly.
	-->
	<div
		class="splash-root fixed inset-0 z-50 flex items-end justify-center pb-24 sm:pb-32 {reducedMotion
			? ''
			: fadeOut
				? 'splash-out'
				: 'splash-in'}"
		onclick={dismiss}
		onkeydown={(e) => e.key === 'Escape' && dismiss()}
		role="button"
		tabindex="0"
	>
		<!-- Background image — USGS Tracy Arm aerial -->
		<div
			class="absolute inset-0 bg-cover bg-center"
			style="background-image: url('/splash-tracy-arm.jpg'); background-color: #1c1917;"
		>
			<!-- Dark gradient overlay -->
			<div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent"></div>
		</div>

		<!-- Content -->
		<div class="relative z-10 text-center px-6 max-w-2xl">
			<h1 class="text-5xl sm:text-6xl font-serif font-extrabold text-white mb-6 tracking-wide">
				SCARP
			</h1>
			<p class="text-base sm:text-lg text-white/90 font-serif italic leading-relaxed mb-2">
				In 1958, Lituya Bay saw the highest wave ever recorded — 524 meters.
			</p>
			<p class="text-base sm:text-lg text-white/90 font-serif italic leading-relaxed mb-2">
				In August 2025, Tracy Arm came within 50 meters of that record.
			</p>
			<p class="text-lg sm:text-xl font-bold text-amber-500 mb-6">Nobody saw it coming.</p>
			<p class="text-xs text-white/40 uppercase tracking-widest">tap anywhere to continue</p>
		</div>

		<!-- Photo credit -->
		<div class="absolute bottom-3 left-4 text-[10px] text-white/30 z-10">
			Photo: USGS, Public Domain
		</div>
	</div>
{/if}

<style>
	/* Whole-overlay crossfade. The photo and text fade together so the map
	   beneath is revealed smoothly. Fast timings for a snappy reveal. */
	.splash-root {
		will-change: opacity;
	}

	.splash-in {
		animation: splashIn 0.35s ease-out both;
	}

	.splash-out {
		animation: splashOut 0.4s ease-in both;
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
</style>
