-- Independent rbxmk decoder/encoder validation, not a Roblox runtime test.
local place = fs.read("build/RavenRidge.rbxlx", "rbxlx")
local parts, scripts = 0, 0
for _, instance in ipairs(place:GetDescendants()) do
    if instance.ClassName == "Part" or instance.ClassName == "WedgePart" or instance.ClassName == "CornerWedgePart" or instance.ClassName == "SpawnLocation" then
        parts = parts + 1
        assert(instance.Anchored == true, "Unanchored part " .. instance.Name)
    end
    if instance.ClassName == "Script" or instance.ClassName == "LocalScript" then scripts = scripts + 1 end
end
local expected = fs.read("build/manifest.json", "json").stats.parts
assert(parts == expected, "Geometry did not survive decoding: " .. parts)
assert(scripts == 2, "Missing runtime scripts")
fs.write("build/RavenRidge.rbxl", place, "rbxl")
local reread = fs.read("build/RavenRidge.rbxl", "rbxl")
assert(#reread:GetDescendants() == #place:GetDescendants(), "Binary round-trip changed instance count")
print("Independent native-file round trip passed: " .. parts .. " parts, " .. scripts .. " scripts")
