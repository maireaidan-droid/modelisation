--[[
DragonAnimator : anime le Dragon Long (modèle avec squelette Dragon_Long_v19_rig).

À placer dans : StarterPlayer > StarterPlayerScripts (LocalScript).
L'animation tourne chez chaque joueur (les os ne se répliquent pas depuis le serveur), c'est normal.

Le dragon est trouvé automatiquement :
  - tout Model qui porte le tag « DragonLong » (CollectionService), ou dont le nom commence par « Dragon_Long ».
Le mode se choisit avec l'attribut « Mode » du Model (réglable depuis un script serveur, il se réplique) :
  "Idle" (repos), "Walk" (marche), "Fly" (vol). Les changements de mode sont progressifs.

Ce qui est animé :
  - corps : piloté comme un serpent. On décrit la forme voulue de tout le corps (une vague qui glisse de la tête
    vers la queue, de même amplitude partout), puis on en déduit l'angle de chaque os. Le corps est recentré
    pour que tête, milieu et queue ondulent ensemble. En vol : longue vague souple, un peu en spirale ;
  - tête : suit la vague en plus calme, regarde autour d'elle au repos, mâchoire qui respire ;
  - yeux : la pupille glisse sur l'œil par petits sauts rapides (le regard), la tête suit ; clignements avec de vraies paupières (haut et bas) qui glissent sur l'œil :
    fermeture rapide, réouverture plus lente avec un petit rebond, parfois double, parfois lent au repos ;
  - crinière, moustaches, barbichette : flottent, plus fort en vol ;
  - pattes : marche en diagonale, repliées vers l'arrière en vol ;
  - actions (attribut « Action » du Model, réglé par un script serveur) : "Roar" (rugissement), "Bite" (morsure ;
    elle vise la position donnée par l'attribut « Target » (Vector3) s'il existe, sinon tout droit),
    "Breath" (souffle, avec des particules qui sortent de la gueule). Le rugissement lance une onde de choc et fait
    trembler la caméra des joueurs proches. Pour relancer la même action, ajoute un
    numéro après un # : "Roar#1", "Roar#2"… Style du souffle : attribut « BreathStyle » = "fire" (par défaut),
    "ice", "gold" ou "void" ;
  - virages : calculés tout seuls d'après la rotation du Model ; le corps se courbe dans le virage, la tête
    regarde à l'intérieur et, en vol, le dragon s'incline ;
  - mort : Mode = "Dead". Il s'effondre sur le flanc, se recourbe, ferme les yeux. Remettre "Idle" pour le relever ;
  - Mythique (Dragon_Long_v19_neant_rig) : les cristaux flottants (os Crest1 à Crest8) montent et descendent,
    et une vague de lumière court des cornes à la queue (parties Crest1…, Crack1…, BellyGlow1…, Horns, Eyes).
    Les autres dragons n'ont pas ces os ni ces parties : rien ne se passe pour eux.
]]

local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")

local TAG = "DragonLong"
local MAX_DISTANCE = 400 -- au-delà, on n'anime pas (économie)
local BLINK_UP = 1.449  -- fermeture de la paupière du haut (rad, elle glisse vers le bas sur l'œil)
local BLINK_LOW = 0.349 -- la paupière du bas remonte à sa rencontre
local EYE_L, EYE_D = 0.78, 0.247 -- demi-longueur et profondeur de l'œil (studs)
-- Course de la pupille sur l'œil (studs) : moins vers l'avant, où l'œil s'enfonce sous l'arcade près du nez.
local GAZE_FWD, GAZE_BACK, GAZE_Y = 0.15, 0.34, 0.07
local PUPIL_FWD_L, PUPIL_FWD_R = -1, 1 -- sens « vers l'avant » de l'axe X de chaque pupille
local SEG = 0.8         -- longueur du corps par pas de colonne (studs)
local KAPPA = 0.11      -- nombre d'onde : ~1,3 vague sur toute la longueur du corps
local PULSE_SEGMENTS, PULSE_STEP = 8, 0.6 -- Mythique : tronçons de la vague de lumière, décalage entre deux
local WHITE, LILAC = Color3.new(1, 1, 1), Color3.fromHex("#C9A2FF")

-- up / side : amplitude de la vague verticale / latérale (rad) ; speed : vitesse de la vague (rad/s) ;
-- helix : décalage entre les deux (pi/2 = chaque anneau décrit un cercle, le corps s'enroule en spirale) ;
-- center : recentrage du corps (1 = tout le corps ondule autour de son milieu, 0 = ancré au poitrail).
local MODES = {
	Idle = { up = 0.03, side = 0.06, speed = 1.2, helix = 0, center = 0, tuck = 0, walk = 0, mane = 0.12, maneSpeed = 1.6,
		jaw = 0.04, bob = 0.15, bank = 0, head = 0.6, dead = 0 },
	Walk = { up = 0.02, side = 0.13, speed = 3.4, helix = 0, center = 0, tuck = 0, walk = 1, mane = 0.2, maneSpeed = 3.2,
		jaw = 0.07, bob = 0.2, bank = 0, head = 0.5, dead = 0 },
	Fly = { up = 0.34, side = 0.16, speed = 2.0, helix = 1.57, center = 1, tuck = 1, walk = 0, mane = 0.42, maneSpeed = 5,
		jaw = 0.12, bob = 0.8, bank = 0.1, head = 0.45, dead = 0 },
	-- Mort : le corps cesse d'onduler, s'effondre sur le flanc en se courbant, yeux fermés, pattes molles.
	Dead = { up = 0, side = 0, speed = 0.3, helix = 0, center = 0, tuck = 0, walk = 0, mane = 0.03, maneSpeed = 0.8,
		jaw = 0, bob = 0, bank = 0, head = 1, dead = 1 },
}

-- Actions ponctuelles : durée en secondes.
local ACTIONS = { Roar = 3.3, Bite = 1.6, Breath = 3.2 }
-- Instant fort de chaque action (cri du rugissement, claquement de la morsure) : effets et caméra.
local BURSTS = { Roar = 0.62, Bite = 0.52 }
local TURN_CURVE = 0.027 -- courbure du corps (rad par pas de colonne) pour 1 rad/s de virage
local DEAD_DROP = 3.6    -- le dragon couché sur le flanc : le poitrail descend de tant de studs
local MID = 34           -- milieu du corps (pas de colonne) : le corps se courbe autour de ce point
local BREATH_STYLES = {  -- couleurs du souffle : début, milieu, fin
	fire = { "#FFF299", "#FF7314", "#731008" },
	ice = { "#F2FFFF", "#73E6FF", "#2659BF" },
	gold = { "#FFFFD9", "#FFC740", "#B3660D" },
	void = { "#FFD9FF", "#F240D9", "#4D149A" },
}

local function ramp(t, a, b) -- 0 avant a, 1 après b, transition douce entre les deux
	local x = math.clamp((t - a) / (b - a), 0, 1)
	return x * x * (3 - 2 * x)
end

-- Pose d'une action à l'instant t (voir demo/animator.js, même calcul).
local function actionPose(name, t)
	local o = { rear = 0, pitch = 0, yaw = 0, jaw = 0, push = 0, lift = 0, mane = 0, lash = 0, breath = 0,
		cry = 0, shiver = 0, eyes = 0, sweep = 0, coil = 0, aim = 0 }
	if name == "Roar" then
		-- 1. Se ramasse : tête basse, poitrail en arrière, gueule fermée.
		local crouch = ramp(t, 0, 0.45) * (1 - ramp(t, 0.5, 0.65))
		-- 2. Explose : cou dressé, tête projetée en avant vers l'ennemi, gueule grande ouverte.
		local cry = ramp(t, 0.5, 0.68) * (1 - ramp(t, 2.1, 2.7))
		local high = ramp(t, 0.5, 0.7) * (1 - ramp(t, 2.6, 3.3)) -- garde la tête haute un moment après
		-- 3. Secousse forte au début qui s'amortit.
		local k = math.max(0, t - 0.68)
		local shake = 0.2 * math.exp(-k * 2.6) * math.sin(k * 24) * cry
		-- 4. Petit souffle par les narines à la fin : la tête donne un coup sec.
		local snort = ramp(t, 2.85, 2.92) * (1 - ramp(t, 2.95, 3.15))
		o.rear = -0.3 * crouch + 0.4 * high
		o.pitch = 0.22 * crouch + 0.08 * cry - 0.12 * high * (1 - cry) + 0.1 * snort
		o.push = -0.8 * crouch + 1.1 * cry
		o.lift = -0.5 * crouch + 0.35 * high
		o.jaw, o.yaw = 1.0 * cry, shake
		o.mane, o.lash = 0.8 * cry + 0.2 * high, 0.12 * cry
		o.cry, o.shiver, o.eyes, o.sweep = cry, 0.035 * cry, cry, cry
	elseif name == "Bite" then
		-- Arrêt net à l'impact : le temps de la pose se fige 70 ms juste après le claquement.
		local tt = (t < 0.53) and t or ((t < 0.6) and 0.53 or (t - 0.07))
		-- 1. S'arme comme un serpent : cou replié en S, tête en arrière, crocs visibles, yeux fixés sur la cible.
		local coil = ramp(tt, 0, 0.3) * (1 - ramp(tt, 0.34, 0.44))
		-- 2. Frappe : tout l'avant du corps se projette, gueule ouverte au maximum juste avant l'impact.
		local strike = ramp(tt, 0.34, 0.5) * (1 - ramp(tt, 0.62, 1.3))
		-- 3. Petit rebond en arrière après l'impact.
		local recoil = ramp(tt, 0.53, 0.62) * (1 - ramp(tt, 0.62, 0.85))
		-- 4. Retour menaçant : tête basse, babines relevées, petit grognement.
		local snarl = ramp(tt, 0.6, 0.8) * (1 - ramp(tt, 1.25, 1.53))
		local open = ramp(tt, 0.3, 0.46) * (1 - ramp(tt, 0.48, 0.52))
		local bounce = ramp(tt, 0.52, 0.56) * (1 - ramp(tt, 0.6, 0.7)) -- la mâchoire rebondit après le claquement
		o.rear = 0.4 * coil - 0.25 * strike + 0.1 * snarl
		o.pitch = -0.12 * coil + 0.22 * strike - 0.12 * recoil + 0.12 * snarl
		o.push = -1.1 * coil + 2.6 * strike - 0.5 * recoil
		o.lift = -0.25 * coil + 0.1 * strike
		o.jaw = 0.15 * coil + 1.0 * open + 0.15 * bounce + 0.18 * snarl
		o.yaw = 0.02 * math.sin(t * 45) * snarl
		o.mane = 0.25 * coil + 0.35 * strike + 0.2 * snarl
		o.eyes = 0.7 * math.max(coil, strike)
		o.coil = coil
		o.aim = ramp(tt, 0, 0.3) * (1 - ramp(tt, 1.0, 1.5))
	elseif name == "Breath" then
		-- Inspire (cou dressé, tête en arrière), puis souffle longtemps en balayant devant lui.
		local inhale = ramp(t, 0, 0.9) * (1 - ramp(t, 0.9, 1.15))
		local blow = ramp(t, 1.0, 1.2) * (1 - ramp(t, 2.6, 3.1))
		o.rear, o.pitch = 0.5 * inhale + 0.1 * blow, -0.3 * inhale + 0.18 * blow
		o.jaw, o.yaw = 0.1 * inhale + 0.85 * blow, 0.25 * math.sin((t - 1.1) * 2.4) * blow
		o.push, o.lift, o.mane = -0.5 * inhale + 0.4 * blow, 0.3 * inhale, 0.4 * inhale + 0.3 * blow
		o.breath = ramp(t, 1.05, 1.25) * (1 - ramp(t, 2.5, 2.9))
	end
	return o
end

-- Colonne, de la tête à la queue : { os, position le long du corps (pas de colonne), parent }.
local SPINE = { { "Head", 0, "Neck" }, { "Neck", 5, "Neck2" }, { "Neck2", 10, "Root" }, { "Root", 14, nil } }
for k = 1, 14 do
	table.insert(SPINE, { string.format("S%02d", k), 14 + 4 * k, k == 1 and "Root" or string.format("S%02d", k - 1) })
end
local BY_NAME = {}
for _, b in ipairs(SPINE) do
	BY_NAME[b[1]] = b
end
-- Ordre parent → enfant (pour cumuler les positions depuis le poitrail).
local ORDER = { BY_NAME.Root, BY_NAME.Neck2, BY_NAME.Neck, BY_NAME.Head }
for k = 5, #SPINE do
	table.insert(ORDER, SPINE[k])
end
local LEGS = { LegFL = { 0, 14 }, LegBR = { 0, 42 }, LegFR = { math.pi, 14 }, LegBL = { math.pi, 42 } }

local rng = Random.new()
local dragons = {} -- [Model] = état

local function collectBones(model)
	-- Un même os peut exister dans plusieurs MeshParts selon l'import : on les anime tous.
	local bones = {}
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("Bone") then
			bones[d.Name] = bones[d.Name] or {}
			table.insert(bones[d.Name], d)
		end
	end
	return bones
end

-- Parties qui s'allument au passage de la vague (Mythique) : { part, tronçon, couleur de repos, couleur au pic, force }.
local function collectGlow(model)
	local list, mythic = {}, false
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			local kind, n = string.match(d.Name, "^(%a+)(%d+)$")
			if kind == "Crest" then
				mythic = true
				table.insert(list, { d, tonumber(n), d.Color, WHITE, 0.55 })
			elseif kind == "Crack" then
				table.insert(list, { d, tonumber(n), d.Color, WHITE, 0.6 })
			elseif kind == "BellyGlow" then
				table.insert(list, { d, tonumber(n), d.Color, LILAC, 0.7 })
			elseif d.Name == "Horns" then
				table.insert(list, { d, 0, d.Color, WHITE, 0.4 })
			elseif d.Name == "Eyes" then
				table.insert(list, { d, 0, d.Color, WHITE, 0.5 })
			end
		end
	end
	-- Seul le Mythique (qui a des tronçons Crest) pulse : les cornes et les yeux des autres dragons ne changent pas.
	return mythic and list or {}
end

local function newState(model)
	local p = {}
	for k, v in pairs(MODES.Idle) do
		p[k] = v
	end
	return {
		model = model, bones = collectBones(model), glow = collectGlow(model), p = p,
		phase = rng:NextNumber(0, 6), step = 0, flutter = 0, pulse = 0, t = 0,
		action = nil, actionT = 0, breath = 0, cry = 0, burst = nil, aimYaw = 0, aimPitch = 0, turn = 0, deadT = 0, yaw = nil,
		blinkIn = rng:NextNumber(1, 4), blink = nil,
		headLook = 0, headTarget = 0,
		gazeX = 0, gazeY = 0, gazeTx = 0, gazeTy = 0, gazeIn = 1, microX = 0, microY = 0, microIn = 0.5,
	}
end

-- Rotation (X puis Y puis Z, comme CFrame.Angles) + décalage le long des axes de l'os.
local function setBone(st, name, rx, ry, rz, ty, tz, tx)
	local list = st.bones[name]
	if not list then
		return
	end
	local cf = CFrame.new(tx or 0, ty or 0, tz or 0) * CFrame.Angles(rx, ry, rz)
	for _, b in ipairs(list) do
		b.Transform = cf
	end
end

-- Forme du corps : angle de la colonne (haut/bas, côté) à la position s.
local function bodyAngles(st, s)
	local p = st.p
	local env = 0.8 + 0.3 * s / 70
	local a = KAPPA * s - st.phase
	return p.up * env * math.sin(a), p.side * env * math.sin(a + p.helix)
end

-- Vague de lumière : 0 (éteint) à 1 (pic) pour le tronçon c (0 = cornes, 1 à 8 de la tête vers la queue).
local function pulseAt(st, c)
	return math.max(0, math.sin(st.pulse - PULSE_STEP * c)) ^ 6
end

-- Fermeture des paupières (0 = ouvert, 1 = fermé) à l'instant tt d'un clignement b.
local function closeOnce(b, tt)
	if tt <= 0 then
		return 0
	end
	if tt < b.close then
		local x = tt / b.close
		return x * x -- accélère en fermant
	end
	if tt < b.close + b.hold then
		return 1
	end
	local y = (tt - b.close - b.hold) / b.open
	if y >= 1 then
		return 0
	end
	local c1 = 1.2 -- réouverture avec léger rebond
	local c3, z = c1 + 1, y - 1
	return 1 - (1 + c3 * z * z * z + c1 * z * z)
end

local function closure(b, tt, one)
	if b.twice and tt > one + 0.08 then
		return closeOnce(b, tt - one - 0.08)
	end
	return closeOnce(b, tt)
end

-- Direction de la cible (attribut « Target », une position Vector3 dans le monde) vue depuis la tête du
-- dragon, dans son propre repère (la tête regarde vers +Z) : angle à gauche (+) / droite, en haut (+) / bas.
local function aimAt(st)
	local target = st.model:GetAttribute("Target")
	local head = st.bones.Head and st.bones.Head[1]
	if typeof(target) ~= "Vector3" or not head then
		return 0, 0
	end
	local v = st.model:GetPivot():VectorToObjectSpace(target - head.WorldPosition)
	return math.atan2(v.X, v.Z), math.atan2(v.Y, math.sqrt(v.X * v.X + v.Z * v.Z))
end

-- Lance une action ponctuelle (Roar, Bite, Breath). Ignorée si le dragon est mort.
-- La morsure vise la cible donnée par l'attribut « Target » (sinon, tout droit).
local function play(st, name)
	if ACTIONS[name] and st.p.dead < 0.5 then
		st.action, st.actionT = name, 0
		local y, p = 0, 0
		if name == "Bite" then
			y, p = aimAt(st)
		end
		st.aimYaw, st.aimPitch = math.clamp(y, -0.8, 0.8), math.clamp(p, -0.5, 0.5)
	end
end

-- Vitesse de virage (rad/s, positif = vers la gauche) d'après la rotation du Model. La tête regarde vers +Z.
local function turnRate(st, dt)
	local look = -st.model:GetPivot().LookVector
	local yaw = math.atan2(look.X, look.Z)
	local prev = st.yaw or yaw
	st.yaw = yaw
	local d = math.atan2(math.sin(yaw - prev), math.cos(yaw - prev))
	if dt <= 0 or math.abs(d) > 0.5 then
		return 0 -- téléporté ou demi-tour instantané : ce n'est pas un virage
	end
	return d / dt
end

local function update(st, dt, turn)
	local mode = st.model:GetAttribute("Mode")
	local target = MODES[mode] or MODES.Idle
	mode = MODES[mode] and mode or "Idle"
	st.t += dt
	local p = st.p
	local k = math.min(1, dt * 1.8)
	for key, v in pairs(target) do
		p[key] += (v - p[key]) * k
	end
	st.phase += dt * p.speed
	st.step += dt * 4.2 * p.walk
	st.flutter += dt * p.maneSpeed
	st.pulse += dt * (1.3 + 1.7 * p.tuck) -- vague de lumière (Mythique) : plus rapide en vol
	st.turn += (math.clamp(turn or 0, -1.5, 1.5) - st.turn) * math.min(1, dt * 3)
	st.deadT = (mode == "Dead") and (st.deadT + dt) or 0
	local act = actionPose("", 0)
	if st.action then
		st.actionT += dt
		if st.actionT >= ACTIONS[st.action] or p.dead > 0.5 then
			st.action = nil
		else
			act = actionPose(st.action, st.actionT)
		end
	end
	st.breath = act.breath
	st.cry = act.cry
	-- Instant fort de l'action (cri, claquement) : nom de l'action pendant une seule image, sinon nil.
	local bt = st.action and BURSTS[st.action]
	st.burst = (bt and st.actionT >= bt and st.actionT - dt < bt) and st.action or nil
	local aimY, aimP = st.aimYaw * act.aim, st.aimPitch * act.aim
	local d = p.dead
	-- Frisson quand il tombe : une dernière vague rapide qui s'éteint.
	local shiver = 0.1 * math.sin(st.deadT * 16) * math.exp(-st.deadT * 2.2) * d

	-- 1. Orientation voulue de chaque morceau de colonne.
	local ax, ay = {}, {}
	for _, b in ipairs(SPINE) do
		ax[b[1]], ay[b[1]] = bodyAngles(st, b[2])
	end
	ax.Head *= p.head -- la tête suit la vague, en plus calme
	ay.Head *= p.head
	-- Poses ajoutées à la forme du corps : cou dressé (actions), courbe du virage, corps recourbé (mort),
	-- queue qui fouette (rugissement). Couché sur le flanc, l'axe « haut / bas » de la colonne devient
	-- horizontal : c'est lui qui recourbe le corps en croissant sur le sol (nul au poitrail).
	for _, b in ipairs(SPINE) do
		local name, sp = b[1], b[2]
		local front = 1 - ramp(sp, 4, 20) -- 1 pour la tête et le cou, 0 dès le poitrail
		ax[name] += -act.rear * front + 0.022 * d * (14 - sp) - 0.5 * aimP * front -- le cou vise la cible
		ay[name] += TURN_CURVE * st.turn * (MID - sp) * (1 - d) + shiver * math.sin(sp * 0.3)
			+ act.lash * ramp(sp, 30, 60) * math.sin(st.t * 9 - sp * 0.15)
			+ act.shiver * math.sin(st.t * 38 - sp * 0.4) -- frisson du cri, de la tête à la queue
			+ act.yaw * 0.5 * front -- le cou suit la secousse de la tête
			+ 0.6 * aimY * front -- le cou se tourne vers la cible
			+ 0.3 * act.coil * front * math.sin(sp * 0.45) -- cou replié en S avant de frapper
	end

	-- 2. Recentrage : position (haut/bas, côté) de chaque articulation par rapport au poitrail.
	local py, px = { Root = 0 }, { Root = 0 }
	for _, b in ipairs(ORDER) do
		local name, parent = b[1], b[3]
		if parent then
			local pb = BY_NAME[parent]
			local len = math.abs(b[2] - pb[2]) * SEG
			local dir = b[2] > pb[2] and 1 or -1 -- vers la queue : +1
			py[name] = py[parent] + dir * len * math.sin(ax[parent])
			px[name] = px[parent] - dir * len * math.sin(ay[parent])
		end
	end
	local sumY, sumX = 0, 0
	for _, b in ipairs(SPINE) do
		sumY += py[b[1]]
		sumX += px[b[1]]
	end
	local cy, cx = -sumY / #SPINE * p.center, -sumX / #SPINE * p.center

	-- 3. Angles relatifs (os par rapport à son parent).
	for _, b in ipairs(SPINE) do
		local name, parent = b[1], b[3]
		if name == "Root" then
			setBone(st, "Root", ax.Root, ay.Root, p.bank * math.sin(st.phase * 0.3) - 0.6 * st.turn * p.tuck - 1.35 * d,
				cy + p.bob * math.sin(st.phase * 0.4 + 1) + 0.12 * p.walk * math.abs(math.sin(st.step)) + act.lift
					- DEAD_DROP * d, act.push, cx)
		elseif name ~= "Head" then
			setBone(st, name, ax[name] - ax[parent], ay[name] - ay[parent], 0)
		end
	end

	-- Regard : la pupille saute vite vers un nouveau point (~80 ms), s'y fixe, avec de petits micro-mouvements.
	-- Au repos le dragon regarde partout et la tête suit le regard avec un temps de retard ; en marche et en vol
	-- il regarde surtout devant. Un grand changement de regard s'accompagne parfois d'un clignement.
	st.gazeIn -= dt
	if st.gazeIn <= 0 then
		local nx = (mode == "Idle") and rng:NextNumber(-1, 1) or rng:NextNumber(0.1, 1)
		local ny = (mode == "Idle") and rng:NextNumber(-1, 1) or rng:NextNumber(-0.4, 0.4)
		if math.abs(nx - st.gazeTx) > 0.8 and not st.blink and rng:NextNumber(0, 1) < 0.3 then
			st.blink = { t = 0, close = 0.07, hold = 0.04, open = 0.15, twice = false }
		end
		st.gazeTx, st.gazeTy = nx, ny
		st.gazeIn = rng:NextNumber(0.6, 3)
		st.headTarget = (mode == "Idle" and not st.action) and rng:NextNumber(-0.25, 0.25) or 0
	end
	st.microIn -= dt
	if st.microIn <= 0 then
		st.microIn = rng:NextNumber(0.25, 0.7)
		st.microX = rng:NextNumber(-0.07, 0.07)
		st.microY = rng:NextNumber(-0.07, 0.07)
	end
	local gk = math.min(1, dt * 28)
	st.gazeX += (st.gazeTx + st.microX - st.gazeX) * gk
	st.gazeY += (st.gazeTy + st.microY - st.gazeY) * gk
	st.headLook += (st.headTarget - st.headLook) * math.min(1, dt * 1.5)

	-- Tête : suit la vague (en plus calme), suit le regard avec retard et lève ou baisse un peu le nez avec lui.
	-- En virage, la tête regarde à l'intérieur ; mort, elle retombe, gueule entrouverte.
	setBone(st, "Head", ax.Head - ax.Neck + (0.04 * math.sin(st.t * 0.9) - 0.06 * st.gazeY) * (1 - d) + act.pitch + 0.25 * d
		- 0.5 * aimP, ay.Head - ay.Neck + st.headLook * (1 - d) + act.yaw + 0.45 * st.turn * (1 - d) + 0.4 * aimY, 0)
	setBone(st, "Jaw", math.max(p.jaw * (0.6 + 0.4 * math.sin(st.t * 1.3)), act.jaw) + 0.2 * d, 0, 0)

	-- Clignement : fermeture très rapide, courte pause, réouverture plus lente avec un léger rebond.
	-- Parfois un double clignement, et au repos parfois un clignement lent et paresseux.
	-- L'œil droit suit le gauche avec 15 ms de retard.
	st.blinkIn -= dt
	if st.blinkIn <= 0 and not st.blink and not st.action then
		if mode == "Idle" and rng:NextNumber(0, 1) < 0.2 then
			st.blink = { t = 0, close = 0.3, hold = 0.25, open = 0.45, twice = false }
		else
			st.blink = { t = 0, close = 0.07, hold = 0.04, open = 0.15, twice = rng:NextNumber(0, 1) < 0.15 }
		end
		st.blinkIn = rng:NextNumber(2.5, 6)
	end
	local lidL, lidR = 0, 0
	if st.blink then
		local b = st.blink
		b.t += dt
		local one = b.close + b.hold + b.open
		local total = b.twice and (2 * one + 0.08) or one
		lidL = closure(b, b.t, one)
		lidR = closure(b, b.t - 0.015, one)
		if b.t > total + 0.05 then
			st.blink = nil
		end
	end
	-- Mort : yeux fermés ; rugissement : paupières remontées, yeux grands ouverts.
	lidL = lidL * (1 - d) + d - 0.12 * act.eyes
	lidR = lidR * (1 - d) + d - 0.12 * act.eyes
	setBone(st, "Lid_L", BLINK_UP * lidL, 0, 0)
	setBone(st, "Lid_R", BLINK_UP * lidR, 0, 0)
	setBone(st, "LidLow_L", -BLINK_LOW * math.max(0, lidL), 0, 0)
	setBone(st, "LidLow_R", -BLINK_LOW * math.max(0, lidR), 0, 0)
	-- Pupilles : glissent sur l'œil (avant / arrière et un peu haut / bas) en suivant sa courbure.
	local g = math.clamp(st.gazeX, -1, 1)
	local gx = g * (g > 0 and GAZE_FWD or GAZE_BACK)
	local gy = math.clamp(st.gazeY, -1, 1) * GAZE_Y
	local depth = EYE_D * (math.sqrt(math.max(0, 1 - (gx / EYE_L) ^ 2)) - 1)
	setBone(st, "Pupil_L", 0, 0, 0, gy, depth, PUPIL_FWD_L * gx)
	setBone(st, "Pupil_R", 0, 0, 0, gy, depth, PUPIL_FWD_R * gx)

	-- Crinière, moustaches, barbichette : flottent, se soulèvent en vol et traînent derrière les mouvements
	-- de la tête.
	local f, m, lift = st.flutter, p.mane + 0.25 * act.mane, 0.22 * p.tuck + act.mane
	local drag, dragY = -0.8 * (ax.Neck - ax.Neck2), -0.8 * (ay.Neck - ay.Neck2)
	setBone(st, "Mane_Top", lift + drag + 0.5 * m * math.sin(f), dragY + m * math.sin(f * 1.3 + 1), 0)
	setBone(st, "Mane_L", lift + drag + 0.6 * m * math.sin(f + 2), dragY + m * math.sin(f * 1.1 + 0.5), 0)
	setBone(st, "Mane_R", lift + drag + 0.6 * m * math.sin(f + 2.6), dragY - m * math.sin(f * 1.1 + 1.2), 0)
	-- Rugissement : moustaches et barbichette plaquées vers l'arrière par le souffle du cri.
	local sweep = -0.6 * act.sweep
	setBone(st, "Whisker_L", 0.8 * m * math.sin(f * 0.9) + drag + sweep, m * math.sin(f * 0.7 + 0.3) + dragY, 0)
	setBone(st, "Whisker_R", 0.8 * m * math.sin(f * 0.9 + 1) + drag + sweep, -m * math.sin(f * 0.7 + 1.1) + dragY, 0)
	setBone(st, "Beard", 0.5 * m * math.sin(f * 0.8) + drag - 0.4 * act.sweep, 0.4 * m * math.sin(f * 1.2), 0)

	-- Cristaux flottants (Mythique) : montent et descendent doucement, et se soulèvent un peu quand la vague passe.
	for c = 1, PULSE_SEGMENTS do
		setBone(st, "Crest" .. c, 0.06 * math.sin(st.t * 1.3 + c * 0.9), 0, 0.05 * math.sin(st.t * 1.1 + c * 1.7),
			0.35 * math.sin(st.t * 1.6 + c * 0.7) + 0.3 * pulseAt(st, c), 0)
	end
	-- Vague de lumière : chaque partie passe de sa couleur de repos à une couleur claire (en Neon, elle brille).
	for _, gl in ipairs(st.glow) do
		gl[1].Color = gl[3]:Lerp(gl[4], gl[5] * pulseAt(st, gl[2]))
	end

	-- Pattes : marche en diagonale ; en vol, repliées et elles suivent doucement la vague du corps.
	for leg, info in pairs(LEGS) do
		local ph = st.step + info[1]
		local sw, up = math.sin(ph), math.max(0, math.cos(ph))
		local flow = 0.5 * (bodyAngles(st, info[2] + 6)) * p.tuck
		-- Mort : pattes molles, un peu écartées du corps.
		setBone(st, leg .. "_Upper", -0.45 * sw * p.walk + 0.9 * p.tuck + flow + 0.45 * d, 0, 0)
		setBone(st, leg .. "_Fore", 0.6 * up * p.walk + 0.6 * p.tuck + flow + 0.35 * d, 0, 0)
		setBone(st, leg .. "_Foot", -0.35 * up * p.walk - 0.4 * p.tuck - 0.2 * d, 0, 0)
	end
end

-- Souffle : un ParticleEmitter (créé chez le joueur seulement) dans l'os de la mâchoire, qui projette les
-- particules vers l'avant de la tête. Son débit suit st.breath (0 à 1).
local function updateBreath(st)
	local fx = st.breathFx
	if not fx then
		if st.breath <= 0 then
			return
		end
		local jaw = st.bones.Jaw and st.bones.Jaw[1]
		if not jaw then
			return
		end
		fx = Instance.new("ParticleEmitter")
		fx.Name = "DragonBreath"
		fx.EmissionDirection = Enum.NormalId.Back -- +Z de l'os = vers l'avant de la gueule
		fx.SpreadAngle = Vector2.new(14, 14)
		fx.Speed = NumberRange.new(26, 36)
		fx.Drag = 0.9
		fx.Acceleration = Vector3.new(0, 6, 0)
		fx.Lifetime = NumberRange.new(0.85, 1.1)
		fx.LightEmission = 1
		fx.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 4) })
		fx.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
		fx.Rate = 0
		fx.Parent = jaw
		st.breathFx = fx
	end
	local style = BREATH_STYLES[st.model:GetAttribute("BreathStyle") or "fire"] or BREATH_STYLES.fire
	if st.breathStyle ~= style then
		st.breathStyle = style
		fx.Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, Color3.fromHex(style[1])),
			ColorSequenceKeypoint.new(0.35, Color3.fromHex(style[2])),
			ColorSequenceKeypoint.new(1, Color3.fromHex(style[3])),
		})
	end
	fx.Rate = 300 * st.breath
	fx.Enabled = st.breath > 0.02
end

-- Rugissement : onde de choc (3 anneaux de petits blocs lumineux qui partent de la gueule et s'agrandissent)
-- et tremblement de la caméra du joueur s'il est assez près. Tout est créé chez le joueur seulement.
local SHOCK_COLORS = { fire = "#FFB070", ice = "#9FEFFF", gold = "#FFE08A", void = "#FF6FE4" }
local SHOCK_PIECES = 16
local shocks = {}
local shake = { t = 99, strength = 0 }

local function startRoarFx(st)
	local head = st.bones.Head and st.bones.Head[1]
	local jaw = st.bones.Jaw and st.bones.Jaw[1]
	if not head then
		return
	end
	local cf = head.WorldCFrame
	local fwd = -cf.LookVector -- l'avant de la tête est le +Z de l'os
	local origin = (jaw and jaw.WorldPosition or cf.Position) + fwd * 2
	local color = Color3.fromHex(SHOCK_COLORS[st.model:GetAttribute("BreathStyle") or "fire"] or SHOCK_COLORS.fire)
	local right = fwd:Cross(Vector3.yAxis)
	right = right.Magnitude > 0.01 and right.Unit or Vector3.xAxis
	local up = right:Cross(fwd).Unit
	for k = 0, 2 do
		local ring = { t = -0.13 * k, center = origin, fwd = fwd, right = right, up = up, parts = {} }
		for i = 1, SHOCK_PIECES do
			local part = Instance.new("Part")
			part.Anchored, part.CanCollide, part.CanQuery, part.CanTouch, part.CastShadow = true, false, false, false, false
			part.Material = Enum.Material.Neon
			part.Color = color
			part.Transparency = 1
			part.Size = Vector3.new(0.3, 0.3, 0.3)
			part.Parent = workspace
			ring.parts[i] = part
		end
		table.insert(shocks, ring)
	end
	-- La caméra tremble d'autant plus que le joueur est proche.
	local cam = workspace.CurrentCamera
	if cam then
		local dist = (cam.CFrame.Position - origin).Magnitude
		shake.t, shake.strength = 0, 0.9 * math.clamp(1 - dist / 90, 0, 1)
	end
end

local function updateShocks(dt)
	for idx = #shocks, 1, -1 do
		local ring = shocks[idx]
		ring.t += dt
		local q = ring.t / 0.95
		if q >= 1 then
			for _, part in ipairs(ring.parts) do
				part:Destroy()
			end
			table.remove(shocks, idx)
		elseif q > 0 then
			ring.center += ring.fwd * 9 * dt
			local radius = 1 + 18 * (1 - (1 - q) ^ 3) -- s'ouvre vite puis ralentit
			local len = 2 * math.pi * radius / SHOCK_PIECES * 0.8
			for i, part in ipairs(ring.parts) do
				local a = (i - 1) / SHOCK_PIECES * 2 * math.pi
				local dir = ring.right * math.cos(a) + ring.up * math.sin(a)
				local tangent = ring.up * math.cos(a) - ring.right * math.sin(a)
				local pos = ring.center + dir * radius
				part.Size = Vector3.new(0.35, 0.35, len)
				part.CFrame = CFrame.lookAt(pos, pos + tangent)
				part.Transparency = 1 - 0.6 * (1 - q) ^ 2
			end
		end
	end
end

-- Morsure : gerbe d'étincelles au claquement des crocs (émetteur ponctuel dans l'os de la mâchoire) et petite
-- secousse de la caméra.
local function startBiteFx(st)
	local jaw = st.bones.Jaw and st.bones.Jaw[1]
	if not jaw then
		return
	end
	local fx = st.biteFx
	if not fx then
		fx = Instance.new("ParticleEmitter")
		fx.Name = "DragonBiteSparks"
		fx.Rate = 0 -- seulement des gerbes ponctuelles (Emit)
		fx.EmissionDirection = Enum.NormalId.Back
		fx.SpreadAngle = Vector2.new(180, 180)
		fx.Speed = NumberRange.new(8, 20)
		fx.Acceleration = Vector3.new(0, -30, 0)
		fx.Lifetime = NumberRange.new(0.3, 0.5)
		fx.LightEmission = 1
		fx.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) })
		fx.Parent = jaw
		st.biteFx = fx
	end
	fx.Color = ColorSequence.new(Color3.fromHex(SHOCK_COLORS[st.model:GetAttribute("BreathStyle") or "fire"] or SHOCK_COLORS.fire))
	fx:Emit(40)
	local cam = workspace.CurrentCamera
	if cam then
		local dist = (cam.CFrame.Position - jaw.WorldPosition).Magnitude
		shake.t, shake.strength = 0, 0.35 * math.clamp(1 - dist / 60, 0, 1)
	end
end

RunService:BindToRenderStep("DragonRoarShake", Enum.RenderPriority.Camera.Value + 1, function(dt)
	shake.t += dt
	local cam = workspace.CurrentCamera
	if cam and shake.t < 1.2 and shake.strength > 0 then
		local a = shake.strength * math.exp(-shake.t * 4)
		cam.CFrame *= CFrame.new(rng:NextNumber(-a, a), rng:NextNumber(-a, a), rng:NextNumber(-a, a) * 0.5)
	end
end)

local function track(model)
	if model:IsA("Model") and not dragons[model] then
		dragons[model] = newState(model)
		-- Actions : « Roar », « Bite », « Breath » (éventuellement suivies de #numéro pour relancer la même).
		model:GetAttributeChangedSignal("Action"):Connect(function()
			local name = string.match(model:GetAttribute("Action") or "", "^(%a+)")
			if dragons[model] and name then
				play(dragons[model], name)
			end
		end)
		-- Si les os arrivent après le modèle (chargement en streaming), on les recompte.
		model.DescendantAdded:Connect(function(d)
			if d:IsA("Bone") and dragons[model] then
				dragons[model].bones = collectBones(model)
			elseif d:IsA("BasePart") and dragons[model] then
				dragons[model].glow = collectGlow(model)
			end
		end)
	end
end

local function isDragon(inst)
	return inst:IsA("Model") and (CollectionService:HasTag(inst, TAG) or string.sub(inst.Name, 1, 11) == "Dragon_Long")
end

for _, m in ipairs(CollectionService:GetTagged(TAG)) do
	track(m)
end
for _, d in ipairs(workspace:GetDescendants()) do
	if isDragon(d) then
		track(d)
	end
end
CollectionService:GetInstanceAddedSignal(TAG):Connect(track)
workspace.DescendantAdded:Connect(function(d)
	if isDragon(d) then
		track(d)
	end
end)

RunService.RenderStepped:Connect(function(dt)
	dt = math.min(dt, 0.1)
	updateShocks(dt)
	local cam = workspace.CurrentCamera
	for model, st in pairs(dragons) do
		if not model:IsDescendantOf(workspace) then
			dragons[model] = nil
		elseif cam and (model:GetPivot().Position - cam.CFrame.Position).Magnitude < MAX_DISTANCE then
			update(st, dt, turnRate(st, dt))
			updateBreath(st)
			if st.burst == "Roar" then
				startRoarFx(st)
			elseif st.burst == "Bite" then
				startBiteFx(st)
			end
		else
			st.yaw = nil -- trop loin : on repartira de zéro pour le calcul du virage
		end
	end
end)
