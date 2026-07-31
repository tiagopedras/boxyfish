/* Turn a photo of a drawing into a fish cut-out.
 *
 * This is the browser version of tools/extract_fish.py, working on one photo
 * instead of a scanned sheet:
 *   1. flatten the lighting, so a shadow across the paper doesn't read as ink
 *   2. find the ink, close small gaps so a detached tail joins its body
 *   3. keep the blob in the middle of the frame, which is what was held up
 *   4. fill the body, keep whatever colour is inside, drop the paper
 *
 * Unlike the scans it does not try to work out which way the fish points --
 * the drawing is assumed to be held up facing right, and the user can flip it
 * afterwards if they held it the other way round.
 */
window.fishify = (function(){

const MAX_SIDE   = 720;    // work at this size; bigger is slower, not better
const BLUR_FRAC  = 0.06;   // lighting blur, as a fraction of the long side
const CLOSE_FRAC = 0.007;  // gap-closing radius, same
const INK_LO     = 0.20;   // below this is paper
const INK_HI     = 0.34;   // above this is definitely ink
const MIN_FRAC   = 0.004;  // ignore blobs smaller than this share of the frame
const PAD        = 8;

function canvasOf(w, h){
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  return c;
}

/* --- 1D max / min filters, run twice for a square structuring element --- */
function morph(mask, w, h, r, dilate){
  const pick = dilate ? (a,b) => a || b : (a,b) => a && b;
  const tmp = new Uint8Array(w*h), out = new Uint8Array(w*h);
  for (let y = 0; y < h; y++){
    const row = y*w;
    for (let x = 0; x < w; x++){
      let v = dilate ? 0 : 1;
      for (let k = -r; k <= r; k++){
        const xx = x + k;
        const s = (xx < 0 || xx >= w) ? (dilate ? 0 : 1) : mask[row + xx];
        v = pick(v, s);
      }
      tmp[row + x] = v;
    }
  }
  for (let x = 0; x < w; x++){
    for (let y = 0; y < h; y++){
      let v = dilate ? 0 : 1;
      for (let k = -r; k <= r; k++){
        const yy = y + k;
        const s = (yy < 0 || yy >= h) ? (dilate ? 0 : 1) : tmp[yy*w + x];
        v = pick(v, s);
      }
      out[y*w + x] = v;
    }
  }
  return out;
}

/* --- everything the border can reach; the rest is enclosed --- */
function reachable(mask, w, h){
  const seen = new Uint8Array(w*h);
  const stack = [];
  const push = i => { if (!seen[i] && !mask[i]){ seen[i] = 1; stack.push(i); } };
  for (let x = 0; x < w; x++){ push(x); push((h-1)*w + x); }
  for (let y = 0; y < h; y++){ push(y*w); push(y*w + w-1); }
  while (stack.length){
    const i = stack.pop(), x = i % w, y = (i - x)/w;
    if (x > 0)   push(i-1);
    if (x < w-1) push(i+1);
    if (y > 0)   push(i-w);
    if (y < h-1) push(i+w);
  }
  return seen;
}

/* --- label blobs, return the biggest one overlapping the middle --- */
function centreBlob(mask, w, h){
  const lbl = new Int32Array(w*h).fill(-1);
  const cx0 = w*0.2, cx1 = w*0.8, cy0 = h*0.2, cy1 = h*0.8;
  let best = null, id = 0;
  const stack = [];
  for (let s = 0; s < w*h; s++){
    if (!mask[s] || lbl[s] >= 0) continue;
    id++; lbl[s] = id; stack.push(s);
    let area = 0, central = false;
    while (stack.length){
      const i = stack.pop(), x = i % w, y = (i - x)/w;
      area++;
      if (x > cx0 && x < cx1 && y > cy0 && y < cy1) central = true;
      const nb = [];
      if (x > 0)   nb.push(i-1);
      if (x < w-1) nb.push(i+1);
      if (y > 0)   nb.push(i-w);
      if (y < h-1) nb.push(i+w);
      for (const j of nb) if (mask[j] && lbl[j] < 0){ lbl[j] = id; stack.push(j); }
    }
    // a blob out at the edge is a hand or a table edge, not the drawing
    const score = area * (central ? 1 : 0.05);
    if (!best || score > best.score) best = { id, score, area };
  }
  if (!best || best.area < w*h*MIN_FRAC) return null;
  const out = new Uint8Array(w*h);
  for (let i = 0; i < w*h; i++) out[i] = lbl[i] === best.id ? 1 : 0;
  return out;
}

/* How brightly lit the paper is at each point.
 *
 * Taken from a heavily shrunk copy and biased towards the brightest cells
 * nearby, because paper is the brightest thing in the picture. A plain blur
 * would be dragged down by the drawing itself, and a big block of colour
 * would end up dividing itself out to white.
 */
function lightField(sharp, w, h){
  const SW = 40, SH = Math.max(6, Math.round(40 * h / w));
  const small = canvasOf(SW, SH);
  const sc = small.getContext('2d');
  sc.drawImage(sharp, 0, 0, SW, SH);
  const d = sc.getImageData(0, 0, SW, SH).data;

  const lum = new Float32Array(SW*SH);
  for (let i = 0; i < SW*SH; i++)
    lum[i] = 0.299*d[i*4] + 0.587*d[i*4+1] + 0.114*d[i*4+2];

  const R = 3, mx = new Float32Array(SW*SH);
  for (let y = 0; y < SH; y++) for (let x = 0; x < SW; x++){
    let m = 0;
    for (let j = -R; j <= R; j++) for (let i = -R; i <= R; i++){
      const yy = Math.min(SH-1, Math.max(0, y+j));
      const xx = Math.min(SW-1, Math.max(0, x+i));
      m = Math.max(m, lum[yy*SW + xx]);
    }
    mx[y*SW + x] = m;
  }

  const up = canvasOf(SW, SH);
  const uc = up.getContext('2d');
  const uid = uc.createImageData(SW, SH);
  for (let i = 0; i < SW*SH; i++){
    const v = Math.round(mx[i]);
    uid.data[i*4] = uid.data[i*4+1] = uid.data[i*4+2] = v;
    uid.data[i*4+3] = 255;
  }
  uc.putImageData(uid, 0, 0);

  const big = canvasOf(w, h);
  const bc = big.getContext('2d');
  bc.imageSmoothingEnabled = true;
  bc.imageSmoothingQuality = 'high';
  bc.filter = `blur(${Math.max(2, Math.round(Math.max(w,h) * BLUR_FRAC * 0.35))}px)`;
  bc.drawImage(up, 0, 0, w, h);
  return bc.getImageData(0, 0, w, h).data;
}

function smoothstep(e0, e1, x){
  const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0)));
  return t * t * (3 - 2 * t);
}

/**
 * @param {HTMLCanvasElement|HTMLVideoElement} source  the framed photo
 * @returns {{canvas: HTMLCanvasElement}|null}  null if no drawing was found
 */
function fishify(source){
  const sw = source.videoWidth || source.width;
  const sh = source.videoHeight || source.height;
  const scale = Math.min(1, MAX_SIDE / Math.max(sw, sh));
  const w = Math.max(1, Math.round(sw * scale));
  const h = Math.max(1, Math.round(sh * scale));

  const sharp = canvasOf(w, h);
  sharp.getContext('2d').drawImage(source, 0, 0, w, h);

  const A = sharp.getContext('2d').getImageData(0,0,w,h).data;
  const L = lightField(sharp, w, h);

  // inkness: how much darker than the lit paper each pixel is.
  // Dividing every channel by the same number cancels the lighting while
  // leaving hue and saturation alone, so coloured-in areas stay coloured.
  const ink = new Float32Array(w*h);
  const bal = new Float32Array(w*h*3);
  for (let i = 0, p = 0; i < w*h; i++, p += 4){
    const lumA = 0.299*A[p] + 0.587*A[p+1] + 0.114*A[p+2];
    const lit = Math.max(1, L[p]);
    ink[i] = Math.min(1, Math.max(0, 1 - lumA/lit));
    for (let c = 0; c < 3; c++) bal[i*3+c] = Math.min(1, A[p+c] / lit);
  }

  const hard = new Uint8Array(w*h);
  for (let i = 0; i < w*h; i++) hard[i] = ink[i] > INK_HI ? 1 : 0;

  // close gaps, then anything the border can't reach is inside the fish
  const r = Math.max(2, Math.round(Math.max(w,h) * CLOSE_FRAC));
  const closed = morph(morph(hard, w, h, r, true), w, h, r, false);
  const outside = reachable(closed, w, h);
  const solid = new Uint8Array(w*h);
  for (let i = 0; i < w*h; i++) solid[i] = (closed[i] || !outside[i]) ? 1 : 0;

  const body = centreBlob(solid, w, h);
  if (!body) return null;

  // bounding box of the fish
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++){
    if (!body[y*w+x]) continue;
    if (x < x0) x0 = x; if (x > x1) x1 = x;
    if (y < y0) y0 = y; if (y > y1) y1 = y;
  }
  if (x1 < x0) return null;

  // one pixel of soft edge, so the outline isn't stair-stepped
  const near = morph(body, w, h, 1, true);

  const ow = (x1-x0+1) + PAD*2, oh = (y1-y0+1) + PAD*2;
  const out = canvasOf(ow, oh);
  const img = out.getContext('2d').createImageData(ow, oh);
  const D = img.data;
  for (let y = 0; y < oh; y++){
    for (let x = 0; x < ow; x++){
      const sx = x0 + x - PAD, sy = y0 + y - PAD, o = (y*ow + x)*4;
      if (sx < 0 || sy < 0 || sx >= w || sy >= h){ D[o+3] = 0; continue; }
      const i = sy*w + sx;
      // solid inside the outline, feathered by one pixel just outside it, and
      // nothing further out -- so shadows and paper texture leave no halo
      const a = body[i] ? 1 : (near[i] ? smoothstep(INK_LO, INK_HI, ink[i]) : 0);
      if (a <= 0.002){ D[o+3] = 0; continue; }
      D[o]   = Math.round(bal[i*3]   * 255);
      D[o+1] = Math.round(bal[i*3+1] * 255);
      D[o+2] = Math.round(bal[i*3+2] * 255);
      D[o+3] = Math.round(a * 255);
    }
  }
  out.getContext('2d').putImageData(img, 0, 0);
  return { canvas: out };
}

return fishify;
})();
