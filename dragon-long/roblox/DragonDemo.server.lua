--[[
DragonDemo (optionnel) : fait vivre un dragon pour tester les animations.

À placer dans : ServerScriptService (Script). Le dragon doit être dans le Workspace et s'appeler « Dragon_Long_Test »
(c'est le nom que lui donne setup_dragon_long.lua), sinon change DRAGON_NAME.

Cycle : repos et rugissement, morsure, vol en cercle (le corps se courbe dans le
virage), atterrissage et souffle, puis il meurt et se relève.
Le serveur ne fait que déplacer le Model et régler les attributs « Mode » et « Action » ; les os sont animés par
DragonAnimator chez chaque joueur.
]]

local RunService = game:GetService("RunService")
local Players = game:GetService("Players")

local DRAGON_NAME = "Dragon_Long_Test"
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
-- Lance une action (Roar, Bite, Breath). Le numéro après # permet de relancer la même action plusieurs fois.
local actionCount = 0
local function playAction(name)
	actionCount += 1
	dragon:SetAttribute("Action", name .. "#" .. actionCount)
end

-- Cible de la morsure : le joueur le plus proche (à moins de 40 studs), sinon un point devant, un peu à gauche.
local function aimAtNearestPlayer()
	local best, bestDist = nil, 40
	local pos = dragon:GetPivot().Position
	for _, plr in ipairs(Players:GetPlayers()) do
		local root = plr.Character and plr.Character:FindFirstChild("HumanoidRootPart")
		if root and (root.Position - pos).Magnitude < bestDist then
			best, bestDist = root.Position, (root.Position - pos).Magnitude
		end
	end
	-- La tête regarde vers +Z du modèle (HEAD_FORWARD) : point à 30 studs devant, 8 à gauche, 12 de haut.
	dragon:SetAttribute("Target", best or (dragon:GetPivot() * CFrame.new(8, 12, 30 * HEAD_FORWARD)).Position)
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
	-- Repos, puis rugissement
	setMode("Idle")
	task.wait(4)
	playAction("Roar")
	task.wait(3)

	-- Morsure vers le joueur le plus proche
	aimAtNearestPlayer()
	playAction("Bite")
	task.wait(1.5)

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

	-- Au sol : souffle (feu par défaut ; attribut « BreathStyle » = "ice", "gold" ou "void" pour changer).
	setMode("Idle")
	task.wait(1.5)
	playAction("Breath")
	task.wait(4)

	-- Mort, puis il se relève.
	setMode("Dead")
	task.wait(5)
	setMode("Idle")
	task.wait(2)

	-- Retour au point de départ pour recommencer.
	dragon:PivotTo(start)
end
