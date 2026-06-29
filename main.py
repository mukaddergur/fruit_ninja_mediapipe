import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import random
import os
import math
import numpy as np
from collections import deque

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, 'assets')
FRUIT_SIZE = 82
STREAK_FOR_BOMB = 25
MAX_FRUITS = 6
FALL_SPEED_MIN = 11
FALL_SPEED_MAX = 16

hand_detector = vision.HandLandmarker.create_from_options(
    vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=os.path.join(SCRIPT_DIR, 'hand_landmarker.task')),
        num_hands=1,
    )
)

JUICE_COLORS = {
    'cherry.png': (45, 35, 200),
    'grape.png': (175, 55, 145),
    'lemon.png': (45, 225, 245),
    'orange.png': (30, 135, 250),
    'pineapple.png': (55, 205, 250),
    'watermelon.png': (65, 55, 215),
}


def load_best_score():
    path = os.path.join(SCRIPT_DIR, 'best_score.txt')
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0


def save_best_score(value):
    with open(os.path.join(SCRIPT_DIR, 'best_score.txt'), 'w') as f:
        f.write(str(value))


def load_fruit_images():
    skip = {'bomb.png'}
    images = {}
    for filename in sorted(os.listdir(ASSETS_DIR)):
        if not filename.lower().endswith('.png') or filename in skip:
            continue
        img = cv2.imread(os.path.join(ASSETS_DIR, filename), cv2.IMREAD_UNCHANGED)
        if img is not None and img.shape[2] >= 4:
            images[filename] = cv2.resize(img, (FRUIT_SIZE, FRUIT_SIZE))
    return images


def create_wood_background(w, h):
    rng = random.Random(7)
    bg = np.zeros((h, w, 3), dtype=np.uint8)
    plank_w = max(40, w // 8)
    shades = [(32, 52, 78), (38, 58, 84), (28, 46, 70), (35, 54, 80), (30, 48, 74)]
    for i in range(w // plank_w + 2):
        x0 = i * plank_w
        x1 = min((i + 1) * plank_w, w)
        bg[:, x0:x1] = shades[i % len(shades)]
        if x1 < w:
            cv2.line(bg, (x1, 0), (x1, h), (18, 28, 44), 2)
    for _ in range(80):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        cv2.line(bg, (x, y), (x + rng.randint(-12, 12), y + rng.randint(40, 110)), (22, 36, 54), 1, cv2.LINE_AA)
    for _ in range(45):
        x1, y1 = rng.randint(0, w), rng.randint(0, h)
        x2 = x1 + rng.randint(-100, 100)
        y2 = y1 + rng.randint(-50, 50)
        cv2.line(bg, (x1, y1), (x2, y2), (50, 72, 98), rng.randint(1, 2), cv2.LINE_AA)
    return bg


def overlay_png(bg, overlay, x, y):
    h, w = overlay.shape[:2]
    fh, fw = bg.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(fw, x + w), min(fh, y + h)
    if x2 <= x1 or y2 <= y1:
        return bg
    ox1, oy1 = x1 - x, y1 - y
    crop = overlay[oy1:oy1 + (y2 - y1), ox1:ox1 + (x2 - x1)]
    region = bg[y1:y2, x1:x2]
    alpha = crop[:, :, 3:4] / 255.0
    bg[y1:y2, x1:x2] = (alpha * crop[:, :, :3] + (1 - alpha) * region).astype(bg.dtype)
    return bg


def point_seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def slash_hits_fruit(x1, y1, x2, y2, fx, fy):
    cx, cy = fx + FRUIT_SIZE // 2, fy + FRUIT_SIZE // 2
    return point_seg_dist(cx, cy, x1, y1, x2, y2) < FRUIT_SIZE * 0.45 + 10


def spawn_falling_fruit(fw, fruit_images):
    name = random.choice(list(fruit_images.keys()))
    return {
        'name': name,
        'img': fruit_images[name],
        'x': random.randint(30, max(60, fw - FRUIT_SIZE - 30)),
        'y': -FRUIT_SIZE - random.randint(0, 80),
        'speed': random.uniform(FALL_SPEED_MIN, FALL_SPEED_MAX),
    }


def spawn_juice(x, y, color):
    for _ in range(22):
        a = random.uniform(0, math.pi * 2)
        sp = random.uniform(3, 12)
        particles.append({
            'x': x, 'y': y, 'r': random.uniform(2, 7),
            'vx': math.cos(a) * sp, 'vy': math.sin(a) * sp,
            'life': random.randint(14, 22), 'max': 22, 'color': color,
        })
    for a in range(0, 360, 28):
        rad = math.radians(a + random.uniform(-10, 10))
        splatters.append({
            'x': x, 'y': y, 'r': random.randint(8, 20),
            'angle': random.randint(0, 180), 'color': color,
            'life': 40, 'max': 40,
        })


def spawn_explosion(x, y):
    for _ in range(50):
        a = random.uniform(0, math.pi * 2)
        sp = random.uniform(4, 18)
        particles.append({
            'x': x, 'y': y, 'r': random.uniform(4, 12),
            'vx': math.cos(a) * sp, 'vy': math.sin(a) * sp,
            'life': random.randint(20, 35), 'max': 35,
            'color': (30, 30, 30) if random.random() > 0.4 else (40, 40, 220),
        })


def make_slices(img, x, y, sdx, sdy):
    h, w = img.shape[:2]
    if abs(sdx) >= abs(sdy):
        return [
            {'img': img[:, :w // 2], 'x': x, 'y': y, 'vx': random.uniform(-7, -2), 'vy': random.uniform(-8, -2), 'life': 22},
            {'img': img[:, w // 2:], 'x': x + w // 2, 'y': y, 'vx': random.uniform(2, 7), 'vy': random.uniform(-8, -2), 'life': 22},
        ]
    return [
        {'img': img[:h // 2, :], 'x': x, 'y': y, 'vx': random.uniform(-4, 4), 'vy': random.uniform(-10, -4), 'life': 22},
        {'img': img[h // 2:, :], 'x': x, 'y': y + h // 2, 'vx': random.uniform(-4, 4), 'vy': random.uniform(-2, 3), 'life': 22},
    ]


def draw_bomb(frame, x, y, tick):
    cx, cy = int(x + FRUIT_SIZE // 2), int(y + FRUIT_SIZE // 2)
    r = FRUIT_SIZE // 2 - 4
    cv2.circle(frame, (cx, cy), r, (20, 20, 20), -1, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), r, (40, 40, 230), 3, cv2.LINE_AA)
    fx = cx + int(8 * math.sin(tick * 0.3))
    cv2.line(frame, (cx, cy - r), (fx, cy - r - 14), (60, 60, 60), 3, cv2.LINE_AA)
    if tick % 6 < 3:
        cv2.circle(frame, (fx, cy - r - 16), 4, (50, 200, 255), -1, cv2.LINE_AA)


def draw_shooting_star_blade(frame, trail):
    if len(trail) < 2:
        return
    pts = [(float(p[0]), float(p[1])) for p in trail]
    n = len(pts)
    for i in range(1, n):
        t = i / (n - 1)
        thickness = max(1, int(3 + 5 * t))
        glow = (int(180 + 75 * t), int(200 + 55 * t), 255)
        core = (255, 255, 255)
        cv2.line(frame, (int(pts[i - 1][0]), int(pts[i - 1][1])),
                 (int(pts[i][0]), int(pts[i][1])), glow, thickness + 3, cv2.LINE_AA)
        cv2.line(frame, (int(pts[i - 1][0]), int(pts[i - 1][1])),
                 (int(pts[i][0]), int(pts[i][1])), core, thickness, cv2.LINE_AA)
    tip = (int(pts[-1][0]), int(pts[-1][1]))
    cv2.circle(frame, tip, 4, (255, 255, 255), -1, cv2.LINE_AA)


def draw_splatter(frame, s):
    t = s['life'] / s['max']
    x, y, r = int(s['x']), int(s['y']), max(2, int(s['r'] * t))
    ov = frame.copy()
    cv2.ellipse(ov, (x, y), (r, max(2, r // 2)), s['angle'], 0, 360, s['color'], -1, cv2.LINE_AA)
    cv2.addWeighted(ov, 0.4 * t, frame, 1 - 0.4 * t, 0, frame)


def draw_particle(frame, p):
    t = p['life'] / p['max']
    x, y, r = int(p['x']), int(p['y']), max(1, int(p['r'] * t))
    ov = frame.copy()
    cv2.circle(ov, (x, y), r + 1, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(ov, (x, y), r, p['color'], -1, cv2.LINE_AA)
    cv2.addWeighted(ov, t * 0.9, frame, 1 - t * 0.9, 0, frame)


def chunky_text(frame, text, x, y, scale, color, thick=2):
    for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
        cv2.putText(frame, text, (x + ox, y + oy), cv2.FONT_HERSHEY_DUPLEX, scale, (20, 20, 20), thick + 3, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, scale, color, thick, cv2.LINE_AA)


def draw_hud(frame, score, best, cut_toward_bomb, last_fruit_name):
    last_img = fruit_images.get(last_fruit_name)
    if last_img is not None:
        icon = cv2.resize(last_img, (40, 40))
        frame = overlay_png(frame, icon, 10, 8)
    chunky_text(frame, str(score), 54, 46, 1.5, (40, 210, 255))
    cv2.putText(frame, f'BEST: {best}', (54, 68), cv2.FONT_HERSHEY_DUPLEX, 0.5, (30, 30, 30), 3, cv2.LINE_AA)
    cv2.putText(frame, f'BEST: {best}', (54, 68), cv2.FONT_HERSHEY_DUPLEX, 0.5, (50, 140, 255), 1, cv2.LINE_AA)
    bar_w = int(120 * cut_toward_bomb / STREAK_FOR_BOMB)
    cv2.rectangle(frame, (10, 78), (130, 90), (40, 40, 40), -1)
    cv2.rectangle(frame, (10, 78), (10 + bar_w, 90), (40, 180, 255), -1)
    cv2.putText(frame, f'Bomba: {cut_toward_bomb}/{STREAK_FOR_BOMB}', (10, 106),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1, cv2.LINE_AA)


# --- Oyun ---
fruit_images = load_fruit_images()
if not fruit_images:
    raise FileNotFoundError('assets/ klasorune PNG meyve koy')

score = 0
best_score = load_best_score()
cut_toward_bomb = 0
last_cut_fruit = next(iter(fruit_images))
tick = 0
wood_bg = None
wood_size = None
active_fruits = []
slices = []
particles = []
splatters = []
slash_trail = deque(maxlen=8)
prev_finger = None
explosion_timer = 0

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cv2.namedWindow('Fruit Ninja', cv2.WINDOW_NORMAL)

while True:
    ok, camera = cap.read()
    if not ok:
        break
    tick += 1
    camera = cv2.flip(camera, 1)
    fh, fw = camera.shape[:2]

    if wood_size != (fw, fh):
        wood_bg = create_wood_background(fw, fh)
        wood_size = (fw, fh)

    frame = wood_bg.copy()
    rgb = cv2.cvtColor(camera, cv2.COLOR_BGR2RGB)
    result = hand_detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    cx, cy = -1, -1
    slash_on = False
    if result.hand_landmarks:
        tip = result.hand_landmarks[0][8]
        cx = int(tip.x * fw)
        cy = int(tip.y * fh)
        slash_trail.append((cx, cy))
        if prev_finger:
            slash_on = math.hypot(cx - prev_finger[0], cy - prev_finger[1]) > 6
        prev_finger = (cx, cy)
    else:
        prev_finger = None
        slash_trail.clear()

    for s in splatters[:]:
        draw_splatter(frame, s)
        s['life'] -= 1
        if s['life'] <= 0:
            splatters.remove(s)

    if len(active_fruits) < MAX_FRUITS and random.random() < 0.12:
        active_fruits.append(spawn_falling_fruit(fw, fruit_images))

    sx1 = sy1 = sx2 = sy2 = None
    if slash_on and len(slash_trail) >= 2:
        sx1, sy1 = slash_trail[-2]
        sx2, sy2 = slash_trail[-1]

    for i in range(len(active_fruits) - 1, -1, -1):
        f = active_fruits[i]
        f['y'] += f['speed']
        frame = overlay_png(frame, f['img'], int(f['x']), int(f['y']))

        hit = False
        if slash_on and sx1 is not None:
            hit = slash_hits_fruit(sx1, sy1, sx2, sy2, f['x'], f['y'])
        elif cx >= 0:
            hit = (f['x'] - 10 < cx < f['x'] + FRUIT_SIZE + 10 and
                   f['y'] - 10 < cy < f['y'] + FRUIT_SIZE + 10)

        if hit:
            score += 1
            cut_toward_bomb += 1
            last_cut_fruit = f['name']
            best_score = max(best_score, score)
            fx = int(f['x'] + FRUIT_SIZE // 2)
            fy = int(f['y'] + FRUIT_SIZE // 2)
            sdx = (sx2 - sx1) if sx1 is not None else 1
            sdy = (sy2 - sy1) if sy1 is not None else 0
            slices.extend(make_slices(f['img'], int(f['x']), int(f['y']), sdx, sdy))
            spawn_juice(fx, fy, JUICE_COLORS.get(f['name'], (50, 200, 255)))
            if cut_toward_bomb >= STREAK_FOR_BOMB:
                spawn_explosion(fw // 2, fh // 2)
                explosion_timer = 30
                cut_toward_bomb = 0
            active_fruits.pop(i)
            continue

        if f['y'] > fh + 20:
            active_fruits.pop(i)

    for sl in slices[:]:
        frame = overlay_png(frame, sl['img'], int(sl['x']), int(sl['y']))
        sl['x'] += sl['vx']
        sl['y'] += sl['vy']
        sl['vy'] += 0.35
        sl['life'] -= 1
        if sl['life'] <= 0:
            slices.remove(sl)

    for p in particles[:]:
        draw_particle(frame, p)
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += 0.3
        p['life'] -= 1
        if p['life'] <= 0:
            particles.remove(p)

    draw_shooting_star_blade(frame, slash_trail)
    draw_hud(frame, score, best_score, cut_toward_bomb, last_cut_fruit)

    if explosion_timer > 0:
        chunky_text(frame, 'BOOM!', fw // 2 - 55, fh // 2 - 10, 1.4, (40, 40, 240))
        explosion_timer -= 1

    cv2.imshow('Fruit Ninja', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        save_best_score(best_score)
        break

cap.release()
cv2.destroyAllWindows()
hand_detector.close()
