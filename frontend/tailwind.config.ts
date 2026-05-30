import type { Config } from 'tailwindcss';

const config: Config = {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				paper: '#faf7f2',
				ink: '#1c1917',
				navy: '#0f172a'
			},
			fontFamily: {
				serif: ['Fraunces', 'Georgia', 'serif'],
				sans: ['Inter', 'system-ui', 'sans-serif']
			}
		}
	},
	plugins: [require('@tailwindcss/typography')]
};

export default config;
