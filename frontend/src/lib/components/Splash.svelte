<script lang="ts">
	let { onDismiss }: { onDismiss: () => void } = $props();

	let visible = $state(true);
	let fadeOut = $state(false);
	const reducedMotion = typeof window !== 'undefined' ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false;

	function dismiss() {
		if (reducedMotion) {
			visible = false;
			onDismiss();
		} else {
			fadeOut = true;
			setTimeout(() => {
				visible = false;
				onDismiss();
			}, 1000);
		}
	}

	// Auto-dismiss after 3s
	setTimeout(dismiss, 3000);
</script>

{#if visible}
	<div
		class="fixed inset-0 z-50 flex items-end justify-center pb-24 sm:pb-32"
		onclick={dismiss}
		onkeydown={(e) => e.key === 'Escape' && dismiss()}
		role="button"
		tabindex="0"
	>
		<!-- Background image placeholder — uses USGS Tracy Arm aerial if available -->
		<div
			class="absolute inset-0 bg-cover bg-center"
			style="background-image: url('/splash-tracy-arm.jpg'); background-color: #1c1917;"
		>
			<!-- Dark gradient overlay -->
			<div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent"></div>
		</div>

		<!-- Content -->
		<div
			class="relative z-10 text-center px-6 max-w-2xl transition-all duration-1000 {fadeOut
				? 'opacity-0 translate-y-4'
				: reducedMotion
					? 'opacity-100'
					: 'animate-fade-in'}"
		>
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
	:global(.animate-fade-in) {
		animation: fadeIn 0.5s ease-out;
	}
	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
