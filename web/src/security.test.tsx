// @vitest-environment jsdom
import {describe,it,expect} from 'vitest';
import {render} from '@testing-library/react';
import {SafeMarkdown,safeUrl} from './main';
describe('untrusted markdown',()=>{it('rejects active protocols',()=>{expect(safeUrl('javascript:alert(1)')).toBe('');expect(safeUrl('data:text/html,x')).toBe('');expect(safeUrl('https://example.org')).toBe('https://example.org');});it('does not render raw HTML or remote images',()=>{const {container}=render(<SafeMarkdown body={'<script>alert(1)</script>\n\n![track](https://example.org/x.png)\n\n[bad](javascript:alert(1))'}/>);expect(container.querySelector('script')).toBeNull();expect(container.querySelector('img')).toBeNull();expect(container.querySelector('a')).toBeNull();});});
