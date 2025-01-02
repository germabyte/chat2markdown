import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os

def parse_conversation(data):
    """
    Parses the conversation from the JSON data and returns an ordered list of messages.
    Each message is a dictionary with keys: 'role', 'content', 'timestamp'.
    """
    try:
        if not isinstance(data, list) or not data:
            raise ValueError("JSON data is not a non-empty list.")

        conversation = data[0]
        mapping = conversation.get("mapping", {})

        if not mapping:
            raise ValueError("No 'mapping' found in JSON data.")

        # Find all root messages (parent is None)
        root_ids = [msg_id for msg_id, msg in mapping.items() if msg.get("parent") is None]

        if not root_ids:
            raise ValueError("No root message found (message with 'parent' as None).")

        ordered_messages = []

        def traverse(message_id):
            message = mapping.get(message_id)
            if not message:
                print(f"Warning: Message ID '{message_id}' not found in mapping.")
                return  # Skip if message_id not found

            msg_content = message.get("message")
            if msg_content:
                author = msg_content.get("author", {}).get("role", "unknown")
                content_parts = msg_content.get("content", {}).get("parts", [""])[0]
                create_time = msg_content.get("create_time", 0)

                # Only add messages that have non-empty content
                if content_parts.strip():
                    ordered_messages.append({
                        "role": author,
                        "content": content_parts.strip(),
                        "timestamp": create_time
                    })

            # Get children safely
            children_ids = message.get("children", [])
            if children_ids is None:
                print(f"Info: 'children' for message ID '{message_id}' is None. Treating as empty list.")
                children_ids = []
            elif isinstance(children_ids, str):
                print(f"Info: 'children' for message ID '{message_id}' is a single string. Converting to list.")
                children_ids = [children_ids]
            elif not isinstance(children_ids, list):
                print(f"Warning: 'children' for message ID '{message_id}' is not a list. Converting to empty list.")
                children_ids = []

            for child_id in children_ids:
                traverse(child_id)

        for root_id in root_ids:
            traverse(root_id)

        # Sort messages by timestamp to maintain chronological order
        ordered_messages.sort(key=lambda x: x["timestamp"])

        return ordered_messages

    except Exception as e:
        messagebox.showerror("Error Parsing JSON", f"An error occurred while parsing the JSON file:\n{str(e)}")
        return None

def convert_to_markdown(messages):
    """
    Converts the list of messages into Markdown formatted text with enhanced visual distinction.
    """
    md_content = ""
    i = 0
    while i < len(messages):
        msg = messages[i]
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            # User messages in blockquotes
            md_content += f"> **User:** {content}\n\n"
            # Check if the next message is from assistant
            if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                i += 1
                assistant_msg = messages[i]
                assistant_content = assistant_msg["content"]
                # Assistant messages in code blocks
                md_content += f"**ChatGPT:**\n\n```\n{assistant_content}\n```\n\n"
        else:
            # Other roles
            md_content += f"**{role.capitalize()}:** {content}\n\n"
        # Add a horizontal rule after each exchange
        md_content += "---\n\n"
        i += 1
    return md_content

def select_json_file():
    """
    Opens a file dialog for the user to select a JSON file.
    """
    file_path = filedialog.askopenfilename(
        title="Select JSON File",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if file_path:
        json_path_var.set(file_path)

def select_md_file():
    """
    Opens a file dialog for the user to specify the output Markdown file.
    """
    file_path = filedialog.asksaveasfilename(
        title="Save Markdown File",
        defaultextension=".md",
        filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")]
    )
    if file_path:
        md_path_var.set(file_path)

def convert():
    """
    Handles the conversion process from JSON to Markdown.
    """
    json_path = json_path_var.get()
    md_path = md_path_var.get()

    if not json_path:
        messagebox.showwarning("Input Required", "Please select a JSON file to convert.")
        return
    if not md_path:
        messagebox.showwarning("Output Required", "Please specify the output Markdown file.")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = parse_conversation(data)
        if messages is None:
            return  # Error already shown

        if not messages:
            messagebox.showwarning("No Messages Found", "No valid messages were found to convert.")
            return

        md_text = convert_to_markdown(messages)

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_text)

        messagebox.showinfo("Success", f"Conversion completed successfully!\n\nSaved to: {md_path}")

    except json.JSONDecodeError:
        messagebox.showerror("JSON Decode Error", "Failed to decode JSON. Please ensure the file is properly formatted.")
    except Exception as e:
        messagebox.showerror("Conversion Error", f"An error occurred during conversion:\n{str(e)}")

# Set up the GUI
root = tk.Tk()
root.title("JSON to Markdown Converter")
root.geometry("700x250")
root.resizable(False, False)

# Variables to hold file paths
json_path_var = tk.StringVar()
md_path_var = tk.StringVar()

# Layout
padding_options = {'padx': 10, 'pady': 10}

# JSON File Selection
json_frame = tk.Frame(root)
json_frame.pack(fill='x', **padding_options)

json_label = tk.Label(json_frame, text="Select JSON File:")
json_label.pack(side='left')

json_entry = tk.Entry(json_frame, textvariable=json_path_var, width=60)
json_entry.pack(side='left', padx=5)

json_button = tk.Button(json_frame, text="Browse", command=select_json_file)
json_button.pack(side='left')

# Markdown File Selection
md_frame = tk.Frame(root)
md_frame.pack(fill='x', **padding_options)

md_label = tk.Label(md_frame, text="Save Markdown As:")
md_label.pack(side='left')

md_entry = tk.Entry(md_frame, textvariable=md_path_var, width=60)
md_entry.pack(side='left', padx=5)

md_button = tk.Button(md_frame, text="Browse", command=select_md_file)
md_button.pack(side='left')

# Convert Button
convert_button = tk.Button(root, text="Convert", command=convert, bg="green", fg="white", font=("Arial", 12, "bold"))
convert_button.pack(pady=20)

# Run the GUI loop
root.mainloop()
