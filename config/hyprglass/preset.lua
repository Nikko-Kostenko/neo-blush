-- HyprGlass 0.6.4 settings for the Neo Blush desktop.
-- Declare presets before using them, and keep ordinary application windows
-- opt-in. Alpha masks leave transparent gaps between controls untouched.
local state = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state"))
-- Retire handles from the previous Dolphin-only preset on a live reload.
for _, rule in ipairs(neoHyprglassDolphinRules or {}) do
    rule:set_enabled(false)
end
neoHyprglassDolphinRules = nil
for _, rule in ipairs(neoHyprglassFileRules or {}) do
    rule:set_enabled(false)
end
neoHyprglassFileRules = {}
local fileClass = "^(org\\.kde\\.dolphin|dolphin|thunar|Thunar)$"
local disabled = io.open(state .. "/neo-hyprglass/disabled", "r")
-- Disabling a rule does not clear an existing dynamic tag in this compositor.
-- The dispatcher clears those tags; the static disabled tag also wins while off.
for _, window in ipairs(hl.get_windows()) do
    if window.class == "org.kde.dolphin" or window.class == "dolphin"
        or window.class == "thunar" or window.class == "Thunar" then
        hl.dispatch(hl.dsp.window.tag({
            tag = disabled and "+hyprglass_disabled" or "-hyprglass_disabled",
            window = "address:" .. window.address,
        }))
    end
end
if disabled then
    disabled:close()
    table.insert(neoHyprglassFileRules, hl.window_rule({
        name = "neo-files-glass-blur",
        match = { class = fileClass },
        no_blur = false,
    }))
    return
end
if hl.plugin.hyprglass then
    local hg = hl.plugin.hyprglass
    hg.preset("neo-blush", {
        inherits = "subtle",
        blur_strength = 0.55,
        blur_iterations = 1,
        refraction_strength = 0.25,
        chromatic_aberration = 0.04,
        fresnel_strength = 0.15,
        specular_strength = 0.24,
        lens_distortion = 0.02,
        edge_thickness = 0.055,
        glass_opacity = 1.0,
        tint_color = 0xfff3f90c,
        light = {
            brightness = 1.03,
            contrast = 0.98,
            saturation = 0.92,
            adaptive_boost = 0.10,
        },
    })
    hg.config({
        enabled = false,
        default_theme = "light",
        default_preset = "neo-blush",
        layers = { enabled = true },
    })
    -- Application themes keep dense content quiet and navigation translucent.
    -- Opt in the file managers, never all windows.
    hg.preset("neo-files", {
        inherits = "neo-blush",
        blur_strength = 0.50,
        blur_iterations = 1,
        refraction_strength = 0.12,
        chromatic_aberration = 0.0,
        lens_distortion = 0.0,
        fresnel_strength = 0.08,
        specular_strength = 0.12,
        edge_thickness = 0.025,
    })
    for _, tag in ipairs({ "+hyprglass_enabled", "+hyprglass_theme_light", "+hyprglass_preset_neo-files" }) do
        table.insert(neoHyprglassFileRules, hl.window_rule({
            name = "neo-files-" .. tag:sub(2),
            match = { class = fileClass },
            tag = tag,
        }))
    end
    table.insert(neoHyprglassFileRules, hl.window_rule({
        name = "neo-files-glass-blur",
        match = { class = fileClass },
        no_blur = true,
    }))
    hg.layer("waybar", { preset = "neo-blush", mask_threshold = 0.14 })
    hg.layer("neo-control-center", { preset = "neo-blush", mask_threshold = 0.14 })
    hg.layer("rofi", { preset = "neo-blush", mask_threshold = 0.14 })
    if neoHyprglassLayerRule then
        neoHyprglassLayerRule:set_enabled(false)
    end
    neoHyprglassLayerRule = hl.layer_rule({
        name = "neo-hyprglass-surfaces",
        match = { namespace = "^(waybar|neo-control-center|rofi)$" },
        blur = false,
        blur_popups = true,
    })
end
