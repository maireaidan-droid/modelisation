--[[
Dragon Long v13 : réglages automatiques après l'import dans Roblox Studio.

Utilisation :
  1. Importer Dragon_Long_v13.glb (Avatar > Import 3D, unité Stud, parties séparées, Anchored).
  2. Sélectionner le modèle importé dans l'Explorer (sinon le script cherche un modèle « Dragon_Long_v… » dans le Workspace).
  3. Affichage > Barre de commande (View > Command Bar), coller TOUT ce script, Entrée.

Le script :
  - applique la couleur et le matériau de chaque partie (yeux en Neon) ;
  - coupe les collisions du modèle détaillé et ajoute une Hitbox invisible autour de la tête ;
  - range un exemplaire dans ServerStorage > Dragons > Dragon_Long ;
  - laisse le modèle importé dans le Workspace comme exemplaire de test (renommé Dragon_Long_Test).
Il ne supprime rien. Ctrl+Z annule tout.
]]

local Selection = game:GetService("Selection")
local ServerStorage = game:GetService("ServerStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")

local PARTS = {
	Body     = { color = "#2F7D63", material = Enum.Material.SmoothPlastic, shadow = true },
	Belly    = { color = "#E2B65C", material = Enum.Material.SmoothPlastic, shadow = true },
	Fins     = { color = "#C8432F", material = Enum.Material.SmoothPlastic, shadow = true, doubleSided = true },
	Horns    = { color = "#E6DCC3", material = Enum.Material.SmoothPlastic, shadow = true },
	Whiskers = { color = "#F0C24B", material = Enum.Material.SmoothPlastic, shadow = true, doubleSided = true },
	Eyes     = { color = "#FFD23F", material = Enum.Material.Neon,          shadow = false },
	Pupils   = { color = "#17120E", material = Enum.Material.SmoothPlastic, shadow = false },
	Mouth    = { color = "#3A1013", material = Enum.Material.SmoothPlastic, shadow = false },
	Tongue   = { color = "#B9434C", material = Enum.Material.SmoothPlastic, shadow = false },
}
local EXPECTED_LENGTH = 58 -- studs, environ

-- 1. Trouver le modèle
local model = Selection:Get()[1]
if not (model and model:IsA("Model")) then
	model = workspace:FindFirstChild("Dragon_Long_v13", true)
end
if not (model and model:IsA("Model")) then
	for _, m in ipairs(workspace:GetDescendants()) do
		if m:IsA("Model") and string.sub(m.Name, 1, 13) == "Dragon_Long_v" then model = m break end
	end
end
if not (model and model:IsA("Model")) then
	warn("[Dragon] Modèle introuvable : sélectionne le modèle importé dans l'Explorer puis relance le script.")
	return
end

ChangeHistoryService:SetWaypoint("Avant réglage Dragon Long")

-- 2. Réglages de chaque partie
local found, body, eyes = {}, nil, {}
for _, part in ipairs(model:GetDescendants()) do
	if part:IsA("BasePart") then
		for name, cfg in pairs(PARTS) do
			if part.Name == name or string.find(part.Name, name, 1, true) then
				part.Name = name
				part.Color = Color3.fromHex(cfg.color)
				part.Material = cfg.material
				part.CastShadow = cfg.shadow
				if cfg.doubleSided then
					pcall(function() part.DoubleSided = true end) -- pas modifiable partout : on ignore si refusé
				end
				found[name] = (found[name] or 0) + 1
				if name == "Body" then body = part end
				if name == "Eyes" then table.insert(eyes, part) end
				break
			end
		end
		part.Anchored = true
		part.CanCollide = false
		part.CanTouch = false
		part.CanQuery = false
	end
end

local missing = {}
for name in pairs(PARTS) do
	if not found[name] then table.insert(missing, name) end
end

-- 3. Vérification de la taille (problème d'unité à l'import)
local size = model:GetExtentsSize()
local longest = math.max(size.X, size.Y, size.Z)
print(string.format("[Dragon] Taille : %.1f x %.1f x %.1f studs", size.X, size.Y, size.Z))
if longest > EXPECTED_LENGTH * 2 or longest < EXPECTED_LENGTH / 2 then
	warn("[Dragon] Taille inattendue : réimporte avec une autre unité (Stud / Mètre), le modèle fait environ 58 studs de long.")
end

-- 4. Hitbox invisible autour de la tête (centrée sur les yeux)
if #eyes > 0 and not model:FindFirstChild("Hitbox") then
	local center = Vector3.zero
	for _, e in ipairs(eyes) do center += e.Position end
	center /= #eyes
	local bboxCf = model:GetBoundingBox()
	local hitbox = Instance.new("Part")
	hitbox.Name = "Hitbox"
	hitbox.Size = Vector3.new(9, 9, 13)
	hitbox.CFrame = CFrame.new(center) * (bboxCf - bboxCf.Position)
	hitbox.Transparency = 1
	hitbox.Anchored = true
	hitbox.CanCollide = true
	hitbox.CanQuery = true
	hitbox.CanTouch = false
	hitbox.CastShadow = false
	hitbox.Parent = model
end

if body then model.PrimaryPart = body end

-- 5. Rangement : un exemplaire dans ServerStorage > Dragons, l'importé reste dans le Workspace pour le test
local dragons = ServerStorage:FindFirstChild("Dragons") or Instance.new("Folder")
dragons.Name = "Dragons"
dragons.Parent = ServerStorage
if not dragons:FindFirstChild("Dragon_Long") then
	local template = model:Clone()
	template.Name = "Dragon_Long"
	template.Parent = dragons
end
model.Name = "Dragon_Long_Test"
if model.Parent ~= workspace and not model:IsDescendantOf(workspace) then
	model.Parent = workspace
end
Selection:Set({ model })

ChangeHistoryService:SetWaypoint("Réglage Dragon Long")

-- 6. Rapport
local report = {}
for name, n in pairs(found) do table.insert(report, name .. " x" .. n) end
table.sort(report)
print("[Dragon] Parties réglées : " .. table.concat(report, ", "))
if #missing > 0 then
	warn("[Dragon] Parties introuvables : " .. table.concat(missing, ", ") .. " (vérifie leurs noms dans l'Explorer)")
else
	print("[Dragon] Les 9 parties sont là. Modèle rangé dans ServerStorage > Dragons > Dragon_Long, test : Workspace > Dragon_Long_Test.")
end
