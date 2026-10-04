-- The launcher compares the plugin's compiled ABI with the running compositor.
-- It remains available after user-only activation and declarative rebuilds.
local home = os.getenv("HOME")
-- Observe outside clicks without a fullscreen input surface or pointer grab.
-- Lua only checks compositor geometry; the D-Bus call runs asynchronously.
local function dismiss_control_center()
    local cursor = hl.get_cursor_pos()
    if not cursor then return end
    for _, layer in ipairs(hl.get_layers()) do
        if layer.namespace == "neo-control-center" and layer.mapped then
            if cursor.x >= layer.x and cursor.x < layer.x + layer.w
                and cursor.y >= layer.y and cursor.y < layer.y + layer.h then
                return
            end
            hl.exec_cmd(home .. "/.local/bin/neo-control-center --dismiss")
            return
        end
    end
end
for _, key in ipairs({ "mouse:272", "mouse:273", "mouse:274" }) do
    hl.bind(key, dismiss_control_center, {
        release = true, non_consuming = true, ignore_mods = true,
    })
end
-- Escape closes the panel even if focus follows the pointer into another app.
-- Enable this binding only while the panel is mapped, leaving normal app
-- Escape handling alone when Control Center is closed.
local panel_escape = hl.bind("Escape", hl.dsp.exec_cmd(home .. "/.local/bin/neo-control-center --escape"))
panel_escape:set_enabled(false)
hl.on("layer.opened", function(layer)
    if layer.namespace == "neo-control-center" then panel_escape:set_enabled(true) end
end)
hl.on("layer.closed", function(layer)
    if layer.namespace == "neo-control-center" then panel_escape:set_enabled(false) end
end)
for _, layer in ipairs(hl.get_layers()) do
    if layer.namespace == "neo-control-center" and layer.mapped then
        panel_escape:set_enabled(true)
    end
end
local preset = home .. "/.local/share/neo-hyprglass/preset.lua"
if hl.plugin.hyprglass then
    local file = io.open(preset, "r")
    if file then
        file:close()
        dofile(preset)
    end
end
-- Launch only after the compositor starts, never during config parsing:
-- the helper loads the plugin and reloads this file to apply its preset.
hl.on("hyprland.start", function()
    if hl.plugin.hyprglass then return end
    local launcher = home .. "/.local/bin/neo-hyprglass"
    local file = io.open(launcher, "r")
    if file then
        file:close()
        hl.exec_cmd(launcher .. " apply")
    end
end)
