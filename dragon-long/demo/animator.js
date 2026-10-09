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
  const PULSE_SEGMENTS = 8, PULSE_STEP = 0.6;  // Mythique : tronçons de la vague de lumière, décalage entre deux

  // up / side : amplitude de la vague verticale / latérale (rad) ; speed : vitesse de la vague (rad/s) ;
  // helix : décalage entre les deux (pi/2 = chaque anneau décrit un cercle, le corps s'enroule en spirale) ;
  // center : recentrage du corps (1 = tout le corps ondule autour de son milieu, 0 = ancré au poitrail).
  const MODES = {
    Idle: { up: 0.03, side: 0.06, speed: 1.2, helix: 0, center: 0, tuck: 0, mane: 0.12, maneSpeed: 1.6,
            jaw: 0.04, bob: 0.15, bank: 0, head: 0.6, dead: 0 },
    // Vol : longue vague souple et continue de la tête à la queue, un peu en spirale ; le dragon « nage » dans
    // l'air. Léger roulis, crinière soulevée, pattes repliées qui suivent la vague.
    Fly:  { up: 0.34, side: 0.16, speed: 2.0, helix: 1.57, center: 1, tuck: 1, mane: 0.42, maneSpeed: 5,
            jaw: 0.12, bob: 0.8, bank: 0.1, head: 0.45, dead: 0 },
    // Mort : le corps cesse d'onduler, s'effondre sur le flanc en se courbant, yeux fermés, pattes molles.
    Dead: { up: 0, side: 0, speed: 0.3, helix: 0, center: 0, tuck: 0, mane: 0.03, maneSpeed: 0.8,
            jaw: 0, bob: 0, bank: 0, head: 1, dead: 1 }
  };

  // Actions ponctuelles (lancées par play(nom)) : durée en secondes.
  const ACTIONS = { Roar: 3.3, Bite: 1.6, Breath: 3.2 };
  // Instant fort de chaque action (cri du rugissement, claquement de la morsure) : effets et caméra.
  const BURSTS = { Roar: 0.62, Bite: 0.52 };
  const TURN_CURVE = 0.027;  // courbure du corps (rad par pas de colonne) pour 1 rad/s de virage
  const DEAD_DROP = 3.6;     // le dragon couché sur le flanc : le poitrail descend de tant de studs
  const MID = 34;            // milieu du corps (pas de colonne) : le corps se courbe autour de ce point

  function ramp(t, a, b) {   // 0 avant a, 1 après b, transition douce entre les deux
    const x = Math.max(0, Math.min(1, (t - a) / (b - a)));
    return x * x * (3 - 2 * x);
  }

  // Pose d'une action à l'instant t : rear = cou dressé (rad), pitch / yaw = tête en plus (rad), jaw = gueule,
  // push = poitrail en avant / en arrière (studs), lift = poitrail plus haut, mane = crinière hérissée,
  // lash = queue qui fouette, breath = souffle (0 à 1, pour les particules), cry = force du cri (0 à 1),
  // shiver = frisson qui parcourt le corps, eyes = yeux grands ouverts (0 à 1), sweep = moustaches plaquées.
  function actionPose(name, t) {
    const o = { rear: 0, pitch: 0, yaw: 0, jaw: 0, push: 0, lift: 0, mane: 0, lash: 0, breath: 0,
                cry: 0, shiver: 0, eyes: 0, sweep: 0, coil: 0, aim: 0 };
    if (name === "Roar") {
      // 1. Se ramasse : tête basse, poitrail en arrière, gueule fermée.
      const crouch = ramp(t, 0, 0.45) * (1 - ramp(t, 0.5, 0.65));
      // 2. Explose : cou dressé, tête projetée en avant vers l'ennemi, gueule grande ouverte.
      const cry = ramp(t, 0.5, 0.68) * (1 - ramp(t, 2.1, 2.7));
      const high = ramp(t, 0.5, 0.7) * (1 - ramp(t, 2.6, 3.3));     // garde la tête haute un moment après
      // 3. Secousse forte au début qui s'amortit.
      const k = Math.max(0, t - 0.68);
      const shake = 0.2 * Math.exp(-k * 2.6) * Math.sin(k * 24) * cry;
      // 4. Petit souffle par les narines à la fin : la tête donne un coup sec.
      const snort = ramp(t, 2.85, 2.92) * (1 - ramp(t, 2.95, 3.15));
      o.rear = -0.3 * crouch + 0.4 * high;
      o.pitch = 0.22 * crouch + 0.08 * cry - 0.12 * high * (1 - cry) + 0.1 * snort;
      o.push = -0.8 * crouch + 1.1 * cry;
      o.lift = -0.5 * crouch + 0.35 * high;
      o.jaw = 1.0 * cry;
      o.yaw = shake;
      o.mane = 0.8 * cry + 0.2 * high;
      o.lash = 0.12 * cry;
      o.cry = cry;
      o.shiver = 0.035 * cry;
      o.eyes = cry;
      o.sweep = cry;
    } else if (name === "Bite") {
      // Arrêt net à l'impact : le temps de la pose se fige 70 ms juste après le claquement.
      const tt = t < 0.53 ? t : (t < 0.6 ? 0.53 : t - 0.07);
      // 1. S'arme comme un serpent : cou replié en S, tête en arrière, crocs visibles, yeux fixés sur la cible.
      const coil = ramp(tt, 0, 0.3) * (1 - ramp(tt, 0.34, 0.44));
      // 2. Frappe : tout l'avant du corps se projette, gueule ouverte au maximum juste avant l'impact.
      const strike = ramp(tt, 0.34, 0.5) * (1 - ramp(tt, 0.62, 1.3));
      // 3. Petit rebond en arrière après l'impact.
      const recoil = ramp(tt, 0.53, 0.62) * (1 - ramp(tt, 0.62, 0.85));
      // 4. Retour menaçant : tête basse, babines relevées, petit grognement.
      const snarl = ramp(tt, 0.6, 0.8) * (1 - ramp(tt, 1.25, 1.53));
      const open = ramp(tt, 0.3, 0.46) * (1 - ramp(tt, 0.48, 0.52));
      const bounce = ramp(tt, 0.52, 0.56) * (1 - ramp(tt, 0.6, 0.7));    // la mâchoire rebondit après le claquement
      o.rear = 0.4 * coil - 0.25 * strike + 0.1 * snarl;
      o.pitch = -0.12 * coil + 0.22 * strike - 0.12 * recoil + 0.12 * snarl;
      o.push = -1.1 * coil + 2.6 * strike - 0.5 * recoil;
      o.lift = -0.25 * coil + 0.1 * strike;
      o.jaw = 0.15 * coil + 1.0 * open + 0.15 * bounce + 0.18 * snarl;
      o.yaw = 0.02 * Math.sin(t * 45) * snarl;
      o.mane = 0.25 * coil + 0.35 * strike + 0.2 * snarl;
      o.eyes = 0.7 * Math.max(coil, strike);
      o.coil = coil;
      o.aim = ramp(tt, 0, 0.3) * (1 - ramp(tt, 1.0, 1.5));
    } else if (name === "Breath") {
      // Inspire (cou dressé, tête en arrière), puis souffle longtemps en balayant devant lui.
      const inhale = ramp(t, 0, 0.9) * (1 - ramp(t, 0.9, 1.15));
      const blow = ramp(t, 1.0, 1.2) * (1 - ramp(t, 2.6, 3.1));
      o.rear = 0.5 * inhale + 0.1 * blow; o.pitch = -0.3 * inhale + 0.18 * blow;
      o.jaw = 0.1 * inhale + 0.85 * blow; o.yaw = 0.25 * Math.sin((t - 1.1) * 2.4) * blow;
      o.push = -0.5 * inhale + 0.4 * blow; o.lift = 0.3 * inhale; o.mane = 0.4 * inhale + 0.3 * blow;
      o.breath = ramp(t, 1.05, 1.25) * (1 - ramp(t, 2.5, 2.9));
    }
    return o;
  }

  // Colonne, de la tête à la queue : [os, position le long du corps (pas de colonne), parent].
  const SPINE = [["Head", 0, "Neck"], ["Neck", 5, "Neck2"], ["Neck2", 10, "Root"], ["Root", 14, null]];
  for (let k = 1; k <= 14; k++) {
    SPINE.push(["S" + String(k).padStart(2, "0"), 14 + 4 * k, k === 1 ? "Root" : "S" + String(k - 1).padStart(2, "0")]);
  }
  // Ordre parent → enfant (pour cumuler les positions depuis le poitrail).
  const ORDER = ["Root", "Neck2", "Neck", "Head"].concat(SPINE.slice(4).map(function (b) { return b[0]; }))
    .map(function (n) { return SPINE.find(function (b) { return b[0] === n; }); });
  const LEGS = { LegFL: 14, LegBR: 42, LegFR: 14, LegBL: 42 };   // position de chaque patte le long du corps

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
    const st = { p: Object.assign({}, MODES.Idle), phase: 0, flutter: 0, pulse: 0, t: 0,
      action: null, actionT: 0, breath: 0, cry: 0, burst: null, aimYaw: 0, aimPitch: 0, turn: 0, deadT: 0,
      blinkIn: 2, blink: null, headLook: 0, headTarget: 0,
      gazeX: 0, gazeY: 0, gazeTx: 0, gazeTy: 0, gazeIn: 1, microX: 0, microY: 0, microIn: 0.5 };
    function rnd(a, b) { return a + Math.random() * (b - a); }

    // Forme du corps : angle de la colonne (haut/bas, côté) à la position s.
    function bodyAngles(p, s) {
      const env = 0.8 + 0.3 * s / 70;
      const a = KAPPA * s - st.phase;
      return [p.up * env * Math.sin(a), p.side * env * Math.sin(a + p.helix)];
    }

    // Vague de lumière : 0 (éteint) à 1 (pic) pour le tronçon c (0 = cornes, 1 à 8 de la tête vers la queue).
    function pulseAt(c) {
      return Math.pow(Math.max(0, Math.sin(st.pulse - PULSE_STEP * c)), 6);
    }

    // Lance une action ponctuelle (Roar, Bite, Breath). Ignorée si le dragon est mort.
    // aimYaw / aimPitch (rad, facultatifs) : direction de la cible par rapport à l'avant du dragon
    // (positif = vers la gauche / vers le haut). La morsure part vers elle.
    function play(name, aimYaw, aimPitch) {
      if (ACTIONS[name] && st.p.dead < 0.5) {
        st.action = name; st.actionT = 0;
        st.aimYaw = Math.max(-0.8, Math.min(0.8, aimYaw || 0));
        st.aimPitch = Math.max(-0.5, Math.min(0.5, aimPitch || 0));
      }
    }

    // turn : vitesse de virage du dragon (rad/s, positif = vers la gauche, c'est-à-dire vers +X quand il
    // regarde vers +Z). Le corps se courbe dans le virage, la tête regarde à l'intérieur, en vol il s'incline.
    function update(dt, mode, turn) {
      st.t += dt;
      const target = MODES[mode] || MODES.Idle;
      const k = Math.min(1, dt * 1.8);
      for (const key in target) st.p[key] += (target[key] - st.p[key]) * k;
      const p = st.p;
      st.phase += dt * p.speed;
      st.flutter += dt * p.maneSpeed;
      st.pulse += dt * (1.3 + 1.7 * p.tuck);       // vague de lumière (Mythique) : plus rapide en vol
      st.turn += (Math.max(-1.5, Math.min(1.5, turn || 0)) - st.turn) * Math.min(1, dt * 3);
      st.deadT = mode === "Dead" ? st.deadT + dt : 0;
      let act = actionPose("", 0);
      if (st.action) {
        st.actionT += dt;
        if (st.actionT >= ACTIONS[st.action] || p.dead > 0.5) st.action = null;
        else act = actionPose(st.action, st.actionT);
      }
      st.breath = act.breath;
      st.cry = act.cry;
      // Instant fort de l'action (cri, claquement) : nom de l'action pendant une seule image, sinon null.
      const bt = st.action ? BURSTS[st.action] : undefined;
      st.burst = bt !== undefined && st.actionT >= bt && st.actionT - dt < bt ? st.action : null;
      const aimY = st.aimYaw * act.aim, aimP = st.aimPitch * act.aim;
      const d = p.dead;
      // Frisson quand il tombe : une dernière vague rapide qui s'éteint.
      const shiver = 0.1 * Math.sin(st.deadT * 16) * Math.exp(-st.deadT * 2.2) * d;

      // 1. Orientation voulue de chaque morceau de colonne.
      const abs = {};
      SPINE.forEach(function (b) { abs[b[0]] = bodyAngles(p, b[1]); });
      abs.Head = [abs.Head[0] * p.head, abs.Head[1] * p.head];   // la tête suit la vague, en plus calme
      // Poses ajoutées à la forme du corps : cou dressé (actions), courbe du virage, corps recourbé (mort),
      // queue qui fouette (rugissement).
      SPINE.forEach(function (b) {
        const sp = b[1], a = abs[b[0]];
        const front = 1 - ramp(sp, 4, 20);                        // 1 pour la tête et le cou, 0 dès le poitrail
        // Couché sur le flanc, l'axe « haut / bas » de la colonne devient horizontal : c'est lui qui recourbe
        // le corps en croissant sur le sol.
        a[0] += -act.rear * front + 0.022 * d * (14 - sp)        // nul au poitrail : le corps ne bascule pas
              - 0.5 * aimP * front;                                // le cou se lève / se baisse vers la cible
        a[1] += TURN_CURVE * st.turn * (MID - sp) * (1 - d) + shiver * Math.sin(sp * 0.3)
              + act.lash * ramp(sp, 30, 60) * Math.sin(st.t * 9 - sp * 0.15)
              + act.shiver * Math.sin(st.t * 38 - sp * 0.4)                // frisson du cri, de la tête à la queue
              + act.yaw * 0.5 * front                                      // le cou suit la secousse de la tête
              + 0.6 * aimY * front                                         // le cou se tourne vers la cible
              + 0.3 * act.coil * front * Math.sin(sp * 0.45);              // cou replié en S avant de frapper
      });

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
          setBone("Root", a[0], a[1], p.bank * Math.sin(st.phase * 0.3) - 0.6 * st.turn * p.tuck - 1.35 * d,
            cy + p.bob * Math.sin(st.phase * 0.4 + 1) + act.lift
              - DEAD_DROP * d, act.push, cx);
          return;
        }
        const pa = abs[parent];
        setBone(name, a[0] - pa[0], a[1] - pa[1], 0, 0, 0);
      });

      // Regard : la pupille saute vite vers un nouveau point (~80 ms), s'y fixe, avec de petits micro-mouvements.
      // Au repos le dragon regarde partout et la tête suit le regard avec un temps de retard ; en vol
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
        st.headTarget = mode === "Idle" && !st.action ? rnd(-0.25, 0.25) : 0;
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
      // En virage, la tête regarde à l'intérieur ; mort, elle retombe, gueule entrouverte.
      setBone("Head", abs.Head[0] - abs.Neck[0] + (0.04 * Math.sin(st.t * 0.9) - 0.06 * st.gazeY) * (1 - d) + act.pitch
        + 0.25 * d - 0.5 * aimP, abs.Head[1] - abs.Neck[1] + st.headLook * (1 - d) + act.yaw + 0.45 * st.turn * (1 - d)
        + 0.4 * aimY, 0, 0, 0);
      setBone("Jaw", Math.max(p.jaw * (0.6 + 0.4 * Math.sin(st.t * 1.3)), act.jaw) + 0.2 * d, 0, 0, 0, 0);

      // Clignement : fermeture très rapide, courte pause, réouverture plus lente avec un léger rebond.
      // Parfois un double clignement, et au repos parfois un clignement lent et paresseux.
      // L'œil droit suit le gauche avec 15 ms de retard.
      st.blinkIn -= dt;
      if (st.blinkIn <= 0 && !st.blink && !st.action) {
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
      // Mort : yeux fermés ; rugissement : paupières remontées, yeux grands ouverts.
      lidL = lidL * (1 - d) + d - 0.12 * act.eyes;
      lidR = lidR * (1 - d) + d - 0.12 * act.eyes;
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
      const f = st.flutter, m = p.mane + 0.25 * act.mane, lift = 0.22 * p.tuck + act.mane;
      const drag = -0.8 * (abs.Neck[0] - abs.Neck2[0]), dragY = -0.8 * (abs.Neck[1] - abs.Neck2[1]);
      setBone("Mane_Top", lift + drag + 0.5 * m * Math.sin(f), dragY + m * Math.sin(f * 1.3 + 1), 0, 0, 0);
      setBone("Mane_L", lift + drag + 0.6 * m * Math.sin(f + 2), dragY + m * Math.sin(f * 1.1 + 0.5), 0, 0, 0);
      setBone("Mane_R", lift + drag + 0.6 * m * Math.sin(f + 2.6), dragY - m * Math.sin(f * 1.1 + 1.2), 0, 0, 0);
      // Rugissement : moustaches et barbichette plaquées vers l'arrière par le souffle du cri.
      const sweep = -0.6 * act.sweep;
      setBone("Whisker_L", 0.8 * m * Math.sin(f * 0.9) + drag + sweep, m * Math.sin(f * 0.7 + 0.3) + dragY, 0, 0, 0);
      setBone("Whisker_R", 0.8 * m * Math.sin(f * 0.9 + 1) + drag + sweep, -m * Math.sin(f * 0.7 + 1.1) + dragY, 0, 0, 0);
      setBone("Beard", 0.5 * m * Math.sin(f * 0.8) + drag - 0.4 * act.sweep, 0.4 * m * Math.sin(f * 1.2), 0, 0, 0);

      // Cristaux flottants (Mythique, os Crest1 à Crest8) : montent et descendent doucement, et se soulèvent
      // un peu quand la vague de lumière passe. Les autres dragons n'ont pas ces os : rien ne se passe.
      for (let c = 1; c <= PULSE_SEGMENTS; c++) {
        setBone("Crest" + c, 0.06 * Math.sin(st.t * 1.3 + c * 0.9), 0, 0.05 * Math.sin(st.t * 1.1 + c * 1.7),
          0.35 * Math.sin(st.t * 1.6 + c * 0.7) + 0.3 * pulseAt(c), 0);
      }

      // Pattes : en vol, repliées et elles suivent doucement la vague du corps ; mort, molles et écartées.
      for (const leg in LEGS) {
        const flow = 0.5 * bodyAngles(p, LEGS[leg] + 6)[0] * p.tuck;
        setBone(leg + "_Upper", 0.9 * p.tuck + flow + 0.45 * d, 0, 0, 0, 0);
        setBone(leg + "_Fore", 0.6 * p.tuck + flow + 0.35 * d, 0, 0, 0, 0);
        setBone(leg + "_Foot", -0.4 * p.tuck - 0.2 * d, 0, 0, 0, 0);
      }
    }
    return { update: update, play: play, state: st, pulseAt: pulseAt };
  }
  global.DragonAnimator = { create: create, MODES: MODES, ACTIONS: ACTIONS, BURSTS: BURSTS, BLINK_UP: BLINK_UP, BLINK_LOW: BLINK_LOW };
})(window);
