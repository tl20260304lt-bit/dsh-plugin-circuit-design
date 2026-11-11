export const name = 'dsh-plugin-circuit-design';
export const version = '0.1.0';

export function activate(ctx) {
	// Register circuit-design skill
	ctx.skills.register({
		id: 'circuit-design',
		name: 'circuit-design',
		description: 'Hardware design workflow for schematic capture, PCB layout, BOM management, and DRC/ERC verification.',
		assetsDir: ctx.assets.subdir('skills/circuit-design')
	});
}