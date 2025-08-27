"""Tree widget helper functions for the tournament application."""
from typing import Dict, List, Optional, Tuple, cast
import tkinter as tk
from tkinter import ttk

def create_scrolled_treeview(
    parent: ttk.Frame,
    columns: List[str],
    headings: Dict[str, str],
    column_widths: Dict[str, int]
) -> Tuple[ttk.Frame, ttk.Treeview]:
    """Create a treeview with a scrollbar and configured columns.
    
    Args:
        parent: The parent frame
        columns: List of column IDs
        headings: Dict mapping column IDs to heading text
        column_widths: Dict mapping column IDs to widths
        
    Returns:
        Tuple of (frame, treeview)
    """
    frame = ttk.Frame(parent)
    
    # Create tree with columns
    tree = ttk.Treeview(frame, columns=tuple(columns), show='headings', selectmode='browse')
    
    # Configure scrollbar
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    # Configure columns
    for col in columns:
        tree.heading(col, text=headings.get(col, col))
        tree.column(col, width=column_widths.get(col, 100))
    
    # Pack components
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    frame.pack(fill=tk.BOTH, expand=True)
    return frame, tree
