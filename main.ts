import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

// Opcode table: byte -> [immediate bytes, pops, pushes]. From ISA.md / vm.mjs.
const O: Record<number, [number, number, number]> = {
  0: [0, 0, 0], 1: [1, 0, 1], 2: [4, 0, 1], 3: [0, 1, 0], 4: [0, 1, 2],
  5: [0, 2, 2], 6: [0, 2, 3], 7: [0, 3, 3],
  16: [0, 2, 1], 17: [0, 2, 1], 18: [0, 2, 1], 19: [0, 2, 1], 20: [0, 2, 1],
  21: [0, 2, 1], 22: [0, 2, 1], 23: [0, 1, 1], 24: [0, 2, 1], 25: [0, 2, 1],
  26: [0, 2, 1], 27: [0, 1, 1], 28: [0, 2, 1], 29: [0, 2, 1], 30: [0, 2, 1],
  32: [0, 2, 1], 33: [0, 2, 1], 34: [0, 2, 1],
  48: [2, 0, 0], 49: [2, 1, 0], 50: [2, 1, 0], 51: [2, 0, 0], 52: [0, 0, 0],
  64: [0, 1, 1], 65: [0, 2, 0], 80: [0, 1, 0], 81: [0, 1, 0], 82: [0, 0, 1], 83: [0, 1, 0],
};

// Binary-op dispatch table, indexed by op - 0x10. Slots for the unary ops
// 0x17 (NEG), 0x1b (NOT) and the invalid 0x1f are never called. A divide or
// modulo by zero returns NaN, which the caller turns into trap code 4.
const B: ((a: number, b: number) => number)[] = [
  (a, b) => (a + b) | 0,
  (a, b) => (a - b) | 0,
  (a, b) => Math.imul(a, b),
  (a, b) => (b ? (a === -2147483648 && b === -1 ? a : (a / b) | 0) : NaN),
  (a, b) => (b ? (b === -1 ? 0 : (a % b) | 0) : NaN),
  (a, b) => (b ? Math.floor((a >>> 0) / (b >>> 0)) | 0 : NaN),
  (a, b) => (b ? ((a >>> 0) % (b >>> 0)) | 0 : NaN),
  (a, b) => 0,
  (a, b) => a & b,
  (a, b) => a | b,
  (a, b) => a ^ b,
  (a, b) => 0,
  (a, b) => a << (b & 31),
  (a, b) => a >> (b & 31),
  (a, b) => (a >>> (b & 31)) | 0,
  (a, b) => 0,
  (a, b) => (a === b ? 1 : 0),
  (a, b) => (a < b ? 1 : 0),
  (a, b) => ((a >>> 0) < (b >>> 0) ? 1 : 0),
];

function run(p: Uint8Array, inp: Uint8Array): { out: number[]; code: number } {
  const D = new Int32Array(256);
  const C = new Int32Array(64);
  const M = new Int32Array(256);
  const out: number[] = [];
  let sp = 0, cp = 0, ip = 0, pc = 0, steps = 0;
  const n = p.length;
  for (;;) {
    if (steps === 1000000) return { out, code: 10 };
    if (pc < 0 || pc >= n) return { out, code: 9 };
    const op = p[pc];
    const t = O[op];
    if (!t) return { out, code: 5 };
    const imm = t[0], pops = t[1], pushes = t[2];
    if (pc + imm >= n) return { out, code: 9 };
    steps++;
    const nx = pc + 1 + imm;
    if (sp < pops) return { out, code: 2 };
    if (sp - pops + pushes > 256) return { out, code: 3 };
    pc = nx;
    if (op >= 0x10 && op <= 0x22 && op !== 0x17 && op !== 0x1b) {
      const r = B[op - 0x10](D[sp - 2], D[sp - 1]);
      if (Number.isNaN(r)) return { out, code: 4 };
      sp -= 2;
      D[sp++] = r;
      continue;
    }
    switch (op) {
      case 0x00: return { out, code: 0 };
      case 0x01: D[sp++] = (p[nx - 1] << 24) >> 24; break;
      case 0x02: D[sp++] = p[nx - 4] | (p[nx - 3] << 8) | (p[nx - 2] << 16) | (p[nx - 1] << 24); break;
      case 0x03: sp--; break;
      case 0x04: D[sp] = D[sp - 1]; sp++; break;
      case 0x05: { const q = D[sp - 1]; D[sp - 1] = D[sp - 2]; D[sp - 2] = q; break; }
      case 0x06: D[sp] = D[sp - 2]; sp++; break;
      case 0x07: { const a = D[sp - 3]; D[sp - 3] = D[sp - 2]; D[sp - 2] = D[sp - 1]; D[sp - 1] = a; break; }
      case 0x17: D[sp - 1] = -D[sp - 1] | 0; break;
      case 0x1b: D[sp - 1] = ~D[sp - 1]; break;
      case 0x30: case 0x31: case 0x32: {
        const rel = ((p[nx - 2] | (p[nx - 1] << 8)) << 16) >> 16;
        let take = op === 0x30;
        if (op !== 0x30) { const v = D[--sp]; take = op === 0x31 ? v === 0 : v !== 0; }
        if (take) pc = nx + rel;
        break;
      }
      case 0x33:
        if (cp === 64) return { out, code: 7 };
        C[cp++] = nx;
        pc = p[nx - 2] | (p[nx - 1] << 8);
        break;
      case 0x34:
        if (cp === 0) return { out, code: 8 };
        pc = C[--cp];
        break;
      case 0x40: {
        const a = D[sp - 1];
        if (a < 0 || a >= 256) return { out, code: 6 };
        D[sp - 1] = M[a];
        break;
      }
      case 0x41: {
        const a = D[sp - 1], v = D[sp - 2];
        if (a < 0 || a >= 256) return { out, code: 6 };
        sp -= 2;
        M[a] = v;
        break;
      }
      case 0x50: {
        const s = String(D[sp - 1]);
        if (out.length + s.length > 65536) return { out, code: 11 };
        sp--;
        for (let i = 0; i < s.length; i++) out.push(s.charCodeAt(i));
        break;
      }
      case 0x51:
        if (out.length + 1 > 65536) return { out, code: 11 };
        out.push(D[--sp] & 255);
        break;
      case 0x52: D[sp++] = ip < inp.length ? inp[ip++] : -1; break;
      case 0x53: return { out, code: D[--sp] & 255 };
      default: return { out, code: 5 };
    }
  }
}

const I = process.env.MAKEFUN_INPUT_DIR ?? '/input';
const W = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
for (const id of readdirSync(I).sort()) {
  const r = run(new Uint8Array(readFileSync(join(I, id, 'program.bin'))), new Uint8Array(readFileSync(join(I, id, 'input.bin'))));
  mkdirSync(join(W, id), { recursive: true });
  writeFileSync(join(W, id, 'stdout.bin'), Uint8Array.from(r.out));
  writeFileSync(join(W, id, 'exit.txt'), `${r.code}\n`);
}
