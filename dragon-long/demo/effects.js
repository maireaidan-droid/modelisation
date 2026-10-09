// Souffle du dragon (démo web) : un jet de particules qui sort de la gueule quand l'animateur souffle
// (state.breath entre 0 et 1). Quatre styles : feu, glace, or, néant.
(function (global) {
  // Couleur au début, au milieu et à la fin de la vie d'une particule (linéaire, 0 à 1).
  const PRESETS = {
    fire: [[1.0, 0.95, 0.6], [1.0, 0.45, 0.08], [0.45, 0.06, 0.03]],
    ice:  [[0.95, 1.0, 1.0], [0.45, 0.9, 1.0], [0.15, 0.35, 0.75]],
    gold: [[1.0, 1.0, 0.85], [1.0, 0.78, 0.25], [0.7, 0.4, 0.05]],
    void: [[1.0, 0.85, 1.0], [0.95, 0.25, 0.85], [0.3, 0.08, 0.6]]
  };
  const N = 700, LIFE = 1.05;

  function createBreath(THREE, scene) {
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(N * 3), col = new Float32Array(N * 3), alpha = new Float32Array(N), size = new Float32Array(N);
    const vel = new Float32Array(N * 3), age = new Float32Array(N).fill(LIFE);
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    geo.setAttribute("alpha", new THREE.BufferAttribute(alpha, 1));
    geo.setAttribute("size", new THREE.BufferAttribute(size, 1));
    const mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uScale: { value: 1 } },
      vertexShader: "attribute vec3 color; attribute float alpha; attribute float size; uniform float uScale;" +
        "varying vec3 vC; varying float vA; void main(){ vC = color; vA = alpha;" +
        "vec4 mv = modelViewMatrix * vec4(position,1.0); gl_PointSize = uScale * size * 40.0 / -mv.z;" +
        "gl_Position = projectionMatrix * mv; }",
      fragmentShader: "varying vec3 vC; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5);" +
        "float a = smoothstep(0.5, 0.0, r) * vA; gl_FragColor = vec4(vC * a, a); }"
    });
    const points = new THREE.Points(geo, mat);
    points.frustumCulled = false;
    scene.add(points);

    let preset = PRESETS.fire, carry = 0, next = 0;
    const tmp = new THREE.Vector3();

    function lerp3(a, b, t, out, o) {
      out[o] = a[0] + (b[0] - a[0]) * t; out[o + 1] = a[1] + (b[1] - a[1]) * t; out[o + 2] = a[2] + (b[2] - a[2]) * t;
    }

    // origin : point de départ (bout de la gueule), dir : direction du jet (vecteur unitaire), amount : 0 à 1.
    function update(dt, amount, origin, dir) {
      carry += amount * 480 * dt;
      while (carry >= 1) {
        carry -= 1;
        const i = next;
        next = (next + 1) % N;
        age[i] = 0;
        pos[i * 3] = origin.x; pos[i * 3 + 1] = origin.y; pos[i * 3 + 2] = origin.z;
        tmp.set(Math.random() - 0.5, Math.random() - 0.5, Math.random() - 0.5).multiplyScalar(0.45).add(dir).normalize()
          .multiplyScalar(26 + Math.random() * 10);
        vel[i * 3] = tmp.x; vel[i * 3 + 1] = tmp.y; vel[i * 3 + 2] = tmp.z;
      }
      for (let i = 0; i < N; i++) {
        if (age[i] >= LIFE) { alpha[i] = 0; continue; }
        age[i] += dt;
        const q = Math.min(1, age[i] / LIFE);
        const drag = Math.max(0, 1 - dt * 0.9);
        vel[i * 3] *= drag; vel[i * 3 + 1] = vel[i * 3 + 1] * drag + dt * 6; vel[i * 3 + 2] *= drag;
        pos[i * 3] += vel[i * 3] * dt; pos[i * 3 + 1] += vel[i * 3 + 1] * dt; pos[i * 3 + 2] += vel[i * 3 + 2] * dt;
        if (q < 0.35) lerp3(preset[0], preset[1], q / 0.35, col, i * 3);
        else lerp3(preset[1], preset[2], (q - 0.35) / 0.65, col, i * 3);
        alpha[i] = Math.min(1, age[i] * 25) * Math.pow(1 - q, 1.3) * 0.9;
        size[i] = 0.8 + 4.6 * q;
      }
      geo.attributes.position.needsUpdate = true;
      geo.attributes.color.needsUpdate = true;
      geo.attributes.alpha.needsUpdate = true;
      geo.attributes.size.needsUpdate = true;
    }

    return {
      update: update,
      setStyle: function (name) { preset = PRESETS[name] || PRESETS.fire; },
      setScale: function (s) { mat.uniforms.uScale.value = s; },
      points: points
    };
  }

  // Bout de la gueule dans le repère de l'os Head : on prend le bout de la langue (le point le plus en avant).
  function mouthInHead(THREE, meshes, head) {
    const tongue = meshes && meshes[0];
    if (!tongue || !head) return new THREE.Vector3(0, -0.5, 4);
    let top = head;                                   // matrices à jour depuis la racine du modèle
    while (top.parent) top = top.parent;
    top.updateMatrixWorld(true);
    const p = tongue.geometry.attributes.position, best = new THREE.Vector3(), v = new THREE.Vector3();
    let bestZ = -Infinity;
    for (let i = 0; i < p.count; i++) {
      v.fromBufferAttribute(p, i);
      if (v.z > bestZ) { bestZ = v.z; best.copy(v); }
    }
    return head.worldToLocal(best.applyMatrix4(tongue.matrixWorld)).add(new THREE.Vector3(0, 0, 0.8));
  }

  // Onde de choc du rugissement : trois anneaux qui partent de la gueule, s'agrandissent et s'effacent.
  function createShockwave(THREE, scene) {
    const rings = [];
    for (let k = 0; k < 3; k++) {
      const m = new THREE.Mesh(new THREE.RingGeometry(0.94, 1, 64), new THREE.MeshBasicMaterial({
        transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending }));
      m.visible = false;
      m.userData.t = 99;
      scene.add(m);
      rings.push(m);
    }
    const look = new THREE.Vector3();
    return {
      // origin : bout de la gueule, dir : direction du cri, color : couleur des anneaux
      trigger: function (origin, dir, color) {
        rings.forEach(function (m, k) {
          m.position.copy(origin).addScaledVector(dir, 1.5);
          m.lookAt(look.copy(m.position).add(dir));
          m.material.color.set(color).convertSRGBToLinear();
          m.userData.t = -0.13 * k;                   // les anneaux partent l'un après l'autre
          m.userData.dir = dir.clone();
        });
      },
      update: function (dt) {
        rings.forEach(function (m) {
          m.userData.t += dt;
          const q = m.userData.t / 0.95;
          m.visible = q > 0 && q < 1;
          if (!m.visible) return;
          const e = 1 - Math.pow(1 - q, 3);           // s'ouvre vite puis ralentit
          m.scale.setScalar(1 + 18 * e);
          m.position.addScaledVector(m.userData.dir, dt * 9);
          m.material.opacity = 0.6 * (1 - q) * (1 - q);
        });
      }
    };
  }

  // Étincelles de la morsure : une gerbe qui jaillit dans toutes les directions au claquement des crocs.
  function createSparks(THREE, scene) {
    const n = 90, geo = new THREE.BufferGeometry();
    const pos = new Float32Array(n * 3), vel = new Float32Array(n * 3), alpha = new Float32Array(n), age = new Float32Array(n).fill(9);
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("alpha", new THREE.BufferAttribute(alpha, 1));
    const mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uColor: { value: new THREE.Color(1, 0.8, 0.5) }, uScale: { value: 1 } },
      vertexShader: "attribute float alpha; varying float vA; uniform float uScale; void main(){ vA = alpha;" +
        "vec4 mv = modelViewMatrix * vec4(position,1.0); gl_PointSize = uScale * 75.0 / -mv.z; gl_Position = projectionMatrix * mv; }",
      fragmentShader: "uniform vec3 uColor; varying float vA; void main(){ float r = length(gl_PointCoord - 0.5);" +
        "float a = smoothstep(0.5, 0.0, r) * vA; gl_FragColor = vec4(uColor * (1.0 + 2.0 * smoothstep(0.25, 0.0, r)) * a, a); }"
    });
    const pts = new THREE.Points(geo, mat);
    pts.frustumCulled = false;
    scene.add(pts);
    return {
      trigger: function (origin, color) {
        mat.uniforms.uColor.value.set(color).convertSRGBToLinear();
        for (let i = 0; i < n; i++) {
          age[i] = 0;
          pos[i * 3] = origin.x; pos[i * 3 + 1] = origin.y; pos[i * 3 + 2] = origin.z;
          const u = Math.random() * 2 - 1, th = Math.random() * Math.PI * 2, k = Math.sqrt(1 - u * u), sp = 8 + Math.random() * 12;
          vel[i * 3] = k * Math.cos(th) * sp; vel[i * 3 + 1] = u * sp + 4; vel[i * 3 + 2] = k * Math.sin(th) * sp;
        }
      },
      update: function (dt) {
        for (let i = 0; i < n; i++) {
          age[i] += dt;
          const q = age[i] / 0.45;
          if (q >= 1) { alpha[i] = 0; continue; }
          vel[i * 3 + 1] -= 30 * dt;                            // retombent
          pos[i * 3] += vel[i * 3] * dt; pos[i * 3 + 1] += vel[i * 3 + 1] * dt; pos[i * 3 + 2] += vel[i * 3 + 2] * dt;
          alpha[i] = 1 - q;
        }
        geo.attributes.position.needsUpdate = true;
        geo.attributes.alpha.needsUpdate = true;
      },
      setScale: function (s) { mat.uniforms.uScale.value = s; }
    };
  }

  // Direction d'une cible vue par le dragon : angle à gauche (+) / droite et en haut (+) / bas, depuis la tête,
  // dans le repère du dragon (pivot = Object3D qui le porte, la tête regarde vers +Z).
  function aimAt(THREE, pivot, head, target) {
    const h = pivot.worldToLocal(head.getWorldPosition(new THREE.Vector3()));
    const t = pivot.worldToLocal(target.clone()).sub(h);
    return [Math.atan2(t.x, t.z), Math.atan2(t.y, Math.hypot(t.x, t.z))];
  }

  // Tremblement de la caméra : décalage aléatoire qui s'éteint. strength = force au départ (studs).
  function createShake() {
    let t = 99, strength = 0;
    return {
      trigger: function (s) { t = 0; strength = s; },
      // Renvoie le décalage à ajouter à la caméra pour cette image (0 quand c'est fini).
      offset: function (dt, out) {
        t += dt;
        const a = strength * Math.exp(-t * 4) * (t < 1.2 ? 1 : 0);
        return out.set((Math.random() - 0.5) * a, (Math.random() - 0.5) * a, (Math.random() - 0.5) * a);
      }
    };
  }

  global.DragonEffects = { createBreath: createBreath, createShockwave: createShockwave, createShake: createShake,
                           createSparks: createSparks, aimAt: aimAt,
                           mouthInHead: mouthInHead, PRESETS: PRESETS };
})(window);
