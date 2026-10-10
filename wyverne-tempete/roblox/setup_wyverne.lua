--[[
Wyverne des tempêtes v4 : réglages automatiques après l'import dans Roblox Studio.

Utilisation :
  1. Importer Wyverne_Tempete_v4.glb (Avatar > Import 3D, unité Stud, parties séparées, Anchored).
  2. Sélectionner le modèle importé dans l'Explorer (sinon le script cherche un modèle « Wyverne_Tempete… »).
  3. Affichage > Barre de commande (View > Command Bar), coller TOUT ce script, Entrée.

Le script :
  - applique la couleur et le matériau de chaque partie (éclairs et yeux en Neon) ;
  - coupe les collisions du modèle détaillé et ajoute des Hitbox invisibles (corps, buste, trois têtes) ;
  - range un exemplaire dans ServerStorage > Dragons > Wyverne_Tempete ;
  - laisse le modèle importé dans le Workspace comme exemplaire de test (renommé Wyverne_Tempete_Test) ;
  - ajoute le tag « WyverneTempete ».
Il ne supprime rien. Ctrl+Z annule tout.
]]

local Selection = game:GetService("Selection")
local ServerStorage = game:GetService("ServerStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local CollectionService = game:GetService("CollectionService")

local PARTS = {
	Body      = { color = "#1F2C52", material = Enum.Material.SmoothPlastic, shadow = true },
	Scales    = { color = "#2A3D72", material = Enum.Material.SmoothPlastic, shadow = true },
	Belly     = { color = "#3B4F86", material = Enum.Material.SmoothPlastic, shadow = true },
	Plates    = { color = "#2E3C68", material = Enum.Material.SmoothPlastic, shadow = true },
	Membrane  = { color = "#2A3E7A", material = Enum.Material.SmoothPlastic, shadow = true, doubleSided = true },
	Membrane2 = { color = "#16204A", material = Enum.Material.SmoothPlastic, shadow = true, doubleSided = true },
	Horns     = { color = "#C9D6F0", material = Enum.Material.SmoothPlastic, shadow = true },
	Bolt      = { color = "#6FF2FF", material = Enum.Material.Neon,          shadow = false },
	Bolt2     = { color = "#FFF27A", material = Enum.Material.Neon,          shadow = false },
	Eyes      = { color = "#B8FBFF", material = Enum.Material.Neon,          shadow = false },
	Mouth     = { color = "#3A1030", material = Enum.Material.SmoothPlastic, shadow = false },
}
-- Ordre de recherche : les noms longs d'abord (« Membrane2 » avant « Membrane », « Bolt2 » avant « Bolt »).
local ORDER = { "Membrane2", "Membrane", "Bolt2", "Bolt", "Body", "Scales", "Belly", "Plates", "Horns", "Eyes", "Mouth" }
local EXPECTED_LENGTH = 95 -- studs, environ (envergure)

-- 1. Trouver le modèle
local model = Selection:Get()[1]
if not (model and model:IsA("Model")) then
	for _, m in ipairs(workspace:GetDescendants()) do
		if m:IsA("Model") and string.sub(m.Name, 1, 15) == "Wyverne_Tempete" then
			model = m
			break
		end
	end
end
if not (model and model:IsA("Model")) then
	warn("[Wyverne] Modèle introuvable : sélectionne le modèle importé dans l'Explorer puis relance le script.")
	return
end

ChangeHistoryService:SetWaypoint("Avant réglage Wyverne")

-- 2. Réglages de chaque partie
local found = {}
local body
for _, part in ipairs(model:GetDescendants()) do
	if part:IsA("BasePart") then
		for _, name in ipairs(ORDER) do
			if part.Name == name or string.sub(part.Name, 1, #name) == name then
				local cfg = PARTS[name]
				part.Name = name
				part.Color = Color3.fromHex(cfg.color)
				part.Material = cfg.material
				part.CastShadow = cfg.shadow
				if cfg.doubleSided then
					pcall(function() part.DoubleSided = true end) -- pas modifiable partout : on ignore si refusé
				end
				found[name] = (found[name] or 0) + 1
				if name == "Body" then body = part end
				break
			end
		end
		part.Anchored = true
		part.CanCollide = false
		part.CanTouch = false
		part.CanQuery = false
	end
end

-- 3. Taille (problème d'unité à l'import)
local size = model:GetExtentsSize()
local longest = math.max(size.X, size.Y, size.Z)
print(string.format("[Wyverne] Taille : %.1f x %.1f x %.1f studs", size.X, size.Y, size.Z))
if longest > EXPECTED_LENGTH * 2 or longest < EXPECTED_LENGTH / 2 then
	warn("[Wyverne] Taille inattendue : réimporte avec une autre unité (Stud / Mètre), l'envergure fait environ 95 studs.")
end

-- 4. Hitbox invisibles : corps, buste et les trois têtes (positions dans le repère du modèle, tête vers +Z).
local HITBOXES = {
	{ "Hitbox_Corps", Vector3.new(0, 15, -8), Vector3.new(11, 12, 26) },
	{ "Hitbox_Buste", Vector3.new(0, 21, 6), Vector3.new(16, 10, 10) },
	{ "Hitbox_Tete", Vector3.new(0, 33, 20), Vector3.new(7, 7, 12) },
	{ "Hitbox_TeteG", Vector3.new(12, 30, 18), Vector3.new(6, 6, 11) },
	{ "Hitbox_TeteD", Vector3.new(-12, 30, 18), Vector3.new(6, 6, 11) },
}
local pivot = model:GetPivot()
for _, h in ipairs(HITBOXES) do
	if not model:FindFirstChild(h[1]) then
		local p = Instance.new("Part")
		p.Name = h[1]
		p.Size = h[3]
		p.CFrame = pivot * CFrame.new(h[2])
		p.Transparency = 1
		p.Anchored = true
		p.CanCollide = true
		p.CanQuery = true
		p.CanTouch = true
		p.CastShadow = false
		p.Parent = model
	end
end

if body then model.PrimaryPart = body end
CollectionService:AddTag(model, "WyverneTempete")

-- 5. Rangement
local dragons = ServerStorage:FindFirstChild("Dragons") or Instance.new("Folder")
dragons.Name = "Dragons"
dragons.Parent = ServerStorage
if not dragons:FindFirstChild("Wyverne_Tempete") then
	local template = model:Clone()
	template.Name = "Wyverne_Tempete"
	template.Parent = dragons
end
model.Name = "Wyverne_Tempete_Test"
if not model:IsDescendantOf(workspace) then
	model.Parent = workspace
end
Selection:Set({ model })

ChangeHistoryService:SetWaypoint("Réglage Wyverne")

-- 6. Rapport
local report, missing = {}, {}
for name, n in pairs(found) do table.insert(report, name .. " x" .. n) end
for name in pairs(PARTS) do
	if not found[name] then table.insert(missing, name) end
end
table.sort(report)
print("[Wyverne] Parties réglées : " .. table.concat(report, ", "))
if #missing > 0 then
	warn("[Wyverne] Parties introuvables : " .. table.concat(missing, ", ") .. " (vérifie leurs noms dans l'Explorer)")
else
	print("[Wyverne] Les 11 parties sont là. Modèle rangé dans ServerStorage > Dragons > Wyverne_Tempete, test : Workspace > Wyverne_Tempete_Test.")
end
