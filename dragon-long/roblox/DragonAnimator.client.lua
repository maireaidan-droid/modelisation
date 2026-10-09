--[[
DragonAnimator : anime le Dragon Long (modèle avec squelette Dragon_Long_v18_rig).

À placer dans : StarterPlayer > StarterPlayerScripts (LocalScript).
L'animation tourne chez chaque joueur (les os ne se répliquent pas depuis le serveur), c'est normal.

Le dragon est trouvé automatiquement :
  - tout Model qui porte le tag « DragonLong » (CollectionService), ou dont le nom commence par « Dragon_Long ».
Le mode se choisit avec l'attribut « Mode » du Model (réglable depuis un script serveur, il se réplique) :
  "Idle" (repos), "Walk" (marche), "Fly" (vol). Les changements de mode sont progressifs.

Ce qui est animé :
  - corps : ondulation qui part du cou et grandit vers la queue ;
  - tête : reste stable pendant l'ondulation, regarde autour d'elle au repos, mâchoire qui respire ;
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

local MODES = {
	Idle = { side = 0.035, pitch = 0.015, wave = 1.2, tuck = 0, walk = 0, mane = 0.12, maneSpeed = 1.6, jaw = 0.04, bob = 0.15, bank = 0, dive = 0, neck = 0.75, sway = 0, swayPh = 0, tail = 1, helix = 0 },
	Walk = { side = 0.07, pitch = 0.012, wave = 3.4, tuck = 0, walk = 1, mane = 0.2, maneSpeed = 3.2, jaw = 0.07, bob = 0.2, bank = 0, dive = 0, neck = 0.75, sway = 0, swayPh = 0, tail = 1, helix = 0 },
	-- Vol : vague en spirale (le corps s'enroule comme un tire-bouchon, comme les dragons chinois) + tonneaux,
	-- grandes vagues qui descendent du cou vers la queue (le dragon « nage » dans l'air),
	-- un peu de roulis et de tangage de tout le corps, crinière soulevée qui claque au vent.
	-- neck : force de l'onde dans le cou ; sway : bascule du poitrail (fait bouger tout l'avant) ; tail : force dans la queue.
	Fly  = { side = 0.05, pitch = 0.1, wave = 2.6, tuck = 1, walk = 0, mane = 0.5, maneSpeed = 7, jaw = 0.14, bob = 1.4, bank = 0.12, dive = 0.05,
		neck = 1.0, sway = 0.18, swayPh = 2.0, tail = 0.5, helix = 1 },
}

local TAIL = {}
for k = 1, 14 do
	TAIL[k] = string.format("S%02d", k)
end
local NECK = { { "Neck2", -1 }, { "Neck", -2 } }
local LEGS = { LegFL = 0, LegBR = 0, LegFR = math.pi, LegBL = math.pi }

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
		blinkIn = rng:NextNumber(1, 4), blink = -1, rollIn = 3, roll = -1,
		look = 0, lookTarget = 0, lookIn = 1.5, headLook = 0, headTarget = 0,
	}
end

local function setBone(st, name, rx, ry, rz, ty, tz)
	local list = st.bones[name]
	if not list then
		return
	end
	local cf = CFrame.new(0, ty or 0, tz or 0) * CFrame.Angles(rx, ry, rz)
	for _, b in ipairs(list) do
		b.Transform = cf
	end
end

local function update(st, dt)
	local mode = st.model:GetAttribute("Mode")
	local target = MODES[mode] or MODES.Idle
	mode = MODES[mode] and mode or "Idle"
	st.t += dt
	local p = st.p
	local k = math.min(1, dt * 2.5)
	for key, v in pairs(target) do
		p[key] += (v - p[key]) * k
	end
	st.phase += dt * p.wave
	st.step += dt * 4.2 * p.walk
	st.flutter += dt * p.maneSpeed

	-- Colonne : une onde qui part du cou et grandit vers la queue.
	for i, name in ipairs(TAIL) do
		local grow = 0.6 + 0.4 * i / 14
		-- helix = 1 : le côté suit le haut/bas avec un quart de tour d'avance, chaque anneau décrit un cercle.
		local amp = p.pitch * p.tail * grow
		local yaw = p.side * grow * math.sin(st.phase * 0.7 - i * 0.4 + 1) * (1 - p.helix)
			+ amp * p.helix * math.cos(st.phase - i * 0.45)
		local pitch = amp * math.sin(st.phase - i * 0.45)
		setBone(st, name, pitch, yaw, 0)
	end
	-- Cou : la même onde continue jusqu'à la tête (signe inversé : ces os pointent vers l'avant).
	local neckPitch, neckYaw = 0, 0
	for _, n in ipairs(NECK) do
		local k1 = n[2]
		local yaw = -p.side * p.neck * math.sin(st.phase * 0.7 - k1 * 0.4 + 1) * (1 - p.helix)
			- p.pitch * p.neck * p.helix * math.cos(st.phase - k1 * 0.45)
		local pitch = -p.pitch * p.neck * math.sin(st.phase - k1 * 0.45)
		setBone(st, n[1], pitch, yaw, 0)
		neckPitch += pitch
		neckYaw += yaw
	end
	-- Tout le corps : monte et descend, pique légèrement et s'incline (roulis) en vol.
	-- sway : le poitrail bascule au rythme de la vague, ce qui fait monter et descendre tout l'avant.
	-- Tonneau : en vol, toutes les 6 à 10 s, le dragon fait un tour complet sur lui-même (2,4 s).
	st.rollIn -= dt * p.helix
	if st.rollIn <= 0 and st.roll < 0 and p.helix > 0.9 then
		st.roll = 0
		st.rollIn = rng:NextNumber(6, 10)
	end
	local rollAngle = 0
	if st.roll >= 0 then
		st.roll += dt / 2.4
		local r = math.min(1, st.roll)
		rollAngle = 2 * math.pi * r * r * (3 - 2 * r)
		if st.roll >= 1 then
			st.roll = -1
		end
	end
	setBone(st, "Root", p.dive * math.sin(st.phase * 0.5) + p.sway * math.sin(st.phase + p.swayPh), 0,
		p.bank * math.sin(st.phase * 0.35) + rollAngle,
		p.bob * math.sin(st.phase * 0.5 + 1) + 0.12 * p.walk * math.abs(math.sin(st.step)))

	-- Tête : compense l'ondulation pour garder le regard stable, et regarde autour d'elle au repos.
	st.lookIn -= dt
	if st.lookIn <= 0 then
		st.lookIn = rng:NextNumber(1.5, 4)
		st.lookTarget = rng:NextNumber(-0.2, 0.2)
		st.headTarget = (mode == "Idle") and rng:NextNumber(-0.25, 0.25) or 0
	end
	st.look += (st.lookTarget - st.look) * math.min(1, dt * 6)
	st.headLook += (st.headTarget - st.headLook) * math.min(1, dt * 1.5)
	-- La tête suit la vague et n'en compense qu'une partie : elle mène le mouvement.
	setBone(st, "Head", 0.05 * math.sin(st.t * 0.9) - neckPitch * 0.2, -neckYaw * 0.4 + st.headLook, 0)
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

	-- Crinière, moustaches, barbichette : flottent, plus fort en vol.
	local f, m = st.flutter, p.mane
	local lift = 0.25 * p.tuck -- en vol, la crinière se soulève et part vers l'arrière
	setBone(st, "Mane_Top", lift + 0.5 * m * math.sin(f), m * math.sin(f * 1.3 + 1), 0)
	setBone(st, "Mane_L", lift + 0.6 * m * math.sin(f + 2), m * math.sin(f * 1.1 + 0.5), 0)
	setBone(st, "Mane_R", lift + 0.6 * m * math.sin(f + 2.6), -m * math.sin(f * 1.1 + 1.2), 0)
	setBone(st, "Whisker_L", 0.8 * m * math.sin(f * 0.9), m * math.sin(f * 0.7 + 0.3), 0)
	setBone(st, "Whisker_R", 0.8 * m * math.sin(f * 0.9 + 1), -m * math.sin(f * 0.7 + 1.1), 0)
	setBone(st, "Beard", 0.5 * m * math.sin(f * 0.8), 0.4 * m * math.sin(f * 1.2), 0)

	-- Pattes : marche en diagonale (avant gauche + arrière droite, puis l'inverse), repliées en vol.
	for leg, offset in pairs(LEGS) do
		local ph = st.step + offset
		local sw, lift = math.sin(ph), math.max(0, math.cos(ph))
		local paddle = 0.15 * p.tuck * math.sin(st.phase * 1.5 + offset) -- pattes qui pagaient en vol
		setBone(st, leg .. "_Upper", -0.45 * sw * p.walk + 0.9 * p.tuck + paddle, 0, 0)
		setBone(st, leg .. "_Fore", 0.6 * lift * p.walk + 0.6 * p.tuck, 0, 0)
		setBone(st, leg .. "_Foot", -0.35 * lift * p.walk - 0.4 * p.tuck, 0, 0)
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
