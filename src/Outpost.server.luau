-- Raven Ridge. Server-owned, distance-checked architectural interactions.
local TweenService = game:GetService("TweenService")
local outpost = workspace:WaitForChild("RavenRidge")
local mechanisms = {}

for _, instance in outpost:GetDescendants() do
    if instance:IsA("BasePart") then
        local tag = instance:FindFirstChild("Mechanism")
        if tag and tag:IsA("StringValue") then
            mechanisms[tag.Value] = mechanisms[tag.Value] or {parts = {}, open = false, busy = false}
            table.insert(mechanisms[tag.Value].parts, {part = instance, origin = instance.CFrame})
        end
    end
end

local function bind(prompt, mechanismName)
    local mechanism = mechanisms[mechanismName]
    if not mechanism then return end
    prompt.Triggered:Connect(function(player)
        local character = player.Character
        local root = character and character:FindFirstChild("HumanoidRootPart")
        local parent = prompt.Parent
        if not root or not parent:IsA("BasePart") then return end
        if (root.Position - parent.Position).Magnitude > prompt.MaxActivationDistance + 2 then return end
        if mechanism.busy then return end
        mechanism.busy = true
        mechanism.open = not mechanism.open
        local offset = if mechanismName == "gate" then Vector3.new(0, 8, 0) else Vector3.new(8.5, 0, 0)
        for _, entry in mechanism.parts do
            local target = entry.origin + (if mechanism.open then offset else Vector3.zero)
            TweenService:Create(entry.part, TweenInfo.new(1.1, Enum.EasingStyle.Quart, Enum.EasingDirection.InOut), {CFrame = target}):Play()
        end
        prompt.ActionText = if mechanism.open then "Close " .. mechanismName else "Open " .. mechanismName
        task.delay(1.2, function() mechanism.busy = false end)
    end)
end

for _, instance in outpost:GetDescendants() do
    if instance:IsA("ProximityPrompt") then
        bind(instance, if instance.Parent.Name == "BunkerDoor" then "bunker" else "gate")
    end
end
