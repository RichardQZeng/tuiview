"""
BERATools Plugin for TuiView

This plugin integrates BERATools into TuiView, providing dockable panels
for tool selection, parameter configuration, and execution.
"""

with open("beratools_plugin_debug.log", "a") as f:
    f.write("[DEBUG] beratools_plugin.py imported\n")
print("[DEBUG] beratools_plugin.py imported")

from PySide6.QtCore import Qt, QTimer

# Import dock panel classes
try:
    from .beratools_panel import BERAToolsPanel, LogPanel
except ImportError:
    try:
        from beratools_panel import BERAToolsPanel, LogPanel
    except ImportError as e:
        print(f"[BERATools] Error importing panel classes: {e}")
        BERAToolsPanel = None
        LogPanel = None

# ============================================
# Required TuiView Plugin Interface Functions
# ============================================

def name():
    """Return plugin display name."""
    return "BERATools"


def author():
    """Return plugin author."""
    return "AppliedGRG"


def description():
    """Return plugin description."""
    return "Integration of BERATools tools into TuiView for geospatial analysis"


def action(actioncode, param):
    with open("beratools_plugin_debug.log", "a") as f:
        f.write(f"[DEBUG] beratools_plugin.py action called with code: {actioncode}\n")
    print(f"[DEBUG] beratools_plugin.py action called with code: {actioncode}")
    """
    Main plugin action handler.
    
    Args:
        actioncode: PLUGIN_ACTION_* constant
            0 = PLUGIN_ACTION_INIT (TuiView startup)
            1 = PLUGIN_ACTION_NEWVIEWER (new ViewerWindow created)
            2 = PLUGIN_ACTION_NEWQUERY (new query window)
        param: Action-specific parameter (ViewerWindow for NEWVIEWER)
    """
    if actioncode == 1:  # PLUGIN_ACTION_NEWVIEWER
        viewer_window = param
        _on_viewer_created(viewer_window)


# ============================================
# Plugin Implementation
# ============================================

def _on_viewer_created(viewer_window):
    """
    Initialize BERATools UI when a new ViewerWindow is created.
    
    Args:
        viewer_window: The ViewerWindow instance
    """
    print("[BERATools] ViewerWindow created, initializing plugin...")
    
    if BERAToolsPanel is None or LogPanel is None:
        print("[BERATools] ERROR: Panel classes not loaded, cannot initialize")
        return
    
    # Store reference to viewer window for later use
    global _viewer_window_ref
    _viewer_window_ref = viewer_window
    
    # Create dock panels
    try:
        beratools_panel = BERAToolsPanel(viewer_window)
        log_panel = LogPanel(viewer_window)
        
        # Add panels to viewer window
        viewer_window.addDockWidget(Qt.LeftDockWidgetArea, beratools_panel)
        viewer_window.addDockWidget(Qt.BottomDockWidgetArea, log_panel)
        
        # Make panels visible by default
        beratools_panel.show()
        log_panel.show()
        
        # Ensure panels are visible after layout updates
        # Use QTimer to defer visibility confirmation
        QTimer.singleShot(500, lambda: (
            beratools_panel.show(),
            log_panel.show()
        ))
        
        # Connect signals between panels
        beratools_panel.output_received.connect(log_panel.append_log)
        beratools_panel.progress_updated.connect(log_panel.set_progress)
        
        # Store references globally for later access
        global _beratools_panel, _log_panel
        _beratools_panel = beratools_panel
        _log_panel = log_panel
        
        print("[BERATools] Dock panels created and added")

        # Add a menu item to control panel visibility
        _add_menu_action(viewer_window)

        print("[BERATools] Plugin initialized successfully")
        
    except Exception as e:
        print(f"[BERATools] ERROR initializing panels: {e}")
        import traceback
        traceback.print_exc()

def _add_menu_action(viewer_window):
    """Adds a menu item to the Tools menu to show the panels."""
    try:
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMenu

        tools_menu = None
        # --- DEBUG: List all available menus ---
        print("[BERATools DEBUG] Found menus:")
        all_menus = viewer_window.menuBar().findChildren(QMenu)
        for menu in all_menus:
            print(f"[BERATools DEBUG]  - '{menu.title()}'")
        # --- END DEBUG ---

        # Find the 'Tools' menu, which might be named '&Tools'
        for menu in all_menus:
            if menu.title().replace('&', '').lower() == 'tools':
                tools_menu = menu
                break
        
        if not tools_menu:
            print("[BERATools] 'Tools' menu not found. Cannot add menu item.")
            return

        def show_panels():
            """Shows and raises the BERATools panels."""
            global _beratools_panel, _log_panel
            if _beratools_panel:
                _beratools_panel.show()
                _beratools_panel.raise_()
            if _log_panel:
                _log_panel.show()
                _log_panel.raise_()

        action = QAction("Show BERATools Panels", viewer_window)
        action.triggered.connect(show_panels)
        tools_menu.addAction(action)

        print("[BERATools] 'Show BERATools Panels' menu item added to Tools menu.")

    except Exception as e:
        print(f"[BERATools] ERROR adding menu item: {e}")
        import traceback
        traceback.print_exc()
