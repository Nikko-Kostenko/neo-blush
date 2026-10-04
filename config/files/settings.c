#include <gtk/gtk.h>

/* GTK settings are applied once in this native process, without global changes. */
void gtk_module_init (gint *argc, gchar ***argv)
{
    (void) argc;
    (void) argv;
    g_object_set (gtk_settings_get_default (),
                  "gtk-icon-theme-name", "NeoBlushFiles",
                  "gtk-font-name", "SF Pro Text 11",
                  NULL);
}
