--[[
DragonAnimator : anime le Dragon Long (modèle avec squelette Dragon_Long_v18_rig).

À placer dans : StarterPlayer > StarterPlayerScripts (LocalScript).
L'animation tourne chez chaque joueur (les os ne se répliquent pas depuis le serveur), c'est normal.

Le dragon est trouvé automatiquement :
  - tout Model qui porte le tag « DragonLong » (CollectionService), ou dont le nom commence par « Dragon_Long ».
Le mode se choisit avec l'attribut « Mode » du Model (réglable depuis un script serveur, il se réplique) :
  "Idle" (repos), "Walk" (marche), "Fly" (vol). Les changements de mode sont progressifs.

Ce qui est animé :
  - corps : piloté comme un serpent. On décrit la forme voulue de tout le corps (une vague qui glisse de la tête
    vers la queue, de même amplitude partout), puis on en déduit l'angle de chaque os. Le corps est recentré
    pour que tête, milieu et queue ondulent ensemble. En vol : longue vague souple, un peu en spirale, et un
    tonneau lent de temps en temps ;
  - tête : suit la vague en plus calme, regarde autour d'elle au repos, mâchoire qui respire ;
  - yeux : regard qui se déplace, clignements au hasard ;
  - crinière, moustaches, barbichette : flottent, plus fort en vol ;
  - pattes : marche en diagonale, repliées vers l'arrière en vol.
]]

local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")

local TAG = "DragonLong"
local MAX_DISTANCE = 400 -- au-delà, on n'anime pas (économie)
local BLINK = 0.45      -- la paupière descend un peu (rad)…
local SINK = 0.75       -- …et l'œil s'enfonce dans l'orbite (studs) : l'œil paraît fermé
local SEG = 0.8         -- longueur du corps par pas de colonne (studs)
local KAPPA = 0.11      -- nombre d'onde : ~1,3 vague sur toute la longueur du corps

-- up / side : amplitude de la vague verticale / latérale (rad) ; speed : vitesse de la vague (rad/s) ;
-- helix : décalage entre les deux (pi/2 = chaque anneau décrit un cercle, le corps s'enroule en spirale) ;
-- center : recentrage du corps (1 = tout le corps ondule autour de son milieu, 0 = ancré au poitrail) ;
-- roll : 1 = tonneau lent de temps en temps.
local MODES = {
	Idle = { up = 0.03, side = 0.06, speed = 1.2, helix = 0, center = 0, tuck = 0, walk = 0, mane = 0.12, maneSpeed = 1.6,
		jaw = 0.04, bob = 0.15, bank = 0, roll = 0, head = 0.6 },
	Walk = { up = 0.02, side = 0.13, speed = 3.4, helix = 0, center = 0, tuck = 0, walk = 1, mane = 0.2, maneSpeed = 3.2,
		jaw = 0.07, bob = 0.2, bank = 0, roll = 0, head = 0.5 },
	Fly = { up = 0.34, side = 0.16, speed = 2.0, helix = 1.57, center = 1, tuck = 1, walk = 0, mane = 0.42, maneSpeed = 5,
		jaw = 0.12, bob = 0.8, bank = 0.1, roll = 1, head = 0.45 },
}

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

local function newState(model)
	local p = {}
	for k, v in pairs(MODES.Idle) do
		p[k] = v
	end
	return {
		model = model, bones = collectBones(model), p = p,
		phase = rng:NextNumber(0, 6), step = 0, flutter = 0, t = 0,
		blinkIn = rng:NextNumber(1, 4), blink = -1, rollIn = 6, roll = -1,
		look = 0, lookTarget = 0, lookIn = 1.5, headLook = 0, headTarget = 0,
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

local function update(st, dt)
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

	-- 1. Orientation voulue de chaque morceau de colonne.
	local ax, ay = {}, {}
	for _, b in ipairs(SPINE) do
		ax[b[1]], ay[b[1]] = bodyAngles(st, b[2])
	end
	ax.Head *= p.head -- la tête suit la vague, en plus calme
	ay.Head *= p.head

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

	-- 3. Tonneau lent, de temps en temps, en vol.
	st.rollIn -= dt * p.roll
	if st.rollIn <= 0 and st.roll < 0 and p.roll > 0.9 then
		st.roll = 0
		st.rollIn = rng:NextNumber(12, 18)
	end
	local rollAngle = 0
	if st.roll >= 0 then
		st.roll += dt / 3.5
		local r = math.min(1, st.roll)
		rollAngle = 2 * math.pi * r * r * (3 - 2 * r)
		if st.roll >= 1 then
			st.roll = -1
		end
	end

	-- 4. Angles relatifs (os par rapport à son parent).
	for _, b in ipairs(SPINE) do
		local name, parent = b[1], b[3]
		if name == "Root" then
			setBone(st, "Root", ax.Root, ay.Root, p.bank * math.sin(st.phase * 0.3) + rollAngle,
				cy + p.bob * math.sin(st.phase * 0.4 + 1) + 0.12 * p.walk * math.abs(math.sin(st.step)), 0, cx)
		elseif name ~= "Head" then
			setBone(st, name, ax[name] - ax[parent], ay[name] - ay[parent], 0)
		end
	end

	-- Tête : suit la vague (en plus calme) et regarde autour d'elle au repos.
	st.lookIn -= dt
	if st.lookIn <= 0 then
		st.lookIn = rng:NextNumber(1.5, 4)
		st.lookTarget = rng:NextNumber(-0.2, 0.2)
		st.headTarget = (mode == "Idle") and rng:NextNumber(-0.25, 0.25) or 0
	end
	st.look += (st.lookTarget - st.look) * math.min(1, dt * 6)
	st.headLook += (st.headTarget - st.headLook) * math.min(1, dt * 1.5)
	setBone(st, "Head", ax.Head - ax.Neck + 0.04 * math.sin(st.t * 0.9), ay.Head - ay.Neck + st.headLook, 0)
	setBone(st, "Jaw", p.jaw * (0.6 + 0.4 * math.sin(st.t * 1.3)), 0, 0)

	-- Clignement : fermeture rapide, réouverture un peu plus lente.
	st.blinkIn -= dt
	if st.blinkIn <= 0 and st.blink < 0 then
		st.blink = 0
		st.blinkIn = rng:NextNumber(2, 6)
	end
	local lid = 0
	if st.blink >= 0 then
		st.blink += dt
		if st.blink < 0.07 then
			lid = st.blink / 0.07
		else
			lid = math.max(0, 1 - (st.blink - 0.07) / 0.13)
		end
		if st.blink > 0.2 then
			st.blink = -1
		end
	end
	setBone(st, "Lid_L", BLINK * lid, 0, 0)
	setBone(st, "Lid_R", BLINK * lid, 0, 0)
	setBone(st, "Eye_L", 0, st.look, 0, 0, -SINK * lid)
	setBone(st, "Eye_R", 0, st.look, 0, 0, -SINK * lid)

	-- Crinière, moustaches, barbichette : flottent, se soulèvent en vol et traînent derrière les mouvements
	-- de la tête.
	local f, m, lift = st.flutter, p.mane, 0.22 * p.tuck
	local drag, dragY = -0.8 * (ax.Neck - ax.Neck2), -0.8 * (ay.Neck - ay.Neck2)
	setBone(st, "Mane_Top", lift + drag + 0.5 * m * math.sin(f), dragY + m * math.sin(f * 1.3 + 1), 0)
	setBone(st, "Mane_L", lift + drag + 0.6 * m * math.sin(f + 2), dragY + m * math.sin(f * 1.1 + 0.5), 0)
	setBone(st, "Mane_R", lift + drag + 0.6 * m * math.sin(f + 2.6), dragY - m * math.sin(f * 1.1 + 1.2), 0)
	setBone(st, "Whisker_L", 0.8 * m * math.sin(f * 0.9) + drag, m * math.sin(f * 0.7 + 0.3) + dragY, 0)
	setBone(st, "Whisker_R", 0.8 * m * math.sin(f * 0.9 + 1) + drag, -m * math.sin(f * 0.7 + 1.1) + dragY, 0)
	setBone(st, "Beard", 0.5 * m * math.sin(f * 0.8) + drag, 0.4 * m * math.sin(f * 1.2), 0)

	-- Pattes : marche en diagonale ; en vol, repliées et elles suivent doucement la vague du corps.
	for leg, info in pairs(LEGS) do
		local ph = st.step + info[1]
		local sw, up = math.sin(ph), math.max(0, math.cos(ph))
		local flow = 0.5 * (bodyAngles(st, info[2] + 6)) * p.tuck
		setBone(st, leg .. "_Upper", -0.45 * sw * p.walk + 0.9 * p.tuck + flow, 0, 0)
		setBone(st, leg .. "_Fore", 0.6 * up * p.walk + 0.6 * p.tuck + flow, 0, 0)
		setBone(st, leg .. "_Foot", -0.35 * up * p.walk - 0.4 * p.tuck, 0, 0)
	end
end

local function track(model)
	if model:IsA("Model") and not dragons[model] then
		dragons[model] = newState(model)
		-- Si les os arrivent après le modèle (chargement en streaming), on les recompte.
		model.DescendantAdded:Connect(function(d)
			if d:IsA("Bone") and dragons[model] then
				dragons[model].bones = collectBones(model)
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
	local cam = workspace.CurrentCamera
	for model, st in pairs(dragons) do
		if not model:IsDescendantOf(workspace) then
			dragons[model] = nil
		elseif cam and (model:GetPivot().Position - cam.CFrame.Position).Magnitude < MAX_DISTANCE then
			update(st, dt)
		end
	end
end)
