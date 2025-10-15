import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	preview: {
		allowedHosts: [
			'mini-competition-production.up.railway.app',
			'.railway.app'
		]
	}
});
