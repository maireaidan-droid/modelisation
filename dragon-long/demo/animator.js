// Animation procédurale du Dragon Long (même logique que roblox/DragonAnimator.client.lua).
// Chaque os reçoit une rotation par rapport à sa pose de repos, recalculée à chaque image.
(function (global) {
  const BLINK = 0.45;              // la paupière descend un peu (rad)…
  const SINK = 0.75;               // …et l'œil s'enfonce dans l'orbite (studs) : l'œil paraît fermé
  const MODES = {
    Idle: { side: 0.035, pitch: 0.015, wave: 1.2, tuck: 0, walk: 0, mane: 0.12, maneSpeed: 1.6, jaw: 0.04, bob: 0.15, bank: 0, dive: 0 },
    Walk: { side: 0.07, pitch: 0.012, wave: 3.4, tuck: 0, walk: 1, mane: 0.2, maneSpeed: 3.2, jaw: 0.07, bob: 0.2, bank: 0, dive: 0 },
    // Vol : grandes vagues verticales qui descendent du cou vers la queue (le dragon « nage » dans l'air),
    // un peu de roulis et de tangage de tout le corps, crinière soulevée qui claque au vent.
    Fly:  { side: 0.06, pitch: 0.17, wave: 2.6, tuck: 1, walk: 0, mane: 0.5, maneSpeed: 7, jaw: 0.14, bob: 1.4, bank: 0.12, dive: 0.08 }
  };
  const TAIL = [];
  for (let k = 1; k <= 14; k++) TAIL.push("S" + String(k).padStart(2, "0"));
  const LEGS = { LegFL: 0, LegBR: 0, LegFR: Math.PI, LegBL: Math.PI };

  function create(bones, setBone) {
    // setBone(name, rx, ry, rz, ty, tz) : rotation (X puis Y puis Z, comme CFrame.Angles) + petit décalage
    // le long des axes Y et Z de l'os
    const st = { mode: "Idle", p: Object.assign({}, MODES.Idle), phase: 0, step: 0, flutter: 0, t: 0,
      blinkIn: 2, blink: -1, look: 0, lookTarget: 0, lookIn: 1.5, headLook: 0, headTarget: 0 };
    function rnd(a, b) { return a + Math.random() * (b - a); }
    function update(dt, mode) {
      st.t += dt;
      const target = MODES[mode] || MODES.Idle;
      const k = Math.min(1, dt * 2.5);
      for (const key in target) st.p[key] += (target[key] - st.p[key]) * k;
      const p = st.p;
      st.phase += dt * p.wave;
      st.step += dt * 4.2 * p.walk;
      st.flutter += dt * p.maneSpeed;

      // Colonne : une onde qui part du cou et grandit vers la queue.
      TAIL.forEach(function (name, i) {
        const k1 = i + 1, grow = 0.6 + 0.6 * k1 / 14;
        const yaw = p.side * grow * Math.sin(st.phase * 0.7 - k1 * 0.4 + 1);
        const pitch = p.pitch * grow * Math.sin(st.phase - k1 * 0.45);
        setBone(name, pitch, yaw, 0, 0);
      });
      const neckYaw = p.side * 0.7 * Math.sin(st.phase * 0.7 + 1.4);
      const neckPitch = p.pitch * 0.9 * Math.sin(st.phase + 0.45);
      setBone("Neck", neckPitch, neckYaw, 0, 0);
      // Tout le corps : monte et descend, pique légèrement et s'incline (roulis) en vol.
      setBone("Root", p.dive * Math.sin(st.phase * 0.5), 0, p.bank * Math.sin(st.phase * 0.35), 
        p.bob * Math.sin(st.phase * 0.5 + 1) + 0.12 * p.walk * Math.abs(Math.sin(st.step)));

      // Tête : compense l'ondulation pour garder le regard stable, et regarde autour en Idle.
      st.lookIn -= dt;
      if (st.lookIn <= 0) {
        st.lookIn = rnd(1.5, 4);
        st.lookTarget = rnd(-0.2, 0.2);
        st.headTarget = mode === "Idle" ? rnd(-0.25, 0.25) : 0;
      }
      st.look += (st.lookTarget - st.look) * Math.min(1, dt * 6);
      st.headLook += (st.headTarget - st.headLook) * Math.min(1, dt * 1.5);
      // La tête garde le cap : elle compense une bonne partie de l'ondulation du cou.
      setBone("Head", 0.05 * Math.sin(st.t * 0.9) - neckPitch * 0.7, -neckYaw * 0.8 + st.headLook, 0, 0);
      setBone("Jaw", p.jaw * (0.6 + 0.4 * Math.sin(st.t * 1.3)), 0, 0, 0);

      // Clignement : fermeture rapide, réouverture un peu plus lente.
      st.blinkIn -= dt;
      if (st.blinkIn <= 0 && st.blink < 0) { st.blink = 0; st.blinkIn = rnd(2, 6); }
      let lid = 0;
      if (st.blink >= 0) {
        st.blink += dt;
        lid = st.blink < 0.07 ? st.blink / 0.07 : Math.max(0, 1 - (st.blink - 0.07) / 0.13);
        if (st.blink > 0.2) st.blink = -1;
      }
      setBone("Lid_L", BLINK * lid, 0, 0, 0);
      setBone("Lid_R", BLINK * lid, 0, 0, 0);
      setBone("Eye_L", 0, st.look, 0, 0, -SINK * lid);
      setBone("Eye_R", 0, st.look, 0, 0, -SINK * lid);

      // Crinière, moustaches, barbichette : flottent, plus fort en vol.
      const f = st.flutter, m = p.mane;
      const lift = 0.25 * p.tuck;                      // en vol, la crinière se soulève et part vers l'arrière
      setBone("Mane_Top", lift + 0.5 * m * Math.sin(f), m * Math.sin(f * 1.3 + 1), 0, 0);
      setBone("Mane_L", lift + 0.6 * m * Math.sin(f + 2), m * Math.sin(f * 1.1 + 0.5), 0, 0);
      setBone("Mane_R", lift + 0.6 * m * Math.sin(f + 2.6), -m * Math.sin(f * 1.1 + 1.2), 0, 0);
      setBone("Whisker_L", 0.8 * m * Math.sin(f * 0.9), m * Math.sin(f * 0.7 + 0.3), 0, 0);
      setBone("Whisker_R", 0.8 * m * Math.sin(f * 0.9 + 1), -m * Math.sin(f * 0.7 + 1.1), 0, 0);
      setBone("Beard", 0.5 * m * Math.sin(f * 0.8), 0.4 * m * Math.sin(f * 1.2), 0, 0);

      // Pattes : marche en diagonale (avant gauche + arrière droite, puis l'inverse), repliées en vol.
      for (const leg in LEGS) {
        const ph = st.step + LEGS[leg];
        const sw = Math.sin(ph), lift = Math.max(0, Math.cos(ph));
        const paddle = 0.15 * p.tuck * Math.sin(st.phase * 1.5 + LEGS[leg]);   // pattes qui pagaient en vol
        setBone(leg + "_Upper", -0.45 * sw * p.walk + 0.9 * p.tuck + paddle, 0, 0, 0);
        setBone(leg + "_Fore", 0.6 * lift * p.walk + 0.6 * p.tuck, 0, 0, 0);
        setBone(leg + "_Foot", -0.35 * lift * p.walk - 0.4 * p.tuck, 0, 0, 0);
      }
    }
    return { update: update, state: st };
  }
  global.DragonAnimator = { create: create, MODES: MODES, BLINK: BLINK, SINK: SINK };
})(window);
