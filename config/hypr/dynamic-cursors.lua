-- Apple-style shake to find, using the compositor's native cursor plugin.
local plugin = os.getenv("HOME") .. "/.local/lib/hyprland/plugins/dynamic-cursors.so"
-- Declare the plugin on every parse. Omitting a loaded config plugin makes
-- Hyprland unload it; the next reload loads it again and repeats indefinitely.
local file = io.open(plugin, "rb")
if file then
    file:close()
    hl.plugin.load(plugin)
end

if hl.plugin.dynamic_cursors then
    hl.config({ plugin = { dynamic_cursors = {
        enabled = true,
        mode = "none",
        shake = {
            enabled = true,
            threshold = 3.0,
            base = 2.5,
            speed = 1.0,
            limit = 3.0,
            timeout = 1400,
            effects = false,
        },
        hyprcursor = {
            enabled = false,
            nearest = 0,
        },
    } } })
end
