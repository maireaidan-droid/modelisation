--[[
Dragon Long v19 : réglages automatiques après l'import dans Roblox Studio, pour les 5 raretés.

Utilisation :
  1. Importer le fichier du dragon (Avatar > Import 3D, unité Stud, parties séparées, Anchored) :
       Commun et Rare : Dragon_Long_v19_rig.glb      Épique : Dragon_Long_v19_glace_rig.glb
       Légendaire : Dragon_Long_v19_celeste_rig.glb  Mythique : Dragon_Long_v19_neant_rig.glb
  2. Sélectionner le modèle importé dans l'Explorer (sinon le script cherche un modèle « Dragon_Long_v… » dans le Workspace).
  3. Affichage > Barre de commande (View > Command Bar), coller TOUT ce script, Entrée.

La rareté est devinée d'après le nom du modèle importé (glace = Épique, celeste = Légendaire, neant = Mythique,
sinon Commun). Pour le Rare (même forme que le Commun), change RARITY ci-dessous en "Rare", ou mets l'attribut
« Rarity » = "Rare" sur le modèle avant de lancer le script.

Le script :
  - applique la couleur et le matériau de chaque partie selon la rareté (yeux et parties lumineuses en Neon) ;
  - coupe les collisions du modèle détaillé et ajoute une Hitbox invisible autour de la tête ;
  - range un exemplaire dans ServerStorage > Dragons > Dragon_Long_<Rareté> (par exemple Dragon_Long_Mythique) ;
  - laisse le modèle importé dans le Workspace comme exemplaire de test (Dragon_Long_Test pour le premier,
    Dragon_Long_Test_<Rareté> pour les suivants) ;
  - règle l'attribut « BreathStyle » (couleur du souffle et des effets) selon la rareté ;
  - ajoute le tag « DragonLong » et l'attribut Mode = "Idle", utilisés par DragonAnimator pour l'animer.
Il ne supprime rien. Ctrl+Z annule tout.
]]

local Selection = game:GetService("Selection")
local ServerStorage = game:GetService("ServerStorage")
local ChangeHistoryService = game:GetService("ChangeHistoryService")
local CollectionService = game:GetService("CollectionService")

local PARTS = {
	Body     = { color = "#2F7D63", material = Enum.Material.SmoothPlastic, shadow = true },
	Belly    = { color = "#E2B65C", material = Enum.Material.SmoothPlastic, shadow = true },
	Fins     = { color = "#C8432F", material = Enum.Material.SmoothPlastic, shadow = true, doubleSided = true },
	Horns    = { color = "#E6DCC3", material = Enum.Material.SmoothPlastic, shadow = true },
	Whiskers = { color = "#F0C24B", material = Enum.Material.SmoothPlastic, shadow = true, doubleSided = true },
	Eyes     = { color = "#FFD23F", material = Enum.Material.Neon,          shadow = false },
	Pupils   = { color = "#17120E", material = Enum.Material.SmoothPlastic, shadow = false },
	Mouth    = { color = "#8E2529", material = Enum.Material.SmoothPlastic, shadow = false },
	Tongue   = { color = "#B9434C", material = Enum.Material.SmoothPlastic, shadow = false },
}
-- Mythique (Dragon_Long_v19_neant_rig) : crête et ventre découpés en tronçons numérotés (Crest1…, BellyGlow1…)
-- pour la vague de lumière. On garde leurs noms tels quels (DragonAnimator s'en sert).
local SEGMENTS = {
	Crest     = { like = "Fins", material = Enum.Material.Neon },
	BellyGlow = { like = "Belly" },
	Crack     = { color = "#FF3FD8", material = Enum.Material.Neon, shadow = false }, -- fissures de lumière
}
-- Aura d'ombre autour du corps (Mythique) : matériau ForceField (scintille tout seul) et particules aspirées.
local AURA = { color = "#2A1450", material = Enum.Material.ForceField }
local EXPECTED_LENGTH = 58 -- studs, environ

-- Rareté utilisée si on ne peut pas la deviner : "Commun", "Rare", "Epique", "Legendaire" ou "Mythique".
local RARITY = "Commun"
-- Palettes (mêmes couleurs que la démo des raretés). neon = parties qui brillent ; breath = style du souffle.
local RARITIES = {
	Commun = { breath = "fire", neon = {}, colors = {} },
	Rare = { breath = "fire", neon = { Fins = true },
		colors = { Body = "#6E1D1A", Belly = "#E8A33D", Fins = "#FF6A1A", Horns = "#2A2020", Whiskers = "#FFB12E",
			Eyes = "#FFE14A", Pupils = "#1A0A05", Mouth = "#7A1515", Tongue = "#C2453F" } },
	Epique = { breath = "ice", neon = { Fins = true },
		colors = { Body = "#4A82AE", Belly = "#DCEEF6", Fins = "#6FE6FF", Horns = "#E3EEF5", Whiskers = "#C8F4FF",
			Eyes = "#7FE3FF", Pupils = "#0E2233", Mouth = "#5B2A4A", Tongue = "#B85A7A" } },
	Legendaire = { breath = "gold", neon = { Fins = true, Whiskers = true },
		colors = { Body = "#E3D8C4", Belly = "#D9A93F", Fins = "#FFD24D", Horns = "#E8B84F", Whiskers = "#FFF0A8",
			Eyes = "#7FF7FF", Pupils = "#1B1406", Mouth = "#8E2529", Tongue = "#C25A5A" } },
	Mythique = { breath = "void", neon = { Fins = true, Whiskers = true },
		colors = { Body = "#0C0918", Belly = "#2B1F5C", Fins = "#FF4FD8", Horns = "#CFC6E8", Whiskers = "#8FF3FF",
			Eyes = "#FF3FD8", Pupils = "#12021C", Mouth = "#3A0C34", Tongue = "#A03A82" } },
}

-- 1. Trouver le modèle
local model = Selection:Get()[1]
if not (model and model:IsA("Model")) then
	model = workspace:FindFirstChild("Dragon_Long_v19", true)
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

-- Rareté : attribut « Rarity », sinon d'après le nom du fichier importé, sinon RARITY.
local lname = string.lower(model.Name)
local rarityName = model:GetAttribute("Rarity")
	or (string.find(lname, "neant") and "Mythique")
	or (string.find(lname, "celeste") and "Legendaire")
	or (string.find(lname, "glace") and "Epique")
	or RARITY
local rarity = RARITIES[rarityName] or RARITIES.Commun
rarityName = RARITIES[rarityName] and rarityName or "Commun"
for name, cfg in pairs(PARTS) do
	cfg.color = rarity.colors[name] or cfg.color
	if rarity.neon[name] then
		cfg.material = Enum.Material.Neon
	end
end
print("[Dragon] Rareté : " .. rarityName)

ChangeHistoryService:SetWaypoint("Avant réglage Dragon Long")

-- 2. Réglages de chaque partie
local found, body, eyes = {}, nil, {}
for _, part in ipairs(model:GetDescendants()) do
	if part:IsA("BasePart") then
		local kind, num = string.match(part.Name, "^(%a+)(%d+)") -- « Crest3 » ou « Crest3_Mesh » si Studio l'a renommée
		local seg = SEGMENTS[kind or ""]
		if seg then
			local cfg = seg.like and PARTS[seg.like] or seg
			part.Name = kind .. num
			part.Color = Color3.fromHex(cfg.color)
			part.Material = seg.material or cfg.material
			part.CastShadow = cfg.shadow
			if seg.like then found[seg.like] = found[seg.like] or 0 end
		elseif string.sub(part.Name, 1, 4) == "Aura" then
			part.Name = "Aura"
			part.Color = Color3.fromHex(AURA.color)
			part.Material = AURA.material
			part.CastShadow = false
			if not part:FindFirstChild("Absorption") then
				-- Des grains de lumière naissent sur une boîte autour du dragon et sont aspirés vers lui.
				local fx = Instance.new("ParticleEmitter")
				fx.Name = "Absorption"
				fx.Shape = Enum.ParticleEmitterShape.Box
				fx.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
				fx.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
				fx.Color = ColorSequence.new(Color3.fromHex("#C58BFF"))
				fx.LightEmission = 1
				fx.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 0.35) })
				fx.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.2),
					NumberSequenceKeypoint.new(1, 1) })
				fx.Speed = NumberRange.new(3, 6)
				fx.Acceleration = Vector3.zero
				fx.Lifetime = NumberRange.new(1.5, 2.5)
				fx.Rate = 40
				fx.Parent = part
			end
		else
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

-- Animation : DragonAnimator retrouve le dragon grâce à ce tag et lit son mode (Idle / Fly / Dead).
CollectionService:AddTag(model, "DragonLong")
if model:GetAttribute("Mode") == nil then model:SetAttribute("Mode", "Idle") end
model:SetAttribute("Rarity", rarityName)
model:SetAttribute("BreathStyle", rarity.breath)

-- 5. Rangement : un exemplaire dans ServerStorage > Dragons, l'importé reste dans le Workspace pour le test
local dragons = ServerStorage:FindFirstChild("Dragons") or Instance.new("Folder")
dragons.Name = "Dragons"
dragons.Parent = ServerStorage
local templateName = "Dragon_Long_" .. rarityName
if not dragons:FindFirstChild(templateName) then
	local template = model:Clone()
	template.Name = templateName
	template.Parent = dragons
end
-- Le premier dragon réglé s'appelle Dragon_Long_Test (c'est celui que DragonDemo anime) ; les autres gardent
-- leur rareté dans le nom.
local testName = "Dragon_Long_Test"
local other = workspace:FindFirstChild(testName)
if other and other ~= model then
	testName = testName .. "_" .. rarityName
end
model.Name = testName
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
	print("[Dragon] Les 9 parties sont là. Modèle rangé dans ServerStorage > Dragons > " .. templateName
		.. ", test : Workspace > " .. testName .. ".")
end
