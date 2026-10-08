--[[
DragonDemo (optionnel) : fait vivre un dragon pour tester les animations.

À placer dans : ServerScriptService (Script). Le dragon doit être dans le Workspace et s'appeler « Dragon_Long_Test »
(c'est le nom que lui donne setup_dragon_long.lua), sinon change DRAGON_NAME.

Cycle : repos (6 s), marche en ligne droite (8 s), vol en cercle en prenant de la hauteur (12 s), puis retour au sol.
Le serveur ne fait que déplacer le Model et régler l'attribut « Mode » ; les os sont animés par DragonAnimator chez
chaque joueur.
]]

local RunService = game:GetService("RunService")

local DRAGON_NAME = "Dragon_Long_Test"
local WALK_SPEED = 8      -- studs/s
local FLY_SPEED = 30      -- studs/s
local FLY_RADIUS = 60
local FLY_HEIGHT = 35
-- La tête du dragon regarde vers +Z dans le fichier. Si en jeu il avance à reculons, mets -1.
local HEAD_FORWARD = 1
local FACE = HEAD_FORWARD == 1 and CFrame.Angles(0, math.pi, 0) or CFrame.new()

local dragon = workspace:WaitForChild(DRAGON_NAME)
local start = dragon:GetPivot()
local function setMode(m)
	dragon:SetAttribute("Mode", m)
end

local function run(duration, stepFn)
	local t = 0
	while t < duration do
		local dt = RunService.Heartbeat:Wait()
		t += dt
		stepFn(dt, t / duration)
	end
end

while true do
	-- Repos
	setMode("Idle")
	task.wait(6)

	-- Marche : avance tout droit (la tête regarde vers l'avant du modèle).
	setMode("Walk")
	run(8, function(dt)
		dragon:PivotTo(dragon:GetPivot() * CFrame.new(0, 0, HEAD_FORWARD * WALK_SPEED * dt))
	end)

	-- Vol : décolle et tourne en cercle autour du point de départ.
	setMode("Fly")
	local base = dragon:GetPivot()
	local center = (base * CFrame.new(FLY_RADIUS, 0, 0)).Position -- cercle sur le côté gauche du dragon
	local a0 = math.atan2(base.Position.Z - center.Z, base.Position.X - center.X)
	run(12, function(_, k)
		local a = a0 - k * (12 * FLY_SPEED / FLY_RADIUS)
		local h = FLY_HEIGHT * math.sin(math.min(1, k * 1.2) * math.pi * 0.5)
		if k > 0.75 then
			h *= 1 - (k - 0.75) / 0.25
		end
		local pos = center + Vector3.new(math.cos(a) * FLY_RADIUS, h, math.sin(a) * FLY_RADIUS)
		local ahead = center + Vector3.new(math.cos(a - 0.05) * FLY_RADIUS, h, math.sin(a - 0.05) * FLY_RADIUS)
		-- lookAt tourne l'avant Roblox (-Z) vers la cible ; FACE retourne le dragon pour que ce soit sa tête.
		dragon:PivotTo(CFrame.lookAt(pos, Vector3.new(ahead.X, pos.Y, ahead.Z)) * FACE)
	end)

	-- Retour au point de départ pour recommencer.
	dragon:PivotTo(start)
end
