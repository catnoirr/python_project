import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk, ImageSequence
import sqlite3
from cryptography.fernet import Fernet
import os
from tkinter import ttk
import sys

# Function to get the absolute path for PyInstaller
def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Generate and save key if not exists
def load_or_generate_key():
    key_path = resource_path('secret.key')
    if os.path.exists(key_path):
        with open(key_path, 'rb') as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(key_path, 'wb') as key_file:
            key_file.write(key)
        return key

key = load_or_generate_key()

def encrypt_password(password):
    f = Fernet(key)
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    f = Fernet(key)
    return f.decrypt(encrypted_password.encode()).decode()

# Initialize database
def init_db():
    conn = sqlite3.connect(resource_path('passwords.db'))
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS passwords
                 (id INTEGER PRIMARY KEY, service TEXT, username TEXT, password TEXT)''')
    conn.commit()
    conn.close()

# Save or update password in the database
def save_or_update_password(service, username, password):
    conn = sqlite3.connect(resource_path('passwords.db'))
    c = conn.cursor()
    encrypted_password = encrypt_password(password)
    c.execute("SELECT id FROM passwords WHERE service=? AND username=?", (service, username))
    result = c.fetchone()
    if result:
        update = messagebox.askyesno("Entry Exists", "An entry with this service and username already exists. Do you want to update the password?")
        if update:
            c.execute("UPDATE passwords SET password=? WHERE id=?", (encrypted_password, result[0]))
            messagebox.showinfo("Success", "Password updated successfully!")
    else:
        c.execute("INSERT INTO passwords (service, username, password) VALUES (?, ?, ?)", (service, username, encrypted_password))
        messagebox.showinfo("Success", "Password saved successfully!")
    conn.commit()
    conn.close()

# Retrieve password from database using service or username
def get_password(input_value):
    conn = sqlite3.connect(resource_path('passwords.db'))
    c = conn.cursor()
    c.execute("SELECT service, username, password FROM passwords WHERE service=? OR username=?", (input_value, input_value))
    results = c.fetchall()
    conn.close()
    if results:
        return results
    return None

# Decrypt the password
def decrypt_result(result):
    service, username, encrypted_password = result
    try:
        decrypted_password = decrypt_password(encrypted_password)
        return service, username, decrypted_password
    except Exception as e:
        messagebox.showerror("Error", "Failed to decrypt password.")
    return None, None, None

# Main application class
class PasswordManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Manager")
        self.root.geometry('400x500')

        # Center the grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(9, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Load GIF image and extract frames
        self.logo_image = Image.open(resource_path("gif/6.gif"))
        self.frames = [ImageTk.PhotoImage(frame.resize((150, 150), Image.Resampling.LANCZOS)) for frame in ImageSequence.Iterator(self.logo_image)]
        self.frame_index = 0

        # Load Loading GIF
        self.loading_image = Image.open(resource_path("gif/11.gif"))
        self.loading_frames = [ImageTk.PhotoImage(frame.resize((100, 100), Image.Resampling.LANCZOS)) for frame in ImageSequence.Iterator(self.loading_image)]
        self.loading_frame_index = 0

        # Create a label to display the main GIF
        self.logo_label = tk.Label(root)
        self.logo_label.grid(row=1, column=0, columnspan=2, pady=10)
        self.update_animation()

        # Style
        style = ttk.Style()
        style.configure("TLabel", font=('Arial', 12), background='#f0f0f0')
        style.configure("TEntry", font=('Arial', 12), foreground='#333')
        style.configure("TButton", font=('Arial', 12), background='#0078D7', foreground='#000000')

        self.service_label = ttk.Label(root, text="Service:")
        self.service_label.grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.service_entry = ttk.Entry(root, width=30)
        self.service_entry.grid(row=2, column=1, padx=10, pady=5)

        self.username_label = ttk.Label(root, text="Username:")
        self.username_label.grid(row=3, column=0, padx=10, pady=5, sticky='e')
        self.username_entry = ttk.Entry(root, width=30)
        self.username_entry.grid(row=3, column=1, padx=10, pady=5)

        self.password_label = ttk.Label(root, text="Password:")
        self.password_label.grid(row=4, column=0, padx=10, pady=5, sticky='e')
        self.password_entry = ttk.Entry(root, show="*", width=30)
        self.password_entry.grid(row=4, column=1, padx=10, pady=5)

        self.save_button = ttk.Button(root, text="Save", command=self.save_password, width=15)
        self.save_button.grid(row=5, column=1, pady=10)

        self.retrieve_label = ttk.Label(root, text="Retrieve Password for Service/Username:")
        self.retrieve_label.grid(row=6, column=0, columnspan=2, pady=10)
        self.retrieve_entry = ttk.Entry(root, width=40)
        self.retrieve_entry.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

        self.retrieve_button = ttk.Button(root, text="Retrieve", command=self.retrieve_password, width=15)
        self.retrieve_button.grid(row=8, column=0, columnspan=2, pady=10)

    def update_animation(self):
        self.logo_label.config(image=self.frames[self.frame_index])
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.root.after(100, self.update_animation)  # Adjust the delay as needed

    def update_loading_animation(self, loading_label):
        loading_label.config(image=self.loading_frames[self.loading_frame_index])
        self.loading_frame_index = (self.loading_frame_index + 1) % len(self.loading_frames)
        loading_label.after(100, self.update_loading_animation, loading_label)  # Adjust the delay as needed

    def show_loading(self):
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("Loading")
        self.loading_window.geometry('200x200')  # Adjust size if needed

        # Loading GIF
        loading_label = tk.Label(self.loading_window)
        loading_label.pack(pady=10)

        # Searching text
        searching_label = tk.Label(self.loading_window, text="Searching...", font=('Arial', 12))
        searching_label.pack(pady=5)

        self.update_loading_animation(loading_label)

        # Close the loading window after 5 seconds
        self.loading_window.after(2000, lambda: self.retrieve_password_from_db())

    def retrieve_password_from_db(self):
        input_value = self.retrieve_entry.get()
        if input_value:
            results = get_password(input_value)
            self.loading_window.destroy()  # Close loading window when results are obtained
            if results:
                if len(results) == 1:
                    service, username, password = decrypt_result(results[0])
                    if service and username and password:
                        messagebox.showinfo("Retrieved Password", f"Service: {service}\nUsername: {username}\nPassword: {password}")
                else:
                    unique_services = set(result[0] for result in results)
                    if len(unique_services) > 1:
                        service = simpledialog.askstring("Service Required", f"Multiple entries found for {input_value}. Please specify the service: \n{', '.join(unique_services)}")
                        if service:
                            filtered_results = [result for result in results if result[0] == service]
                            if len(filtered_results) == 1:
                                service, username, password = decrypt_result(filtered_results[0])
                                if service and username and password:
                                    messagebox.showinfo("Retrieved Password", f"Service: {service}\nUsername: {username}\nPassword: {password}")
                            else:
                                username = simpledialog.askstring("Username Required", f"Multiple entries found for service '{service}'. Please specify the username.")
                                if username:
                                    for result in filtered_results:
                                        if result[1] == username:
                                            service, username, password = decrypt_result(result)
                                            if service and username and password:
                                                messagebox.showinfo("Retrieved Password", f"Service: {service}\nUsername: {username}\nPassword: {password}")
                                            break
                                else:
                                    messagebox.showerror("Error", "Username field is required.")
                    else:
                        service = unique_services.pop()
                        usernames = [result[1] for result in results]
                        username = simpledialog.askstring("Username Required", f"Multiple entries found for service '{service}'. Please specify the username: \n{', '.join(usernames)}")
                        if username:
                            for result in results:
                                if result[1] == username:
                                    service, username, password = decrypt_result(result)
                                    if service and username and password:
                                        messagebox.showinfo("Retrieved Password", f"Service: {service}\nUsername: {username}\nPassword: {password}")
                                    break
                        else:
                            messagebox.showerror("Error", "Username field is required.")
            else:
                messagebox.showerror("Error", "Service/Username not found or decryption failed.")
        else:
            self.loading_window.destroy()  # Close loading window if no input
            messagebox.showerror("Error", "Service/Username field is required.")

    def save_password(self):
        service = self.service_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        if service and username and password:
            save_or_update_password(service, username, password)
            self.service_entry.delete(0, tk.END)
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "All fields are required.")

    def retrieve_password(self):
        self.show_loading()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = PasswordManagerApp(root)
    root.mainloop()
