// Animation procédurale du Dragon Long (même logique que roblox/DragonAnimator.client.lua).
// Chaque os reçoit une rotation par rapport à sa pose de repos, recalculée à chaque image.
//
// Le corps est piloté comme un serpent : on décrit la FORME voulue de tout le corps (une vague qui glisse
// de la tête vers la queue, de même amplitude partout), puis on en déduit l'angle de chaque os
// (= différence d'orientation avec l'os parent). Le corps est ensuite recentré pour que la tête, le milieu
// et la queue ondulent tous ensemble, au lieu de rester accrochés au poitrail.
(function (global) {
  const BLINK = 0.45;              // la paupière descend un peu (rad)…
  const SINK = 0.75;               // …et l'œil s'enfonce dans l'orbite (studs) : l'œil paraît fermé
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

  function create(bones, setBone) {
    // setBone(name, rx, ry, rz, ty, tz, tx) : rotation (X puis Y puis Z, comme CFrame.Angles) + décalage
    // le long des axes de l'os
    const st = { p: Object.assign({}, MODES.Idle), phase: 0, step: 0, flutter: 0, t: 0,
      blinkIn: 2, blink: -1, look: 0, lookTarget: 0, lookIn: 1.5, headLook: 0, headTarget: 0 };
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

      // Tête : suit la vague (en plus calme) et regarde autour d'elle au repos.
      st.lookIn -= dt;
      if (st.lookIn <= 0) {
        st.lookIn = rnd(1.5, 4);
        st.lookTarget = rnd(-0.2, 0.2);
        st.headTarget = mode === "Idle" ? rnd(-0.25, 0.25) : 0;
      }
      st.look += (st.lookTarget - st.look) * Math.min(1, dt * 6);
      st.headLook += (st.headTarget - st.headLook) * Math.min(1, dt * 1.5);
      setBone("Head", abs.Head[0] - abs.Neck[0] + 0.04 * Math.sin(st.t * 0.9),
        abs.Head[1] - abs.Neck[1] + st.headLook, 0, 0, 0);
      setBone("Jaw", p.jaw * (0.6 + 0.4 * Math.sin(st.t * 1.3)), 0, 0, 0, 0);

      // Clignement : fermeture rapide, réouverture un peu plus lente.
      st.blinkIn -= dt;
      if (st.blinkIn <= 0 && st.blink < 0) { st.blink = 0; st.blinkIn = rnd(2, 6); }
      let lid = 0;
      if (st.blink >= 0) {
        st.blink += dt;
        lid = st.blink < 0.07 ? st.blink / 0.07 : Math.max(0, 1 - (st.blink - 0.07) / 0.13);
        if (st.blink > 0.2) st.blink = -1;
      }
      setBone("Lid_L", BLINK * lid, 0, 0, 0, 0);
      setBone("Lid_R", BLINK * lid, 0, 0, 0, 0);
      setBone("Eye_L", 0, st.look, 0, 0, -SINK * lid);
      setBone("Eye_R", 0, st.look, 0, 0, -SINK * lid);

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
  global.DragonAnimator = { create: create, MODES: MODES, BLINK: BLINK, SINK: SINK };
})(window);
