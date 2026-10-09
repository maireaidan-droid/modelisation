// Animation procédurale du Dragon Long (même logique que roblox/DragonAnimator.client.lua).
// Chaque os reçoit une rotation par rapport à sa pose de repos, recalculée à chaque image.
//
// Le corps est piloté comme un serpent : on décrit la FORME voulue de tout le corps (une vague qui glisse
// de la tête vers la queue, de même amplitude partout), puis on en déduit l'angle de chaque os
// (= différence d'orientation avec l'os parent). Le corps est ensuite recentré pour que la tête, le milieu
// et la queue ondulent tous ensemble, au lieu de rester accrochés au poitrail.
(function (global) {
  const BLINK_UP = 1.449;          // fermeture de la paupière du haut (rad, elle glisse vers le bas sur l'œil)
  const BLINK_LOW = 0.349;         // la paupière du bas remonte à sa rencontre
  const EYE = { L: 0.78, D: 0.247 };  // demi-longueur et profondeur de l'œil (studs)
  // Course de la pupille sur l'œil (studs) : moins vers l'avant, où l'œil s'enfonce sous l'arcade près du nez.
  const GAZE_FWD = 0.15, GAZE_BACK = 0.34, GAZE_Y = 0.07;
  const PUPIL_FWD = { L: -1, R: 1 };  // sens « vers l'avant » de l'axe X de chaque pupille
  const SEG = 0.8;                 // longueur du corps par pas de colonne (studs)
  const KAPPA = 0.11;              // nombre d'onde : ~1,3 vague sur toute la longueur du corps

  // up / side : amplitude de la vague verticale / latérale (rad) ; speed : vitesse de la vague (rad/s) ;
  // helix : décalage entre les deux (pi/2 = chaque anneau décrit un cercle, le corps s'enroule en spirale) ;
  // center : recentrage du corps (1 = tout le corps ondule autour de son milieu, 0 = ancré au poitrail).
  const MODES = {
    Idle: { up: 0.03, side: 0.06, speed: 1.2, helix: 0, center: 0, tuck: 0, walk: 0, mane: 0.12, maneSpeed: 1.6,
            jaw: 0.04, bob: 0.15, bank: 0, head: 0.6 },
    Walk: { up: 0.02, side: 0.13, speed: 3.4, helix: 0, center: 0, tuck: 0, walk: 1, mane: 0.2, maneSpeed: 3.2,
            jaw: 0.07, bob: 0.2, bank: 0, head: 0.5 },
    // Vol : longue vague souple et continue de la tête à la queue, un peu en spirale ; le dragon « nage » dans
    // l'air. Léger roulis, crinière soulevée, pattes repliées qui suivent la vague.
    Fly:  { up: 0.34, side: 0.16, speed: 2.0, helix: 1.57, center: 1, tuck: 1, walk: 0, mane: 0.42, maneSpeed: 5,
            jaw: 0.12, bob: 0.8, bank: 0.1, head: 0.45 }
  };

  // Colonne, de la tête à la queue : [os, position le long du corps (pas de colonne), parent].
  const SPINE = [["Head", 0, "Neck"], ["Neck", 5, "Neck2"], ["Neck2", 10, "Root"], ["Root", 14, null]];
  for (let k = 1; k <= 14; k++) {
    SPINE.push(["S" + String(k).padStart(2, "0"), 14 + 4 * k, k === 1 ? "Root" : "S" + String(k - 1).padStart(2, "0")]);
  }
  // Ordre parent → enfant (pour cumuler les positions depuis le poitrail).
  const ORDER = ["Root", "Neck2", "Neck", "Head"].concat(SPINE.slice(4).map(function (b) { return b[0]; }))
    .map(function (n) { return SPINE.find(function (b) { return b[0] === n; }); });
  const LEGS = { LegFL: [0, 14], LegBR: [0, 42], LegFR: [Math.PI, 14], LegBL: [Math.PI, 42] };

  // Fermeture des paupières (0 = ouvert, 1 = fermé) à l'instant tt d'un clignement b.
  function closeOnce(b, tt) {
    if (tt <= 0) return 0;
    if (tt < b.close) { const x = tt / b.close; return x * x; }                 // accélère en fermant
    if (tt < b.close + b.hold) return 1;
    const y = (tt - b.close - b.hold) / b.open;
    if (y >= 1) return 0;
    const c1 = 1.2, c3 = c1 + 1, z = y - 1;                                     // réouverture avec léger rebond
    return 1 - (1 + c3 * z * z * z + c1 * z * z);
  }
  function closure(b, tt, one) {
    return b.twice && tt > one + 0.08 ? closeOnce(b, tt - one - 0.08) : closeOnce(b, tt);
  }

  function create(bones, setBone) {
    // setBone(name, rx, ry, rz, ty, tz, tx) : rotation (X puis Y puis Z, comme CFrame.Angles) + décalage
    // le long des axes de l'os
    const st = { p: Object.assign({}, MODES.Idle), phase: 0, step: 0, flutter: 0, t: 0,
      blinkIn: 2, blink: null, headLook: 0, headTarget: 0,
      gazeX: 0, gazeY: 0, gazeTx: 0, gazeTy: 0, gazeIn: 1, microX: 0, microY: 0, microIn: 0.5 };
    function rnd(a, b) { return a + Math.random() * (b - a); }

    // Forme du corps : angle de la colonne (haut/bas, côté) à la position s.
    function bodyAngles(p, s) {
      const env = 0.8 + 0.3 * s / 70;
      const a = KAPPA * s - st.phase;
      return [p.up * env * Math.sin(a), p.side * env * Math.sin(a + p.helix)];
    }

    function update(dt, mode) {
      st.t += dt;
      const target = MODES[mode] || MODES.Idle;
      const k = Math.min(1, dt * 1.8);
      for (const key in target) st.p[key] += (target[key] - st.p[key]) * k;
      const p = st.p;
      st.phase += dt * p.speed;
      st.step += dt * 4.2 * p.walk;
      st.flutter += dt * p.maneSpeed;

      // 1. Orientation voulue de chaque morceau de colonne.
      const abs = {};
      SPINE.forEach(function (b) { abs[b[0]] = bodyAngles(p, b[1]); });
      abs.Head = [abs.Head[0] * p.head, abs.Head[1] * p.head];   // la tête suit la vague, en plus calme

      // 2. Recentrage : position (haut/bas, côté) de chaque articulation par rapport au poitrail.
      let sumY = 0, sumX = 0;
      const pos = { Root: [0, 0] };
      ORDER.forEach(function (b) {
        const name = b[0], parent = b[2];
        if (!parent) return;
        const pb = SPINE.find(function (x) { return x[0] === parent; });
        const len = Math.abs(b[1] - pb[1]) * SEG, dir = b[1] > pb[1] ? 1 : -1;   // vers la queue : +1
        const pa = abs[parent];
        pos[name] = [pos[parent][0] + dir * len * Math.sin(pa[0]), pos[parent][1] - dir * len * Math.sin(pa[1])];
      });
      SPINE.forEach(function (b) { sumY += pos[b[0]][0]; sumX += pos[b[0]][1]; });
      const cy = -sumY / SPINE.length * p.center, cx = -sumX / SPINE.length * p.center;

      // 3. Angles relatifs (os par rapport à son parent).
      SPINE.forEach(function (b) {
        const name = b[0], parent = b[2], a = abs[name];
        if (name === "Head") return;
        if (!parent) {
          setBone("Root", a[0], a[1], p.bank * Math.sin(st.phase * 0.3),
            cy + p.bob * Math.sin(st.phase * 0.4 + 1) + 0.12 * p.walk * Math.abs(Math.sin(st.step)), 0, cx);
          return;
        }
        const pa = abs[parent];
        setBone(name, a[0] - pa[0], a[1] - pa[1], 0, 0, 0);
      });

      // Regard : la pupille saute vite vers un nouveau point (~80 ms), s'y fixe, avec de petits micro-mouvements.
      // Au repos le dragon regarde partout et la tête suit le regard avec un temps de retard ; en marche et en vol
      // il regarde surtout devant. Un grand changement de regard s'accompagne parfois d'un clignement.
      st.gazeIn -= dt;
      if (st.gazeIn <= 0) {
        const nx = mode === "Idle" ? rnd(-1, 1) : rnd(0.1, 1);
        const ny = mode === "Idle" ? rnd(-1, 1) : rnd(-0.4, 0.4);
        if (Math.abs(nx - st.gazeTx) > 0.8 && !st.blink && Math.random() < 0.3) {
          st.blink = { t: 0, close: 0.07, hold: 0.04, open: 0.15, twice: false };
        }
        st.gazeTx = nx;
        st.gazeTy = ny;
        st.gazeIn = rnd(0.6, 3);
        st.headTarget = mode === "Idle" ? rnd(-0.25, 0.25) : 0;
      }
      st.microIn -= dt;
      if (st.microIn <= 0) {
        st.microIn = rnd(0.25, 0.7);
        st.microX = rnd(-0.07, 0.07);
        st.microY = rnd(-0.07, 0.07);
      }
      const gk = Math.min(1, dt * 28);
      st.gazeX += (st.gazeTx + st.microX - st.gazeX) * gk;
      st.gazeY += (st.gazeTy + st.microY - st.gazeY) * gk;
      st.headLook += (st.headTarget - st.headLook) * Math.min(1, dt * 1.5);

      // Tête : suit la vague (en plus calme), suit le regard avec retard et lève ou baisse un peu le nez avec lui.
      setBone("Head", abs.Head[0] - abs.Neck[0] + 0.04 * Math.sin(st.t * 0.9) - 0.06 * st.gazeY,
        abs.Head[1] - abs.Neck[1] + st.headLook, 0, 0, 0);
      setBone("Jaw", p.jaw * (0.6 + 0.4 * Math.sin(st.t * 1.3)), 0, 0, 0, 0);

      // Clignement : fermeture très rapide, courte pause, réouverture plus lente avec un léger rebond.
      // Parfois un double clignement, et au repos parfois un clignement lent et paresseux.
      // L'œil droit suit le gauche avec 15 ms de retard.
      st.blinkIn -= dt;
      if (st.blinkIn <= 0 && !st.blink) {
        const lazy = mode === "Idle" && Math.random() < 0.2;
        st.blink = lazy ? { t: 0, close: 0.3, hold: 0.25, open: 0.45, twice: false }
                        : { t: 0, close: 0.07, hold: 0.04, open: 0.15, twice: Math.random() < 0.15 };
        st.blinkIn = rnd(2.5, 6);
      }
      let lidL = 0, lidR = 0;
      if (st.blink) {
        const b = st.blink;
        b.t += dt;
        const one = b.close + b.hold + b.open;
        const total = b.twice ? 2 * one + 0.08 : one;
        lidL = closure(b, b.t, one);
        lidR = closure(b, b.t - 0.015, one);
        if (b.t > total + 0.05) st.blink = null;
      }
      setBone("Lid_L", BLINK_UP * lidL, 0, 0, 0, 0);
      setBone("Lid_R", BLINK_UP * lidR, 0, 0, 0, 0);
      setBone("LidLow_L", -BLINK_LOW * Math.max(0, lidL), 0, 0, 0, 0);
      setBone("LidLow_R", -BLINK_LOW * Math.max(0, lidR), 0, 0, 0, 0);
      // Pupilles : glissent sur l'œil (avant / arrière et un peu haut / bas) en suivant sa courbure.
      const g = Math.max(-1, Math.min(1, st.gazeX));
      const gx = g * (g > 0 ? GAZE_FWD : GAZE_BACK), gy = Math.max(-1, Math.min(1, st.gazeY)) * GAZE_Y;
      const depth = EYE.D * (Math.sqrt(Math.max(0, 1 - (gx / EYE.L) * (gx / EYE.L))) - 1);
      setBone("Pupil_L", 0, 0, 0, gy, depth, PUPIL_FWD.L * gx);
      setBone("Pupil_R", 0, 0, 0, gy, depth, PUPIL_FWD.R * gx);

      // Crinière, moustaches, barbichette : flottent, se soulèvent en vol et traînent derrière les mouvements
      // de la tête.
      const f = st.flutter, m = p.mane, lift = 0.22 * p.tuck;
      const drag = -0.8 * (abs.Neck[0] - abs.Neck2[0]), dragY = -0.8 * (abs.Neck[1] - abs.Neck2[1]);
      setBone("Mane_Top", lift + drag + 0.5 * m * Math.sin(f), dragY + m * Math.sin(f * 1.3 + 1), 0, 0, 0);
      setBone("Mane_L", lift + drag + 0.6 * m * Math.sin(f + 2), dragY + m * Math.sin(f * 1.1 + 0.5), 0, 0, 0);
      setBone("Mane_R", lift + drag + 0.6 * m * Math.sin(f + 2.6), dragY - m * Math.sin(f * 1.1 + 1.2), 0, 0, 0);
      setBone("Whisker_L", 0.8 * m * Math.sin(f * 0.9) + drag, m * Math.sin(f * 0.7 + 0.3) + dragY, 0, 0, 0);
      setBone("Whisker_R", 0.8 * m * Math.sin(f * 0.9 + 1) + drag, -m * Math.sin(f * 0.7 + 1.1) + dragY, 0, 0, 0);
      setBone("Beard", 0.5 * m * Math.sin(f * 0.8) + drag, 0.4 * m * Math.sin(f * 1.2), 0, 0, 0);

      // Pattes : marche en diagonale ; en vol, repliées et elles suivent doucement la vague du corps.
      for (const leg in LEGS) {
        const off = LEGS[leg][0], s = LEGS[leg][1];
        const ph = st.step + off;
        const sw = Math.sin(ph), up = Math.max(0, Math.cos(ph));
        const flow = 0.5 * bodyAngles(p, s + 6)[0] * p.tuck;
        setBone(leg + "_Upper", -0.45 * sw * p.walk + 0.9 * p.tuck + flow, 0, 0, 0, 0);
        setBone(leg + "_Fore", 0.6 * up * p.walk + 0.6 * p.tuck + flow, 0, 0, 0, 0);
        setBone(leg + "_Foot", -0.35 * up * p.walk - 0.4 * p.tuck, 0, 0, 0, 0);
      }
    }
    return { update: update, state: st };
  }
  global.DragonAnimator = { create: create, MODES: MODES, BLINK_UP: BLINK_UP, BLINK_LOW: BLINK_LOW };
})(window);
