name=main.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil

from config import Config
from database import DatabaseManager
from file_manager import FileManager

class TagFileApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tag File - Local File Tagging System")
        self.root.geometry("1400x800")
        
        self.config = Config()
        self.db = DatabaseManager(self.config.db_path)
        self.file_manager = FileManager()
        
        self.selected_file_id = None
        self.setup_ui()
        self.refresh_all()
    
    def setup_ui(self):
        """Setup three-panel layout"""
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Import", command=self.import_file).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<Return>', lambda e: self.search_files())
        
        ttk.Button(toolbar, text="🔍 Search", command=self.search_files).pack(side=tk.LEFT, padx=5)
        
        # Main content
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Tags
        left_frame = ttk.LabelFrame(main_frame, text="📁 Tags", width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        left_frame.pack_propagate(False)
        
        self.tag_tree = ttk.Treeview(left_frame, height=35)
        self.tag_tree.pack(fill=tk.BOTH, expand=True)
        self.tag_tree.bind('<Button-1>', self.on_tag_select)
        
        # Middle panel - Files
        middle_frame = ttk.LabelFrame(main_frame, text="📄 Files")
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.file_tree = ttk.Treeview(middle_frame, columns=('Filename', 'Tags'), height=35)
        self.file_tree.heading('#0', text='ID')
        self.file_tree.heading('Filename', text='Filename')
        self.file_tree.heading('Tags', text='Tags')
        self.file_tree.column('#0', width=40)
        self.file_tree.column('Filename', width=250)
        self.file_tree.column('Tags', width=250)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        self.file_tree.bind('<Button-1>', self.on_file_select)
        self.file_tree.bind('<Double-Button-1>', self.on_file_double_click)
        
        # Right panel - Details
        right_frame = ttk.LabelFrame(main_frame, text="📋 Details", width=350)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        right_frame.pack_propagate(False)
        
        ttk.Label(right_frame, text="File Path:", font=(self.config.FONT_FAMILY, 9, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        self.filepath_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.filepath_var, state='readonly').pack(fill=tk.X, padx=5)
        
        ttk.Label(right_frame, text="Filename:", font=(self.config.FONT_FAMILY, 9, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 5))
        self.filename_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.filename_var).pack(fill=tk.X, padx=5)
        
        ttk.Label(right_frame, text="Tags:", font=(self.config.FONT_FAMILY, 9, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 5))
        self.tags_var = tk.StringVar()
        ttk.Entry(right_frame, textvariable=self.tags_var).pack(fill=tk.X, padx=5)
        
        ttk.Label(right_frame, text="Description:", font=(self.config.FONT_FAMILY, 9, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 5))
        self.description_text = tk.Text(right_frame, height=12, width=40)
        self.description_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=10)
        ttk.Button(btn_frame, text="💾 Save", command=self.save_changes).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="🗑️ Delete", command=self.delete_file).pack(side=tk.LEFT, padx=3)
    
    def import_file(self):
        """Import file"""
        file_path = filedialog.askopenfilename()
        if not file_path:
            return
        
        tag = tk.simpledialog.askstring("Tag", "Enter tag (e.g., Finance/Audit/2024):")
        if not tag:
            return
        
        filename = os.path.basename(file_path)
        dest_dir = os.path.join(self.config.DB_ROOT, tag.replace('/', '\\'))
        self.file_manager.create_directory(dest_dir)
        
        dest_path = os.path.join(dest_dir, filename)
        
        if self.file_manager.copy_file(file_path, dest_path):
            self.db.add_file(filename, dest_path, tag)
            self.refresh_all()
            messagebox.showinfo("Success", f"File imported: {filename}")
        else:
            messagebox.showerror("Error", "Failed to import file")
    
    def search_files(self):
        """Search files"""
        query = self.search_var.get()
        if query:
            results = self.db.search_files(query)
            self.populate_file_list(results)
        else:
            self.refresh_file_list()
    
    def on_tag_select(self, event):
        """Select tag"""
        selection = self.tag_tree.selection()
        if selection:
            tag = self.tag_tree.item(selection[0])['text']
            files = self.db.get_files_by_tag(tag)
            self.populate_file_list(files)
    
    def on_file_select(self, event):
        """Select file"""
        selection = self.file_tree.selection()
        if selection:
            file_id = int(self.file_tree.item(selection[0])['text'])
            self.show_file_details(file_id)
    
    def on_file_double_click(self, event):
        """Open file"""
        selection = self.file_tree.selection()
        if selection:
            file_id = int(self.file_tree.item(selection[0])['text'])
            file_data = self.db.get_file_by_id(file_id)
            if file_data:
                filepath = file_data[2]
                if os.path.exists(filepath):
                    os.startfile(filepath)
    
    def show_file_details(self, file_id):
        """Show file details"""
        file_data = self.db.get_file_by_id(file_id)
        if file_data:
            self.selected_file_id = file_id
            self.filepath_var.set(file_data[2])
            self.filename_var.set(file_data[1])
            self.tags_var.set(file_data[3])
            self.description_text.delete('1.0', tk.END)
            self.description_text.insert('1.0', file_data[4])
    
    def save_changes(self):
        """Save changes"""
        if self.selected_file_id is None:
            messagebox.showwarning("Warning", "No file selected")
            return
        
        new_filename = self.filename_var.get()
        new_tags = self.tags_var.get()
        new_description = self.description_text.get('1.0', tk.END).strip()
        
        file_data = self.db.get_file_by_id(self.selected_file_id)
        old_path = file_data[2]
        
        new_path = os.path.join(os.path.dirname(old_path), new_filename)
        
        if new_filename != file_data[1] and os.path.exists(old_path):
            self.file_manager.rename_file(old_path, new_path)
        
        self.db.update_file(self.selected_file_id, new_filename, new_path, new_tags, new_description)
        self.refresh_all()
        messagebox.showinfo("Success", "Changes saved")
    
    def delete_file(self):
        """Delete file"""
        if self.selected_file_id is None:
            messagebox.showwarning("Warning", "No file selected")
            return
        
        if messagebox.askyesno("Confirm", "Delete file record?"):
            delete_physical = messagebox.askyesno("Confirm", "Also delete physical file?")
            
            file_data = self.db.get_file_by_id(self.selected_file_id)
            if file_data and delete_physical:
                filepath = file_data[2]
                if self.file_manager.file_exists(filepath):
                    self.file_manager.delete_file(filepath)
            
            self.db.delete_file(self.selected_file_id)
            self.refresh_all()
            messagebox.showinfo("Success", "File deleted")
    
    def refresh_file_list(self):
        files = self.db.get_all_files()
        self.populate_file_list(files)
    
    def populate_file_list(self, files):
        self.file_tree.delete(*self.file_tree.get_children())
        for file_id, filename, filepath, tags, description in files:
            self.file_tree.insert('', 'end', text=str(file_id), values=(filename, tags))
    
    def refresh_tag_tree(self):
        self.tag_tree.delete(*self.tag_tree.get_children())
        tag_tree_data = self.db.get_tag_tree()
        self.populate_tag_tree(tag_tree_data, '')
    
    def populate_tag_tree(self, tree_data, parent):
        for tag, subtags in tree_data.items():
            item_id = self.tag_tree.insert(parent, 'end', text=tag)
            if subtags:
                self.populate_tag_tree(subtags, item_id)
    
    def refresh_all(self):
        self.refresh_file_list()
        self.refresh_tag_tree()

def main():
    import tkinter.simpledialog
    root = tk.Tk()
    app = TagFileApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()