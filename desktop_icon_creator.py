#!/usr/bin/env python3
"""
Desktop Icon Creator for Ubuntu Desktop
Creates custom desktop and show apps icons for launching shell scripts
Compatible with Ubuntu 24.04.2 LTS

Usage:
  GUI Mode: python3 desktop_icon_creator.py
  CLI Mode: python3 desktop_icon_creator.py --text "My App" --script /path/to/script.sh
  Help:     python3 desktop_icon_creator.py --help
"""

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox, scrolledtext
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import sys

# Check for required dependencies and provide installation instructions
def check_dependencies():
    """Check if required packages are installed"""
    missing = []
    
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        missing.append("pillow")
    
    try:
        import cairosvg
    except ImportError:
        missing.append("cairosvg")
    
    if missing:
        print("Missing required packages. Please install with:")
        print(f"pip3 install {' '.join(missing)}")
        print("or")
        print(f"sudo apt install python3-pip && pip3 install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

from PIL import Image, ImageDraw, ImageFont
import cairosvg

class DesktopIconCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Desktop Icon Creator")
        self.root.geometry("900x875")
        
        # Setup directories - use current working directory
        self.current_dir = Path.cwd()
        self.scripts_dir = self.current_dir / "CustomScripts"
        self.icons_dir = self.current_dir / "CustomIcons"
        self.desktop_dir = Path.home() / "Desktop"
        self.applications_dir = Path.home() / ".local/share/applications"
        
        # Create directories if they don't exist
        for directory in [self.scripts_dir, self.icons_dir, self.applications_dir]:
            directory.mkdir(exist_ok=True)
        
        # Color presets
        self.color_presets = {
            "Red": "#FF0000",
            "Green": "#00FF00", 
            "Blue": "#0000FF",
            "Yellow": "#FFFF00",
            "Purple": "#800080",
            "Orange": "#FFA500",
            "Black": "#000000",
            "White": "#FFFFFF",
            "Gray": "#808080"
        }
        
        # Initialize variables
        self.bg_color = tk.StringVar(value="#4285F4")
        self.bg_color2 = tk.StringVar(value="#1A73E8")  # Second color for gradient
        self.use_gradient = tk.BooleanVar(value=False)
        self.gradient_direction = tk.StringVar(value="diagonal")  # diagonal, horizontal, vertical, radial
        self.border_color = tk.StringVar(value="#FFFFFF")
        self.text_color = tk.StringVar(value="#FFFFFF")
        self.enable_border = tk.BooleanVar(value=True)
        self.icon_text = tk.StringVar()
        self.font_family = tk.StringVar()
        self.font_size = tk.IntVar(value=16)
        self.use_smart_sizing = tk.BooleanVar(value=True)
        self.script_mode = tk.StringVar(value="create")
        self.script_path = tk.StringVar()
        
        self.setup_ui()
        self.get_system_fonts()
        
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="lightyellow",
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
    def setup_ui(self):
        """Setup the user interface with tabs"""
        # Main container with tabs
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Tab 1: Create Icons
        create_frame = ttk.Frame(notebook)
        notebook.add(create_frame, text="Create Icons")
        
        # Tab 2: Manage Icons
        manage_frame = ttk.Frame(notebook)
        notebook.add(manage_frame, text="Manage Icons")
        
        # Setup create tab
        self.setup_create_tab(create_frame)
        
        # Setup manage tab
        self.setup_manage_tab(manage_frame)
        
        # Footer with links
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Create clickable links
        def open_license():
            import webbrowser
            license_path = self.current_dir / "LICENSE"
            if license_path.exists():
                webbrowser.open(f"file://{license_path}")
            else:
                messagebox.showinfo("License", "MIT License - See LICENSE file in project directory")
        
        def open_website():
            import webbrowser
            webbrowser.open("https://dennisconsorte.com/?utm_source=desktopiconcreator&utm_medium=app&utm_campaign=gui")
        
        def open_donate():
            import webbrowser
            webbrowser.open("https://dennisconsorte.com/donate/?utm_source=desktopiconcreator&utm_medium=app&utm_campaign=donate")
        
        license_link = tk.Label(footer_frame, text="License", fg="blue", cursor="hand2")
        license_link.pack(side=tk.LEFT)
        license_link.bind("<Button-1>", lambda e: open_license())
        
        ttk.Label(footer_frame, text=" | ").pack(side=tk.LEFT)
        
        author_link = tk.Label(footer_frame, text="Created by Dennis Consorte", fg="blue", cursor="hand2")
        author_link.pack(side=tk.LEFT)
        author_link.bind("<Button-1>", lambda e: open_website())
        
        ttk.Label(footer_frame, text=" | ").pack(side=tk.LEFT)
        
        donate_link = tk.Label(footer_frame, text="Please Donate", fg="#006400", cursor="hand2", font=("Arial", 9, "bold"))
        donate_link.pack(side=tk.LEFT)
        donate_link.bind("<Button-1>", lambda e: open_donate())
        self.create_tooltip(donate_link, "Support this project! Your donations help fund development and improvements.")
        
        # Initialize UI state
        self.on_script_mode_change()
        self.on_smart_sizing_change()
        self.on_gradient_toggle()

    def setup_create_tab(self, parent):
        """Setup the create icons tab"""
        # Script Section
        script_frame = ttk.LabelFrame(parent, text="Script Configuration", padding=8)
        script_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Script mode selection
        mode_frame = ttk.Frame(script_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        create_radio = ttk.Radiobutton(mode_frame, text="Create new script", 
                       variable=self.script_mode, value="create",
                       command=self.on_script_mode_change)
        create_radio.pack(side=tk.LEFT, padx=(0, 20))
        self.create_tooltip(create_radio, "Create a new shell script by typing commands in the text area below")
        
        existing_radio = ttk.Radiobutton(mode_frame, text="Use existing script", 
                       variable=self.script_mode, value="existing",
                       command=self.on_script_mode_change)
        existing_radio.pack(side=tk.LEFT)
        self.create_tooltip(existing_radio, "Select an existing shell script file from your system")
        
        # Script creation area
        self.script_create_frame = ttk.Frame(script_frame)
        self.script_create_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(self.script_create_frame, text="Enter shell script content:").pack(anchor=tk.W)
        self.script_text = scrolledtext.ScrolledText(self.script_create_frame, height=6, width=70)
        self.script_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.script_text.insert(tk.END, "#!/bin/bash\n# Your script here\necho 'Hello World!'\necho 'Press Enter to close...'\nread")
        
        # Existing script selection
        self.script_existing_frame = ttk.Frame(script_frame)
        
        path_frame = ttk.Frame(self.script_existing_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="Script path:").pack(side=tk.LEFT)
        ttk.Entry(path_frame, textvariable=self.script_path, width=50).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(path_frame, text="Browse", command=self.browse_script).pack(side=tk.LEFT)
        
        # Icon Configuration
        icon_frame = ttk.LabelFrame(parent, text="Icon Configuration", padding=8)
        icon_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Icon text
        text_frame = ttk.Frame(icon_frame)
        text_frame.pack(fill=tk.X, pady=3)
        ttk.Label(text_frame, text="Icon text (max 24 chars):").pack(side=tk.LEFT)
        text_entry = ttk.Entry(text_frame, textvariable=self.icon_text, width=30)
        text_entry.pack(side=tk.LEFT, padx=(10, 0))
        text_entry.bind('<KeyRelease>', self.validate_text_length)
        self.create_tooltip(text_entry, "Enter text for your icon. Use \\n for line breaks (e.g., 'My\\nApp')")
        
        # Color configuration
        colors_frame = ttk.Frame(icon_frame)
        colors_frame.pack(fill=tk.X, pady=8)
        
        # Background color
        bg_frame = ttk.Frame(colors_frame)
        bg_frame.pack(fill=tk.X, pady=2)
        ttk.Label(bg_frame, text="Background color:", width=15).pack(side=tk.LEFT)
        self.bg_color_display = tk.Label(bg_frame, width=3, height=1, bg=self.bg_color.get())
        self.bg_color_display.pack(side=tk.LEFT, padx=(0, 5))
        self.create_color_controls(bg_frame, self.bg_color, self.bg_color_display)
        
        # Gradient options
        gradient_frame = ttk.Frame(colors_frame)
        gradient_frame.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(gradient_frame, text="Use gradient", 
                       variable=self.use_gradient,
                       command=self.on_gradient_toggle).pack(side=tk.LEFT)
        
        self.gradient_controls_frame = ttk.Frame(gradient_frame)
        self.gradient_controls_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(self.gradient_controls_frame, text="End color:").pack(side=tk.LEFT)
        self.bg_color2_display = tk.Label(self.gradient_controls_frame, width=3, height=1, bg=self.bg_color2.get())
        self.bg_color2_display.pack(side=tk.LEFT, padx=(5, 5))
        self.create_color_controls(self.gradient_controls_frame, self.bg_color2, self.bg_color2_display)
        
        # Gradient direction
        gradient_dir_frame = ttk.Frame(colors_frame)
        gradient_dir_frame.pack(fill=tk.X, pady=2)
        self.gradient_dir_frame = gradient_dir_frame
        ttk.Label(gradient_dir_frame, text="Gradient direction:", width=15).pack(side=tk.LEFT)
        direction_combo = ttk.Combobox(gradient_dir_frame, textvariable=self.gradient_direction,
                                     values=["diagonal", "horizontal", "vertical", "radial"],
                                     width=12, state="readonly")
        direction_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # Border color
        border_frame = ttk.Frame(colors_frame)
        border_frame.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(border_frame, text="Enable border", variable=self.enable_border).pack(side=tk.LEFT)
        self.border_color_display = tk.Label(border_frame, width=3, height=1, bg=self.border_color.get())
        self.border_color_display.pack(side=tk.LEFT, padx=(5, 5))
        self.create_color_controls(border_frame, self.border_color, self.border_color_display)
        
        # Text color
        text_color_frame = ttk.Frame(colors_frame)
        text_color_frame.pack(fill=tk.X, pady=2)
        ttk.Label(text_color_frame, text="Text color:", width=15).pack(side=tk.LEFT)
        self.text_color_display = tk.Label(text_color_frame, width=3, height=1, bg=self.text_color.get())
        self.text_color_display.pack(side=tk.LEFT, padx=(0, 5))
        self.create_color_controls(text_color_frame, self.text_color, self.text_color_display)
        
        # Font configuration
        font_frame = ttk.LabelFrame(icon_frame, text="Font Settings", padding=5)
        font_frame.pack(fill=tk.X, pady=8)
        
        font_select_frame = ttk.Frame(font_frame)
        font_select_frame.pack(fill=tk.X, pady=2)
        ttk.Label(font_select_frame, text="Font family:").pack(side=tk.LEFT)
        self.font_combo = ttk.Combobox(font_select_frame, textvariable=self.font_family, width=30)
        self.font_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Checkbutton(font_select_frame, text="Smart sizing", 
                       variable=self.use_smart_sizing,
                       command=self.on_smart_sizing_change).pack(side=tk.LEFT, padx=(0, 10))
        
        self.manual_size_frame = ttk.Frame(font_select_frame)
        self.manual_size_frame.pack(side=tk.LEFT)
        ttk.Label(self.manual_size_frame, text="Size:").pack(side=tk.LEFT)
        ttk.Spinbox(self.manual_size_frame, from_=8, to=72, 
                   textvariable=self.font_size, width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # Preview and Create button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Preview Icon", command=self.preview_icon).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Create Desktop Icon", command=self.create_desktop_icon).pack(side=tk.LEFT)

    def setup_manage_tab(self, parent):
        """Setup the manage icons tab"""
        # Header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Manage Your Desktop Icons", 
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        refresh_button = ttk.Button(header_frame, text="🔄 Refresh", command=self.refresh_icon_list)
        refresh_button.pack(side=tk.RIGHT)
        self.create_tooltip(refresh_button, "Refresh the list of created icons")
        
        # Search/Filter frame
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=30)
        filter_entry.pack(side=tk.LEFT, padx=(5, 0))
        filter_entry.bind('<KeyRelease>', self.filter_icons)
        self.create_tooltip(filter_entry, "Type to filter icons by name")
        
        # Icon list with details
        list_frame = ttk.LabelFrame(parent, text="Created Icons", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for icon list
        columns = ('Name', 'Type', 'Script', 'Created', 'Status')
        self.icon_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # Define column headings and widths
        self.icon_tree.heading('Name', text='Icon Name')
        self.icon_tree.heading('Type', text='Type')
        self.icon_tree.heading('Script', text='Script File')
        self.icon_tree.heading('Created', text='Created')
        self.icon_tree.heading('Status', text='Status')
        
        self.icon_tree.column('Name', width=150)
        self.icon_tree.column('Type', width=100)
        self.icon_tree.column('Script', width=200)
        self.icon_tree.column('Created', width=120)
        self.icon_tree.column('Status', width=100)
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.icon_tree.yview)
        self.icon_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.icon_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Left side buttons
        left_buttons = ttk.Frame(action_frame)
        left_buttons.pack(side=tk.LEFT)
        
        preview_button = ttk.Button(left_buttons, text="👁️ Preview", command=self.preview_selected_icon)
        preview_button.pack(side=tk.LEFT, padx=(0, 5))
        self.create_tooltip(preview_button, "Preview the selected icon")
        
        edit_button = ttk.Button(left_buttons, text="✏️ Edit", command=self.edit_selected_icon)
        edit_button.pack(side=tk.LEFT, padx=(0, 5))
        self.create_tooltip(edit_button, "Edit the selected icon (copies settings to Create tab)")
        
        # Right side buttons
        right_buttons = ttk.Frame(action_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        remove_button = ttk.Button(right_buttons, text="🗑️ Remove Selected", 
                                  command=self.remove_selected_icons)
        remove_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(remove_button, "Remove selected icons from desktop and system")
        
        remove_all_button = ttk.Button(right_buttons, text="🗑️ Remove All", 
                                      command=self.remove_all_icons)
        remove_all_button.pack(side=tk.LEFT, padx=(5, 0))
        self.create_tooltip(remove_all_button, "Remove ALL created icons (use with caution!)")
        
        # Info frame
        info_frame = ttk.LabelFrame(parent, text="Selection Info", padding=5)
        info_frame.pack(fill=tk.X)
        
        self.info_label = ttk.Label(info_frame, text="Select an icon to view details")
        self.info_label.pack(anchor=tk.W)
        
        # Bind selection event
        self.icon_tree.bind('<<TreeviewSelect>>', self.on_icon_select)
        
        # Load initial icon list
        self.refresh_icon_list()

    def refresh_icon_list(self):
        """Refresh the list of created icons"""
        # Clear existing items
        for item in self.icon_tree.get_children():
            self.icon_tree.delete(item)
        
        # Find all created icons
        icons = self.get_created_icons()
        
        for icon_info in icons:
            self.icon_tree.insert('', tk.END, values=(
                icon_info['name'],
                icon_info['type'],
                icon_info['script'],
                icon_info['created'],
                icon_info['status']
            ))
        
        # Update info label
        count = len(icons)
        self.info_label.config(text=f"Found {count} created icon{'s' if count != 1 else ''}")

    def get_created_icons(self):
        """Get list of created icons with their details"""
        icons = []
        
        # Check CustomScripts directory for launchers
        if self.scripts_dir.exists():
            for script_file in self.scripts_dir.glob("*.sh"):
                # Skip the Desktop Icon Creator's own launcher
                if script_file.name == "desktop_icon_creator_launcher.sh":
                    continue
                
                # Look for corresponding icon and desktop files
                base_name = script_file.stem
                icon_file = self.icons_dir / f"{base_name}.png"
                desktop_file = self.applications_dir / f"{base_name}.desktop"
                desktop_copy = self.desktop_dir / f"{base_name}.desktop"
                
                # Determine status
                status = "✓ Active"
                if not icon_file.exists():
                    status = "⚠ Missing Icon"
                elif not desktop_file.exists():
                    status = "⚠ Missing Launcher"
                elif not desktop_copy.exists():
                    status = "⚠ Not on Desktop"
                
                # Get creation time
                try:
                    created_time = script_file.stat().st_mtime
                    created_str = self.format_timestamp(created_time)
                except:
                    created_str = "Unknown"
                
                # Extract name from desktop file if available
                display_name = base_name.replace('_', ' ').title()
                if desktop_file.exists():
                    try:
                        with open(desktop_file, 'r') as f:
                            for line in f:
                                if line.startswith('Name='):
                                    display_name = line.split('=', 1)[1].strip()
                                    break
                    except:
                        pass
                
                icons.append({
                    'name': display_name,
                    'type': 'Custom Script',
                    'script': script_file.name,
                    'created': created_str,
                    'status': status,
                    'base_name': base_name,
                    'script_path': script_file,
                    'icon_path': icon_file,
                    'desktop_path': desktop_file,
                    'desktop_copy_path': desktop_copy
                })
        
        # Sort by creation time (newest first)
        icons.sort(key=lambda x: x['created'], reverse=True)
        return icons

    def format_timestamp(self, timestamp):
        """Format timestamp for display"""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")

    def filter_icons(self, event=None):
        """Filter icons based on search term"""
        search_term = self.filter_var.get().lower()
        
        # Clear and repopulate tree with filtered results
        for item in self.icon_tree.get_children():
            self.icon_tree.delete(item)
        
        icons = self.get_created_icons()
        filtered_icons = []
        
        for icon_info in icons:
            if (search_term in icon_info['name'].lower() or 
                search_term in icon_info['script'].lower() or
                search_term in icon_info['type'].lower()):
                filtered_icons.append(icon_info)
                self.icon_tree.insert('', tk.END, values=(
                    icon_info['name'],
                    icon_info['type'],
                    icon_info['script'],
                    icon_info['created'],
                    icon_info['status']
                ))
        
        # Update info label
        total = len(icons)
        filtered = len(filtered_icons)
        if search_term:
            self.info_label.config(text=f"Showing {filtered} of {total} icons (filtered)")
        else:
            self.info_label.config(text=f"Found {total} created icon{'s' if total != 1 else ''}")

    def on_icon_select(self, event):
        """Handle icon selection"""
        selection = self.icon_tree.selection()
        if not selection:
            self.info_label.config(text="Select an icon to view details")
            return
        
        # Get selected item values
        item = selection[0]
        values = self.icon_tree.item(item, 'values')
        
        if values:
            name, icon_type, script, created, status = values
            self.info_label.config(text=f"Selected: {name} | Status: {status} | Script: {script}")

    def preview_selected_icon(self):
        """Preview the selected icon"""
        selection = self.icon_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an icon to preview")
            return
        
        # Get selected icon details
        item = selection[0]
        values = self.icon_tree.item(item, 'values')
        script_name = values[2]  # Script column
        
        # Find the icon file
        base_name = script_name.replace('.sh', '')
        icon_file = self.icons_dir / f"{base_name}.png"
        
        if icon_file.exists():
            # Open with default image viewer
            subprocess.run(['xdg-open', str(icon_file)])
        else:
            messagebox.showerror("Icon Not Found", f"Icon file not found: {icon_file}")

    def edit_selected_icon(self):
        """Edit the selected icon by copying its settings to the create tab"""
        selection = self.icon_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an icon to edit")
            return
        
        # Get selected icon details
        item = selection[0]
        values = self.icon_tree.item(item, 'values')
        script_name = values[2]  # Script column
        
        # Find the script file
        base_name = script_name.replace('.sh', '')
        script_file = self.scripts_dir / script_name
        
        if script_file.exists():
            try:
                # Read script content
                with open(script_file, 'r') as f:
                    script_content = f.read()
                
                # Set the script content in the create tab
                self.script_text.delete('1.0', tk.END)
                self.script_text.insert('1.0', script_content)
                self.script_mode.set("create")
                
                # Set icon text from name
                display_name = values[0]  # Name column
                self.icon_text.set(display_name)
                
                # Switch to create tab
                # Find the notebook widget and select first tab
                for widget in self.root.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Notebook):
                                child.select(0)  # Select first tab (Create)
                                break
                
                self.on_script_mode_change()
                messagebox.showinfo("Icon Loaded", f"Icon settings loaded for editing. You can now modify and recreate the icon.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load icon for editing: {str(e)}")
        else:
            messagebox.showerror("Script Not Found", f"Script file not found: {script_file}")

    def remove_selected_icons(self):
        """Remove selected icons and their associated files"""
        selection = self.icon_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select icons to remove")
            return
        
        # Confirm removal
        count = len(selection)
        response = messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to remove {count} icon{'s' if count != 1 else ''}?\n\n"
            "This will delete:\n"
            "• Desktop icons\n"
            "• Script files\n"
            "• Icon images\n"
            "• Application launcher entries\n\n"
            "This action cannot be undone!"
        )
        
        if not response:
            return
        
        removed_count = 0
        errors = []
        
        for item in selection:
            try:
                values = self.icon_tree.item(item, 'values')
                script_name = values[2]  # Script column
                base_name = script_name.replace('.sh', '')
                
                # Remove all associated files
                self.remove_icon_files(base_name)
                removed_count += 1
                
            except Exception as e:
                errors.append(f"Failed to remove {values[0]}: {str(e)}")
        
        # Update desktop database
        subprocess.run(['update-desktop-database', str(self.applications_dir)], 
                      capture_output=True)
        
        # Show results
        if errors:
            messagebox.showwarning("Partial Success", 
                                 f"Removed {removed_count} icons.\n\nErrors:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Success", f"Successfully removed {removed_count} icon{'s' if removed_count != 1 else ''}")
        
        # Refresh the list
        self.refresh_icon_list()

    def remove_all_icons(self):
        """Remove ALL created icons"""
        icons = self.get_created_icons()
        if not icons:
            messagebox.showinfo("No Icons", "No icons found to remove")
            return
        
        # Confirm removal with extra warning
        response = messagebox.askyesno(
            "⚠️ REMOVE ALL ICONS ⚠️",
            f"Are you ABSOLUTELY SURE you want to remove ALL {len(icons)} icons?\n\n"
            "This will permanently delete:\n"
            "• ALL desktop icons you've created\n"
            "• ALL script files in CustomScripts/\n"
            "• ALL icon images in CustomIcons/\n"
            "• ALL application launcher entries\n\n"
            "⚠️ THIS ACTION CANNOT BE UNDONE! ⚠️\n\n"
            "Consider backing up your files first.",
            icon='warning'
        )
        
        if not response:
            return
        
        # Final confirmation
        response2 = messagebox.askyesno(
            "Final Confirmation",
            "Last chance!\n\nType 'YES' and click Yes to proceed with removing ALL icons.",
            icon='warning'
        )
        
        if not response2:
            return
        
        removed_count = 0
        errors = []
        
        for icon_info in icons:
            try:
                self.remove_icon_files(icon_info['base_name'])
                removed_count += 1
            except Exception as e:
                errors.append(f"Failed to remove {icon_info['name']}: {str(e)}")
        
        # Update desktop database
        subprocess.run(['update-desktop-database', str(self.applications_dir)], 
                      capture_output=True)
        
        # Show results
        if errors:
            messagebox.showwarning("Partial Success", 
                                 f"Removed {removed_count} icons.\n\nErrors:\n" + "\n".join(errors))
        else:
            messagebox.showinfo("Complete", f"Successfully removed all {removed_count} icons")
        
        # Refresh the list
        self.refresh_icon_list()

    def remove_icon_files(self, base_name):
        """Remove all files associated with an icon"""
        files_to_remove = [
            self.scripts_dir / f"{base_name}.sh",
            self.icons_dir / f"{base_name}.svg",
            self.icons_dir / f"{base_name}.png",
            self.applications_dir / f"{base_name}.desktop",
            self.desktop_dir / f"{base_name}.desktop"
        ]
        
        for file_path in files_to_remove:
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    raise Exception(f"Failed to delete {file_path.name}: {str(e)}")

    def create_color_controls(self, parent, color_var, display_label):
        """Create color selection controls with improved functionality"""
        # Preset colors dropdown
        preset_combo = ttk.Combobox(parent, values=list(self.color_presets.keys()), width=10)
        preset_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        # RGB entry
        rgb_entry = ttk.Entry(parent, width=10)
        rgb_entry.pack(side=tk.LEFT, padx=(0, 5))
        rgb_entry.insert(0, color_var.get().upper())
        
        def on_preset_select(event):
            if preset_combo.get() in self.color_presets:
                hex_color = self.color_presets[preset_combo.get()]
                color_var.set(hex_color)
                display_label.config(bg=hex_color)
                rgb_entry.delete(0, tk.END)
                rgb_entry.insert(0, hex_color.upper())
        
        preset_combo.bind('<<ComboboxSelected>>', on_preset_select)
        
        # Custom color button
        def choose_custom_color():
            color = colorchooser.askcolor(color=color_var.get())[1]
            if color:
                hex_color = color.upper()
                color_var.set(hex_color)
                display_label.config(bg=hex_color)
                rgb_entry.delete(0, tk.END)
                rgb_entry.insert(0, hex_color)
                preset_combo.set("")  # Clear dropdown selection
        
        ttk.Button(parent, text="Custom", command=choose_custom_color).pack(side=tk.LEFT, padx=(0, 5))
        
        def validate_and_update_color(rgb_value):
            """Validate and update color from text input"""
            try:
                rgb_value = rgb_value.strip().upper()
                
                if rgb_value.startswith('#') and len(rgb_value) == 7:
                    # Validate hex format
                    int(rgb_value[1:], 16)  # This will raise ValueError if invalid
                    color_var.set(rgb_value)
                    display_label.config(bg=rgb_value)
                    preset_combo.set("")  # Clear dropdown selection
                    return True
                elif rgb_value.count(',') == 2:  # RGB decimal format
                    r, g, b = map(int, rgb_value.split(','))
                    if all(0 <= val <= 255 for val in [r, g, b]):
                        hex_color = f"#{r:02X}{g:02X}{b:02X}"
                        color_var.set(hex_color)
                        display_label.config(bg=hex_color)
                        rgb_entry.delete(0, tk.END)
                        rgb_entry.insert(0, hex_color)
                        preset_combo.set("")  # Clear dropdown selection
                        return True
                return False
            except (ValueError, tk.TclError):
                return False
        
        def on_rgb_change(event):
            rgb_value = rgb_entry.get()
            if validate_and_update_color(rgb_value):
                rgb_entry.config(bg="white")  # Valid color
            else:
                rgb_entry.config(bg="#ffcccc")  # Invalid color - light red background
        
        def on_rgb_focus_out(event):
            rgb_value = rgb_entry.get()
            if not validate_and_update_color(rgb_value):
                # Revert to current valid color if invalid
                rgb_entry.delete(0, tk.END)
                rgb_entry.insert(0, color_var.get().upper())
                rgb_entry.config(bg="white")
        
        rgb_entry.bind('<KeyRelease>', on_rgb_change)
        rgb_entry.bind('<FocusOut>', on_rgb_focus_out)

    def get_system_fonts(self):
        """Get available system fonts"""
        try:
            # Get system fonts
            result = subprocess.run(['fc-list', ':'], capture_output=True, text=True)
            fonts = set()
            
            for line in result.stdout.split('\n'):
                if ':' in line:
                    font_info = line.split(':')[1]
                    if ',' in font_info:
                        font_name = font_info.split(',')[0].strip()
                    else:
                        font_name = font_info.strip()
                    if font_name and not font_name.startswith('style='):
                        fonts.add(font_name)
            
            # Common fonts to prioritize
            common_fonts = ['Ubuntu', 'DejaVu Sans', 'Liberation Sans', 'Arial', 'Helvetica']
            font_list = []
            
            # Add common fonts first if available
            for font in common_fonts:
                if font in fonts:
                    font_list.append(font)
                    fonts.remove(font)
            
            # Add remaining fonts
            font_list.extend(sorted(fonts))
            
            self.font_combo['values'] = font_list
            if font_list:
                self.font_family.set(font_list[0])
                
        except:
            # Fallback fonts
            self.font_combo['values'] = ['Ubuntu', 'DejaVu Sans', 'Liberation Sans']
            self.font_family.set('Ubuntu')

    def on_script_mode_change(self):
        """Handle script mode change"""
        if self.script_mode.get() == "create":
            self.script_existing_frame.pack_forget()
            self.script_create_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.script_create_frame.pack_forget()
            self.script_existing_frame.pack(fill=tk.X)

    def on_gradient_toggle(self):
        """Handle gradient toggle"""
        if self.use_gradient.get():
            # Show gradient controls
            for widget in [self.gradient_controls_frame, self.gradient_dir_frame]:
                for child in widget.winfo_children():
                    child.config(state="normal" if hasattr(child, 'config') else "normal")
        else:
            # Hide/disable gradient controls  
            for widget in [self.gradient_controls_frame, self.gradient_dir_frame]:
                for child in widget.winfo_children():
                    if hasattr(child, 'config'):
                        try:
                            child.config(state="disabled")
                        except:
                            pass

    def on_smart_sizing_change(self):
        """Handle smart sizing toggle"""
        if self.use_smart_sizing.get():
            self.manual_size_frame.pack_forget()
        else:
            self.manual_size_frame.pack(side=tk.LEFT, padx=(20, 0))

    def validate_text_length(self, event):
        """Validate icon text length"""
        text = self.icon_text.get()
        if len(text) > 24:
            self.icon_text.set(text[:24])

    def browse_script(self):
        """Browse for existing script file"""
        filename = filedialog.askopenfilename(
            title="Select Shell Script",
            filetypes=[("Shell scripts", "*.sh"), ("All files", "*.*")],
            initialdir=str(self.current_dir)
        )
        if filename:
            self.script_path.set(filename)
        
        # Make the dialog bigger by setting a custom geometry
        # Note: This affects the next dialog that opens
        if hasattr(self.root, 'tk'):
            self.root.option_add('*Dialog.msg.width', '50c')
            self.root.option_add('*Dialog.msg.height', '20c')

    def calculate_smart_font_size(self, text, icon_size=128):
        """Calculate appropriate font size based on text length"""
        base_size = 16
        if len(text) <= 8:
            return min(base_size + 4, 20)
        elif len(text) <= 12:
            return base_size
        elif len(text) <= 16:
            return max(base_size - 2, 12)
        elif len(text) <= 20:
            return max(base_size - 4, 10)
        else:
            return max(base_size - 6, 8)

    def create_svg_icon(self, text, bg_color, text_color, border_color, enable_border, 
                       font_family, font_size, use_gradient=False, bg_color2=None, gradient_direction="diagonal"):
        """Create SVG icon with optional gradient support"""
        size = 128
        
        # Create SVG
        svg = ET.Element('svg', {
            'width': str(size),
            'height': str(size),
            'viewBox': f'0 0 {size} {size}',
            'xmlns': 'http://www.w3.org/2000/svg'
        })
        
        # Add gradient definition if needed
        fill_value = bg_color
        if use_gradient and bg_color2:
            defs = ET.SubElement(svg, 'defs')
            
            if gradient_direction == "radial":
                gradient = ET.SubElement(defs, 'radialGradient', {
                    'id': 'bgGradient',
                    'cx': '50%',
                    'cy': '50%',
                    'r': '70%'
                })
            else:
                # Linear gradients
                gradient_coords = {
                    'diagonal': {'x1': '0%', 'y1': '0%', 'x2': '100%', 'y2': '100%'},
                    'horizontal': {'x1': '0%', 'y1': '0%', 'x2': '100%', 'y2': '0%'},
                    'vertical': {'x1': '0%', 'y1': '0%', 'x2': '0%', 'y2': '100%'}
                }
                
                coords = gradient_coords.get(gradient_direction, gradient_coords['diagonal'])
                gradient = ET.SubElement(defs, 'linearGradient', {
                    'id': 'bgGradient',
                    **coords
                })
            
            # Add gradient stops
            ET.SubElement(gradient, 'stop', {
                'offset': '0%',
                'style': f'stop-color:{bg_color};stop-opacity:1'
            })
            ET.SubElement(gradient, 'stop', {
                'offset': '100%',
                'style': f'stop-color:{bg_color2};stop-opacity:1'
            })
            
            fill_value = 'url(#bgGradient)'
        
        # Background rectangle
        rect_attrs = {
            'width': str(size),
            'height': str(size),
            'fill': fill_value,
            'rx': '8'  # Rounded corners
        }
        
        if enable_border:
            rect_attrs.update({
                'stroke': border_color,
                'stroke-width': '2'
            })
        
        ET.SubElement(svg, 'rect', rect_attrs)
        
        # Text with line break support
        text_lines = text.replace('\\n', '\n').split('\n')
        line_count = len(text_lines)
        
        # Calculate vertical positioning for multiple lines
        if line_count == 1:
            y_start = size // 2 + font_size // 3
        else:
            total_text_height = (line_count * font_size) + ((line_count - 1) * font_size * 0.2)
            y_start = (size - total_text_height) // 2 + font_size
        
        for i, line in enumerate(text_lines):
            if line.strip():  # Only create text elements for non-empty lines
                y_pos = y_start + (i * font_size * 1.2)
                text_element = ET.SubElement(svg, 'text', {
                    'x': str(size // 2),
                    'y': str(int(y_pos)),
                    'text-anchor': 'middle',
                    'font-family': font_family,
                    'font-size': str(font_size),
                    'fill': text_color,
                    'font-weight': 'bold'
                })
                text_element.text = line.strip()
        
        return ET.tostring(svg, encoding='unicode')

    def preview_icon(self):
        """Preview the icon"""
        if not self.icon_text.get().strip():
            messagebox.showerror("Error", "Please enter icon text")
            return
        
        # Calculate font size
        if self.use_smart_sizing.get():
            font_size = self.calculate_smart_font_size(self.icon_text.get())
        else:
            font_size = self.font_size.get()
        
        # Create SVG
        svg_content = self.create_svg_icon(
            self.icon_text.get(),
            self.bg_color.get(),
            self.text_color.get(),
            self.border_color.get() if self.enable_border.get() else None,
            self.enable_border.get(),
            self.font_family.get(),
            font_size,
            self.use_gradient.get(),
            self.bg_color2.get(),
            self.gradient_direction.get()
        )
        
        # Convert to PNG for preview
        try:
            png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
            
            # Save temporary file and show
            temp_path = "/tmp/icon_preview.png"
            with open(temp_path, 'wb') as f:
                f.write(png_data)
            
            # Open with default image viewer
            subprocess.run(['xdg-open', temp_path])
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Could not create preview: {str(e)}")

    def create_desktop_icon(self):
        """Create the desktop icon and launcher"""
        # Validation
        if not self.icon_text.get().strip():
            messagebox.showerror("Error", "Please enter icon text")
            return
        
        if self.script_mode.get() == "create":
            script_content = self.script_text.get('1.0', tk.END).strip()
            if not script_content:
                messagebox.showerror("Error", "Please enter script content")
                return
        else:
            if not self.script_path.get() or not os.path.exists(self.script_path.get()):
                messagebox.showerror("Error", "Please select a valid script file")
                return
        
        try:
            # Create unique name
            base_name = re.sub(r'[^a-zA-Z0-9]', '_', self.icon_text.get())
            
            # Handle script
            if self.script_mode.get() == "create":
                script_file = self.scripts_dir / f"{base_name}.sh"
                with open(script_file, 'w') as f:
                    f.write(self.script_text.get('1.0', tk.END))
                os.chmod(script_file, 0o755)
                script_path = str(script_file)
            else:
                script_path = self.script_path.get()
            
            # Calculate font size
            if self.use_smart_sizing.get():
                font_size = self.calculate_smart_font_size(self.icon_text.get())
            else:
                font_size = self.font_size.get()
            
            # Create SVG
            svg_content = self.create_svg_icon(
                self.icon_text.get(),
                self.bg_color.get(),
                self.text_color.get(),
                self.border_color.get() if self.enable_border.get() else None,
                self.enable_border.get(),
                self.font_family.get(),
                font_size,
                self.use_gradient.get(),
                self.bg_color2.get(),
                self.gradient_direction.get()
            )
            
            # Save SVG and convert to PNG
            svg_file = self.icons_dir / f"{base_name}.svg"
            png_file = self.icons_dir / f"{base_name}.png"
            
            with open(svg_file, 'w') as f:
                f.write(svg_content)
            
            png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
            with open(png_file, 'wb') as f:
                f.write(png_data)
            
            # Create desktop file
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={self.icon_text.get()}
Comment=Custom launcher for {self.icon_text.get()}
Exec={script_path}
Icon={png_file}
Terminal=true
StartupNotify=true
Categories=Utility;
"""
            
            # Save to applications directory
            desktop_file = self.applications_dir / f"{base_name}.desktop"
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            os.chmod(desktop_file, 0o755)
            
            # Copy to desktop
            desktop_copy = self.desktop_dir / f"{base_name}.desktop"
            with open(desktop_copy, 'w') as f:
                f.write(desktop_content)
            os.chmod(desktop_copy, 0o755)
            
            # Trust the desktop file
            subprocess.run(['gio', 'set', str(desktop_copy), 'metadata::trusted', 'true'], 
                         capture_output=True)
            
            # Update desktop database
            subprocess.run(['update-desktop-database', str(self.applications_dir)], 
                         capture_output=True)
            
            # Refresh the manage tab if it exists
            if hasattr(self, 'icon_tree'):
                self.refresh_icon_list()
            
            # Show success message
            response = messagebox.askyesno(
                "Success", 
                f"Desktop icon '{self.icon_text.get()}' created successfully!\n\n"
                f"Available on Desktop and in Show Apps.\n"
                f"Icon saved to: {png_file}\n"
                f"Script: {script_path}\n\n"
                f"Would you like to create another icon?"
            )
            
            if response:
                self.reset_form()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create desktop icon: {str(e)}")

    def reset_form(self):
        """Reset the form for creating another icon"""
        self.icon_text.set("")
        self.script_text.delete('1.0', tk.END)
        self.script_text.insert(tk.END, "#!/bin/bash\n# Your script here\necho 'Hello World!'\necho 'Press Enter to close...'\nread")
        self.script_path.set("")
        self.script_mode.set("create")
        self.use_gradient.set(False)
        self.bg_color.set("#4285F4")
        self.bg_color2.set("#1A73E8")
        self.gradient_direction.set("diagonal")
        self.on_script_mode_change()
        self.on_gradient_toggle()

def create_icon_cli(args):
    """Create icon from command line arguments"""
    import argparse
    
    # Validate required arguments
    if not args.text:
        print("Error: Icon text is required (--text)")
        return False
    
    if not args.script and not args.script_content:
        print("Error: Either --script or --script-content is required")
        return False
    
    if len(args.text) > 24:
        print("Error: Icon text must be 24 characters or less")
        return False
    
    # Setup directories
    current_dir = Path.cwd()
    scripts_dir = current_dir / "CustomScripts"
    icons_dir = current_dir / "CustomIcons"
    desktop_dir = Path.home() / "Desktop"
    applications_dir = Path.home() / ".local/share/applications"
    
    for directory in [scripts_dir, icons_dir, applications_dir]:
        directory.mkdir(exist_ok=True)
    
    try:
        # Handle script
        if args.script_content:
            # Create script from content
            import re
            base_name = re.sub(r'[^a-zA-Z0-9]', '_', args.text)
            script_file = scripts_dir / f"{base_name}.sh"
            with open(script_file, 'w') as f:
                if not args.script_content.startswith('#!'):
                    f.write("#!/bin/bash\n")
                f.write(args.script_content)
            os.chmod(script_file, 0o755)
            script_path = str(script_file)
            print(f"✓ Created script: {script_file}")
        else:
            # Use existing script
            if not os.path.exists(args.script):
                print(f"Error: Script file not found: {args.script}")
                return False
            script_path = args.script
            print(f"✓ Using existing script: {script_path}")
        
        # Calculate font size
        if args.smart_sizing:
            if len(args.text) <= 8:
                font_size = min(16 + 4, 20)
            elif len(args.text) <= 12:
                font_size = 16
            elif len(args.text) <= 16:
                font_size = max(16 - 2, 12)
            elif len(args.text) <= 20:
                font_size = max(16 - 4, 10)
            else:
                font_size = max(16 - 6, 8)
        else:
            font_size = args.font_size
        
        print(f"✓ Using font size: {font_size}")
        
        # Create SVG icon
        size = 128
        svg = ET.Element('svg', {
            'width': str(size),
            'height': str(size),
            'viewBox': f'0 0 {size} {size}',
            'xmlns': 'http://www.w3.org/2000/svg'
        })
        
        # Add gradient definition if needed
        fill_value = args.bg_color
        if args.gradient and args.gradient_color2:
            defs = ET.SubElement(svg, 'defs')
            
            if args.gradient_direction == "radial":
                gradient = ET.SubElement(defs, 'radialGradient', {
                    'id': 'bgGradient',
                    'cx': '50%',
                    'cy': '50%',
                    'r': '70%'
                })
            else:
                # Linear gradients
                gradient_coords = {
                    'diagonal': {'x1': '0%', 'y1': '0%', 'x2': '100%', 'y2': '100%'},
                    'horizontal': {'x1': '0%', 'y1': '0%', 'x2': '100%', 'y2': '0%'},
                    'vertical': {'x1': '0%', 'y1': '0%', 'x2': '0%', 'y2': '100%'}
                }
                
                coords = gradient_coords.get(args.gradient_direction, gradient_coords['diagonal'])
                gradient = ET.SubElement(defs, 'linearGradient', {
                    'id': 'bgGradient',
                    **coords
                })
            
            # Add gradient stops
            ET.SubElement(gradient, 'stop', {
                'offset': '0%',
                'style': f'stop-color:{args.bg_color};stop-opacity:1'
            })
            ET.SubElement(gradient, 'stop', {
                'offset': '100%',
                'style': f'stop-color:{args.gradient_color2};stop-opacity:1'
            })
            
            fill_value = 'url(#bgGradient)'
            print(f"✓ Created {args.gradient_direction} gradient: {args.bg_color} → {args.gradient_color2}")
        
        # Background rectangle
        rect_attrs = {
            'width': str(size),
            'height': str(size),
            'fill': fill_value,
            'rx': '8'
        }
        
        if not args.no_border:
            rect_attrs.update({
                'stroke': args.border_color,
                'stroke-width': '2'
            })
        
        ET.SubElement(svg, 'rect', rect_attrs)
        
        # Text with line break support
        text_lines = args.text.replace('\\n', '\n').split('\n')
        line_count = len(text_lines)
        
        # Calculate vertical positioning for multiple lines
        if line_count == 1:
            y_start = size // 2 + font_size // 3
        else:
            total_text_height = (line_count * font_size) + ((line_count - 1) * font_size * 0.2)
            y_start = (size - total_text_height) // 2 + font_size
        
        for i, line in enumerate(text_lines):
            if line.strip():  # Only create text elements for non-empty lines
                y_pos = y_start + (i * font_size * 1.2)
                text_element = ET.SubElement(svg, 'text', {
                    'x': str(size // 2),
                    'y': str(int(y_pos)),
                    'text-anchor': 'middle',
                    'font-family': args.font_family,
                    'font-size': str(font_size),
                    'fill': args.text_color,
                    'font-weight': 'bold'
                })
                text_element.text = line.strip()
        
        svg_content = ET.tostring(svg, encoding='unicode')
        
        # Create unique name
        import re
        base_name = re.sub(r'[^a-zA-Z0-9]', '_', args.text)
        
        # Save SVG and convert to PNG
        svg_file = icons_dir / f"{base_name}.svg"
        png_file = icons_dir / f"{base_name}.png"
        
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        # Convert SVG to PNG
        import cairosvg
        png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
        with open(png_file, 'wb') as f:
            f.write(png_data)
        
        print(f"✓ Created icon: {png_file}")
        
        # Create desktop file
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={args.text}
Comment=Custom launcher for {args.text}
Exec={script_path}
Icon={png_file}
Terminal=true
StartupNotify=true
Categories=Utility;
"""
        
        # Save to applications directory
        desktop_file = applications_dir / f"{base_name}.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        os.chmod(desktop_file, 0o755)
        
        # Copy to desktop
        desktop_copy = desktop_dir / f"{base_name}.desktop"
        with open(desktop_copy, 'w') as f:
            f.write(desktop_content)
        os.chmod(desktop_copy, 0o755)
        
        # Trust the desktop file
        subprocess.run(['gio', 'set', str(desktop_copy), 'metadata::trusted', 'true'], 
                     capture_output=True)
        
        # Update desktop database
        subprocess.run(['update-desktop-database', str(applications_dir)], 
                     capture_output=True)
        
        print(f"✓ Desktop entry created: {desktop_file}")
        print(f"✓ Desktop icon created: {desktop_copy}")
        print("✓ Icon available on Desktop and in Show Apps")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to create icon: {str(e)}")
        return False

def create_self_icon():
    """Create desktop icon for the Desktop Icon Creator itself (CLI mode)"""
    import argparse
    
    # Create directories if they don't exist
    current_dir = Path.cwd()
    scripts_dir = current_dir / "CustomScripts"
    icons_dir = current_dir / "CustomIcons"
    desktop_dir = Path.home() / "Desktop"
    applications_dir = Path.home() / ".local/share/applications"
    
    for directory in [scripts_dir, icons_dir, applications_dir]:
        directory.mkdir(exist_ok=True)
    
    try:
        # Create the launcher script
        script_content = f"""#!/bin/bash
# Desktop Icon Creator Launcher
cd "{current_dir}"
if [ -d "venv" ]; then
    source venv/bin/activate
    python3 desktop_icon_creator.py
else
    python3 desktop_icon_creator.py
fi
"""
        
        script_file = scripts_dir / "desktop_icon_creator_launcher.sh"
        with open(script_file, 'w') as f:
            f.write(script_content)
        os.chmod(script_file, 0o755)
        
        # Create SVG icon
        svg_content = """<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4285F4;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1A73E8;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="128" height="128" fill="url(#grad1)" rx="12" stroke="white" stroke-width="3"/>
  <text x="64" y="42" text-anchor="middle" font-family="Ubuntu" font-size="22" fill="white" font-weight="bold">Desktop</text>
  <text x="64" y="68" text-anchor="middle" font-family="Ubuntu" font-size="22" fill="white" font-weight="bold">Icon</text>
  <text x="64" y="94" text-anchor="middle" font-family="Ubuntu" font-size="22" fill="white" font-weight="bold">Creator</text>
</svg>"""
        
        # Save SVG and convert to PNG
        svg_file = icons_dir / "desktop_icon_creator.svg"
        png_file = icons_dir / "desktop_icon_creator.png"
        
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        # Convert SVG to PNG
        import cairosvg
        png_data = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
        with open(png_file, 'wb') as f:
            f.write(png_data)
        
        # Create desktop file
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Desktop Icon Creator
Comment=Create custom desktop icons for shell scripts
Exec={script_file}
Icon={png_file}
Terminal=false
StartupNotify=true
Categories=Utility;Development;
Keywords=desktop;icon;launcher;script;
"""
        
        # Save to applications directory
        desktop_file = applications_dir / "desktop_icon_creator.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        os.chmod(desktop_file, 0o755)
        
        # Copy to desktop
        desktop_copy = desktop_dir / "desktop_icon_creator.desktop"
        with open(desktop_copy, 'w') as f:
            f.write(desktop_content)
        os.chmod(desktop_copy, 0o755)
        
        # Trust the desktop file
        subprocess.run(['gio', 'set', str(desktop_copy), 'metadata::trusted', 'true'], 
                     capture_output=True)
        
        # Update desktop database
        subprocess.run(['update-desktop-database', str(applications_dir)], 
                     capture_output=True)
        
        print("✓ Desktop Icon Creator icon created successfully!")
        print(f"✓ Launcher script: {script_file}")
        print(f"✓ Icon: {png_file}")
        print("✓ Available on Desktop and in Show Apps")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create self icon: {str(e)}")
        return False

def main():
    import sys
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Desktop Icon Creator - Create custom desktop icons for shell scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch GUI
  python3 desktop_icon_creator.py
  
  # Create simple icon from existing script
  python3 desktop_icon_creator.py --text "My App" --script /path/to/script.sh
  
  # Create icon with inline script content
  python3 desktop_icon_creator.py --text "Hello" --script-content "echo 'Hello World!'"
  
  # Create gradient icon with custom colors
  python3 desktop_icon_creator.py --text "Gradient" --script-content "echo 'test'" \\
    --gradient --bg-color "#FF0000" --gradient-color2 "#FFFF00" --gradient-direction horizontal
  
  # Create icon with custom font and no border
  python3 desktop_icon_creator.py --text "Custom" --script ./test.sh \\
    --font-family "Ubuntu Mono" --font-size 14 --no-border --text-color "#FFFFFF"
  
  # Create the Desktop Icon Creator's own icon
  python3 desktop_icon_creator.py --create-self-icon
        """)
    
    # Special flags
    parser.add_argument('--create-self-icon', action='store_true',
                       help='Create desktop icon for Desktop Icon Creator itself')
    
    # Required content
    parser.add_argument('--text', '-t', type=str,
                       help='Icon text (max 24 characters)')
    
    # Script options (mutually exclusive)
    script_group = parser.add_mutually_exclusive_group()
    script_group.add_argument('--script', '-s', type=str,
                             help='Path to existing shell script')
    script_group.add_argument('--script-content', '-c', type=str,
                             help='Shell script content (will create new script)')
    
    # Color options
    parser.add_argument('--bg-color', type=str, default='#4285F4',
                       help='Background color (hex, RGB, or preset name) [default: #4285F4]')
    parser.add_argument('--text-color', type=str, default='#FFFFFF',
                       help='Text color (hex, RGB, or preset name) [default: #FFFFFF]')
    parser.add_argument('--border-color', type=str, default='#FFFFFF',
                       help='Border color (hex, RGB, or preset name) [default: #FFFFFF]')
    parser.add_argument('--no-border', action='store_true',
                       help='Disable border')
    
    # Gradient options
    parser.add_argument('--gradient', action='store_true',
                       help='Enable gradient background')
    parser.add_argument('--gradient-color2', type=str, default='#1A73E8',
                       help='Second gradient color [default: #1A73E8]')
    parser.add_argument('--gradient-direction', type=str, 
                       choices=['diagonal', 'horizontal', 'vertical', 'radial'],
                       default='diagonal',
                       help='Gradient direction [default: diagonal]')
    
    # Font options
    parser.add_argument('--font-family', type=str, default='Ubuntu',
                       help='Font family [default: Ubuntu]')
    parser.add_argument('--font-size', type=int, default=16,
                       help='Font size [default: 16]')
    parser.add_argument('--smart-sizing', action='store_true', default=True,
                       help='Enable smart font sizing based on text length [default: enabled]')
    parser.add_argument('--no-smart-sizing', dest='smart_sizing', action='store_false',
                       help='Disable smart font sizing')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle special case: create self icon
    if args.create_self_icon:
        return create_self_icon()
    
    # If no arguments provided, launch GUI
    if len(sys.argv) == 1:
        # Check if running on Ubuntu/Linux for GUI mode
        if not os.path.exists('/usr/bin/gio'):
            print("Error: This application is designed for Ubuntu Desktop with GNOME.")
            return False
        
        root = tk.Tk()
        app = DesktopIconCreator(root)
        root.mainloop()
        return True
    
    # CLI mode - validate and create icon
    if not args.text and not args.create_self_icon:
        parser.error("--text is required for creating icons")
    
    if not args.script and not args.script_content and not args.create_self_icon:
        parser.error("Either --script or --script-content is required")
    
    # Process color presets
    color_presets = {
        "red": "#FF0000", "green": "#00FF00", "blue": "#0000FF",
        "yellow": "#FFFF00", "purple": "#800080", "orange": "#FFA500",
        "black": "#000000", "white": "#FFFFFF", "gray": "#808080"
    }
    
    # Convert color names to hex
    for color_attr in ['bg_color', 'text_color', 'border_color', 'gradient_color2']:
        color_value = getattr(args, color_attr).lower()
        if color_value in color_presets:
            setattr(args, color_attr, color_presets[color_value])
    
    # Check for system dependencies in CLI mode
    if not os.path.exists('/usr/bin/gio'):
        print("Error: This application requires Ubuntu Desktop with GNOME.")
        print("Missing system dependencies. Please run on Ubuntu Desktop.")
        return False
    
    # Create icon via CLI
    return create_icon_cli(args)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
