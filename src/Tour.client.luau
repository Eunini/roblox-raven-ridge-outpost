-- Optional Studio portfolio tools. Architecture remains a normal explorable place.
-- Press F6 to cycle staged views, F7 to return to the character, L for lighting.
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local Lighting = game:GetService("Lighting")
local cameras = require(game:GetService("ReplicatedStorage"):WaitForChild("TourCameras"))
local player = Players.LocalPlayer
local index = 0
local night = false
local cameraTween = nil
local gui = Instance.new("ScreenGui")
gui.Name = "RavenRidgePortfolio"
gui.ResetOnSpawn = false
gui.Parent = player:WaitForChild("PlayerGui")
local caption = Instance.new("TextLabel")
caption.Position = UDim2.new(0, 20, 1, -60)
caption.Size = UDim2.fromOffset(540, 38)
caption.BackgroundColor3 = Color3.fromRGB(27, 36, 33)
caption.BackgroundTransparency = 0.15
caption.TextColor3 = Color3.fromRGB(233, 233, 219)
caption.TextSize = 16
caption.Font = Enum.Font.GothamMedium
caption.Text = "RAVEN RIDGE   |   F6: views   F7: explore   L: lighting"
caption.Parent = gui

local function explore()
    if cameraTween then cameraTween:Cancel() end
    local camera = workspace.CurrentCamera
    camera.CameraType = Enum.CameraType.Custom
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if humanoid then camera.CameraSubject = humanoid end
    caption.Text = "RAVEN RIDGE   |   F6: views   F7: explore   L: lighting"
end

UserInputService.InputBegan:Connect(function(input, processed)
    if processed then return end
    if input.KeyCode == Enum.KeyCode.F6 then
        index = index % #cameras + 1
        local shot = cameras[index]
        local camera = workspace.CurrentCamera
        if cameraTween then cameraTween:Cancel() end
        camera.CameraType = Enum.CameraType.Scriptable
        local position = Vector3.new(table.unpack(shot.pos))
        local target = Vector3.new(table.unpack(shot.target))
        cameraTween = TweenService:Create(camera, TweenInfo.new(1.4, Enum.EasingStyle.Sine), {CFrame = CFrame.lookAt(position, target)})
        cameraTween:Play()
        caption.Text = "RAVEN RIDGE   |   " .. shot.name .. "   |   F7: explore"
    elseif input.KeyCode == Enum.KeyCode.F7 then
        explore()
    elseif input.KeyCode == Enum.KeyCode.L then
        night = not night
        Lighting.ClockTime = if night then 20 else 16.7
        Lighting.Brightness = if night then 1 else 2.5
    end
end)
player.CharacterAdded:Connect(function() task.defer(explore) end)
