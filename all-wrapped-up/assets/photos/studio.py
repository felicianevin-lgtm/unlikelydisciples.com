"""Studio v2: cut-out + relight + directional shadows on a lit backdrop."""
from rembg import remove, new_session
from PIL import Image, ImageOps, ImageFilter, ImageChops, ImageDraw
import numpy as np, pathlib, sys, time
U = pathlib.Path('/root/.claude/uploads/e47ac2d3-6f0e-5f1a-8d8f-dfa7b433f156')
OUT = pathlib.Path('assets/photos'); OUT.mkdir(exist_ok=True)
CUT = pathlib.Path('/tmp/claude-0/cutouts'); CUT.mkdir(exist_ok=True, parents=True)
sess = new_session("isnet-general-use"); sess_u2 = new_session("u2net")
U2NET = {"3f236cb7", "a082a12c", "2ff12bbc", "726a9940"}
SQ = (900, 900); HERO = (1200, 1500); LAND = (1400, 933)
SPECS = {
 'hero-navy-chiffon':   ('182b1b47', HERO, True,  None),
 'about-hannah':        ('3f236cb7', HERO, True,  None),
 'sq-rainbow-box':      ('cce4d41b', SQ, False, None),
 'sq-hannah-check':     ('3f236cb7', SQ, True,  None),
 'sq-christmas-gold':   ('2ff12bbc', SQ, True,  None),
 'sq-western-rose':     ('f953b99b', SQ, True,  None),
 'sq-flamingo':         ('3945b91d', SQ, False, None),
 'sq-dad-shirt':        ('4dc32eeb', SQ, False, None),
 'sq-purple-organza':   ('161109a9', SQ, False, None),
 'sq-vols':             ('39539df9', SQ, False, None),
 'sq-nutcracker':       ('34ebf013', SQ, True,  None),
 'sq-bee-stack':        ('50c52199', SQ, False, None),
 'sq-trees-burlap':     ('caf7879e', SQ, False, None),
 'sq-paisley':          ('3e9d56c3', SQ, True,  None),
 'corp-purple-set':     ('3e409de2', LAND, False, None),
 'sq-special-delivery': ('c3f0febb', SQ, True,  None),
 'sq-pompom-stack':     ('8b7f17b9', SQ, False, None),
 'sq-snowflake-cube':   ('8727f463', SQ, False, None),
 'sq-purple-joy':       ('726a9940', SQ, False, None),
 'land-colorful-trees': ('750f1b45', LAND, False, None),
 'sq-wedding-navy':     ('182b1b47', SQ, True,  (0, .6)),
 'sq-bridal-dots':      ('a082a12c', SQ, True,  None),
 'sq-baby-shower':      ('d59d1308', SQ, False, None),
 'sq-camo-birthday':    ('efd1c6e1', SQ, False, None),
}
ONLY = sys.argv[1:]
def find(uid): return next(U.glob(uid + '*'))

def cutout(uid):
    f = CUT / (uid + '.png')
    if f.exists(): return Image.open(f).convert('RGBA')
    im = ImageOps.exif_transpose(Image.open(find(uid))).convert('RGB'); im.thumbnail((1600, 1600), Image.LANCZOS)
    out = remove(im, session=sess_u2) if uid in U2NET else remove(im, session=sess, alpha_matting=True,
          alpha_matting_foreground_threshold=240, alpha_matting_background_threshold=10, alpha_matting_erode_size=6)
    out.save(f); return out

def best_angle(alpha):
    a = alpha.copy(); a.thumbnail((320, 320)); best = (0, 1e18)
    for i in range(-40, 41):
        ang = i*0.25; r = a.rotate(ang, expand=True, resample=Image.BILINEAR)
        bb = r.point(lambda v: 255 if v > 128 else 0).getbbox()
        if bb:
            area = (bb[2]-bb[0])*(bb[3]-bb[1])
            if area < best[1]: best = (ang, area)
    return best[0]

# ---------- edge & colour work (numpy) ----------
def clean_edges(rgba):
    """Erode alpha 1px, feather, and pull edge colours from the interior to kill halos."""
    a = rgba.split()[3].filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    arr = np.asarray(rgba).astype(np.float32); al = np.asarray(a).astype(np.float32)/255.0
    rgb = arr[..., :3]
    # interior colour spread: premultiplied blur / blurred alpha
    pre = Image.fromarray((rgb*al[..., None]).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
    ab = Image.fromarray((al*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
    pre = np.asarray(pre).astype(np.float32); ab = np.asarray(ab).astype(np.float32)/255.0
    fill = pre/np.maximum(ab[..., None], 1e-3)
    w = np.clip((0.92 - al)/0.92, 0, 1)[..., None]      # blend toward interior colour near the edge
    rgb = rgb*(1-w) + fill*w
    out = np.dstack([np.clip(rgb, 0, 255), al*255]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')

def white_balance(rgb, al, strength=0.75):
    m = al > 0.95
    px = rgb[m]
    if len(px) < 500: return rgb
    lum = px.mean(1); top = px[lum >= np.percentile(lum, 97)]
    ref = top.mean(0); gain = ref.mean()/np.maximum(ref, 1)
    gain = 1 + (gain-1)*strength; gain = np.clip(gain, 0.88, 1.18)
    return np.clip(rgb*gain, 0, 255)

def tone(rgb, al):
    m = al > 0.95; px = rgb[m]
    lo, hi = np.percentile(px, 0.5), np.percentile(px, 99.6)
    rgb = (rgb - lo)*(255/max(hi-lo, 1)); rgb = np.clip(rgb, 0, 255)
    x = rgb/255.0
    x = x + 0.06*np.sin(np.pi*x)*(1-x)           # lift shadows
    x = np.clip(0.5 + (x-0.5)*1.08, 0, 1)         # gentle contrast
    x = 0.5 + 0.5*np.tanh(2.2*(x-0.5))/np.tanh(1.1)  # soft S curve
    # vibrance: boost low-saturation colours a little more than saturated ones
    mx, mn = x.max(2, keepdims=True), x.min(2, keepdims=True); sat = mx-mn
    mean = x.mean(2, keepdims=True); x = mean + (x-mean)*(1 + 0.12*(1-sat))
    return np.clip(x, 0, 1)*255

def key_light(rgb, al):
    """Soft key from upper-left: brighter top-left, gently darker bottom-right, plus a rim of light along the top."""
    h, w = al.shape; yy, xx = np.mgrid[0:h, 0:w]
    g = 1.07 - 0.14*((xx/w)*0.45 + (yy/h)*0.55)
    top = np.exp(-((yy/h)/0.12)**2)*0.05
    return np.clip(rgb*(g+top)[..., None], 0, 255)

def relight(rgba):
    rgba = clean_edges(rgba)
    arr = np.asarray(rgba).astype(np.float32); rgb, al = arr[..., :3], arr[..., 3]/255.0
    rgb = white_balance(rgb, al); rgb = tone(rgb, al); rgb = key_light(rgb, al)
    out = Image.fromarray(np.dstack([rgb, al*255]).astype(np.uint8), 'RGBA')
    r = out.convert('RGB').filter(ImageFilter.UnsharpMask(radius=1.1, percent=48, threshold=2))
    r = r.convert('RGBA'); r.putalpha(out.split()[3]); return r

# ---------- set ----------
def backdrop(w, h):
    base = np.zeros((h, w, 3), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]; u, v = xx/w, yy/h
    wall = np.array([251, 248, 244], np.float32); floor = np.array([238, 230, 222], np.float32)
    hz = 0.64; t = np.clip((v-hz+0.06)/0.12, 0, 1)[..., None]
    base = wall*(1-t) + floor*t
    base *= (1 - 0.07*np.clip(v-hz, 0, 1)/(1-hz))[..., None]           # floor falls off toward bottom
    spot = np.exp(-(((u-0.3)/0.75)**2 + ((v-0.25)/0.7)**2))             # key light pool upper-left
    base *= (0.93 + 0.10*spot)[..., None]
    vig = 1 - 0.06*np.clip(np.sqrt((u-0.5)**2 + (v-0.5)**2)-0.35, 0, 1)/0.35
    base *= vig[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))

def shadows(W, H, a, x, y, sw):
    """cast shadow (offset down-right with light from upper-left, blurred more with distance) + contact shadow."""
    cast = Image.new('L', (W, H), 0)
    # perspective squash: scale silhouette vertically to lie on the floor, skew right
    sh = a.resize((a.width, max(1, int(a.height*0.26))), Image.BILINEAR)
    sk = sh.transform((sh.width + int(sh.height*0.9), sh.height), Image.AFFINE, (1, -0.9, 0, 0, 1, 0), Image.BILINEAR)
    cast.paste(sk, (x + int(sw*0.02), y + a.height - sh.height + int(sw*0.02)))
    cast = cast.filter(ImageFilter.GaussianBlur(sw*0.05)).point(lambda v: int(v*0.22))
    contact = Image.new('L', (W, H), 0)
    ew, eh = int(sw*0.96), int(sw*0.10)
    ell = Image.new('L', (ew, eh), 0); ImageDraw.Draw(ell).ellipse((0, 0, ew-1, eh-1), fill=255)
    contact.paste(ell, (x + (sw-ew)//2, y + a.height - eh//2 - int(sw*0.008)))
    contact = contact.filter(ImageFilter.GaussianBlur(sw*0.018)).point(lambda v: int(v*0.55))
    amb = Image.new('L', (W, H), 0); amb.paste(a, (x, y + int(sw*0.012)))
    amb = amb.filter(ImageFilter.GaussianBlur(sw*0.02)).point(lambda v: int(v*0.18))
    return ImageChops.lighter(ImageChops.lighter(cast, contact), amb)

def compose(name, uid, canvas, straighten, focus):
    sub = cutout(uid)
    if straighten:
        ang = best_angle(sub.split()[3])
        if 0 < abs(ang) <= 10: sub = sub.rotate(ang, expand=True, resample=Image.BICUBIC)
    bb = sub.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox(); sub = sub.crop(bb)
    if focus: h = sub.height; sub = sub.crop((0, int(h*focus[0]), sub.width, int(h*focus[1])))
    sub = relight(sub)
    W, H = canvas; pad = 0.08
    s = min(W*(1-2*pad)/sub.width, H*(1-2*pad)/sub.height)
    sub = sub.resize((max(1, int(sub.width*s)), max(1, int(sub.height*s))), Image.LANCZOS)
    x = (W - sub.width)//2
    y = max(int(H*pad), min(int(H*0.64) + int(H*0.15) - sub.height, H - sub.height - int(H*pad)))
    bg = backdrop(W, H)
    bg.paste(Image.new('RGB', (W, H), (96, 80, 72)), mask=shadows(W, H, sub.split()[3], x, y, sub.width))
    bg.paste(sub, (x, y), sub)
    bg = bg.filter(ImageFilter.UnsharpMask(radius=0.8, percent=20, threshold=3))
    bg.save(OUT/(name+'.jpg'), 'JPEG', quality=86, optimize=True, progressive=True, subsampling=1)
    return sub.size

t = time.time()
for name, spec in SPECS.items():
    if ONLY and name not in ONLY: continue
    print(f"{name:22} {compose(name, *spec)} {time.time()-t:4.0f}s", flush=True)
