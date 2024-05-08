import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import moviepy.editor as mpy
from tempfile import mktemp
import os
from threading import Thread
import torch
from numpy import swapaxes
from scipy.io import wavfile
from torch_pitch_shift import *

global global_video_clip

# Track progress globally
progress_data = {"audio": 0, "video": 0}
# Track progress bar animation state
video_progress_animation = True
video_progress_value = 0

# Function to incrementally fill the progress bar
def update_video_progress_bar():
    global video_progress_value, video_progress_animation
    if video_progress_animation:
        video_progress_value += 4  # Adjust this value for different fill rates
        if video_progress_value > 100:
            video_progress_value = 0
        update_progress("video", video_progress_value)
        root.after(100, update_video_progress_bar)  # Updates every 0.1 seconds

def update_progress(name, value):
    progress_data[name] = value
    audio_progress["value"] = progress_data["audio"]
    video_progress["value"] = progress_data["video"]

def video_progress_callback(current_frame, total_frames):
    progress_percentage = (current_frame / total_frames) * 100
    update_progress("video", progress_percentage)

def load_video():
    global global_video_clip
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
    if file_path:
        global_video_clip = mpy.VideoFileClip(file_path)
        status_label.config(text=f"Loaded video: {file_path}")
    else:
        status_label.config(text="Loading cancelled.")

def pitch_shift_audio_torch(temp_audio_path, shift_amount):
    # Set initial progress for audio processing
    update_progress("audio", 0)

    SAMPLE_RATE, sample = wavfile.read(temp_audio_path)

    # Convert to tensor of shape (batch_size, channels, samples)
    dtype = sample.dtype
    sample = torch.tensor(
        [swapaxes(sample, 0, 1)],  # (samples, channels) --> (channels, samples)
        dtype=torch.float32,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )

    # Apply pitch shifting
    update_progress("audio", 50)
    up = pitch_shift(sample, shift_amount, SAMPLE_RATE)
    assert up.shape == sample.shape

    wavfile.write(
        temp_audio_path,
        SAMPLE_RATE,
        swapaxes(up.cpu()[0].numpy(), 0, 1).astype(dtype),
    )

    # Complete the progress
    update_progress("audio", 100)

def process_video(output_path, shift_amount):
    global video_progress_animation
    try:
        temp_audio_path = mktemp('.wav')
        global_video_clip.audio.write_audiofile(temp_audio_path)

        # Process audio separately with its progress bar
        pitch_shift_audio_torch(temp_audio_path, shift_amount)

        new_audioclip = mpy.AudioFileClip(temp_audio_path)
        global_video_clip.audio = new_audioclip
        video_progress_animation = True
        update_video_progress_bar()
        # Write the video file and update the progress bar
        global_video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', logger="bar", fps=global_video_clip.fps)

        video_progress_animation = False
        video_progress["value"] = 100
        messagebox.showinfo("Success", "Video saved successfully!")
        os.remove(temp_audio_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def save_video():
    global global_video_clip
    if global_video_clip:
        try:
            shift_amount = float(shift_entry.get())
            output_path = filedialog.asksaveasfilename(defaultextension='.mp4', filetypes=[("MP4 files", "*.mp4")])
            if output_path:
                Thread(target=process_video, args=(output_path, shift_amount), daemon=True).start()
            else:
                messagebox.showinfo("Cancelled", "Saving cancelled.")
        except ValueError:
            messagebox.showerror("Error", "Invalid input for pitch shift.")
    else:
        messagebox.showerror("Error", "No video loaded. Please load a video first.")

# Create GUI
root = tk.Tk()
root.title("Video Pitch Shifter")
root.geometry("500x350")

load_btn = tk.Button(root, text="Load Video", command=load_video)
load_btn.pack(pady=10)

shift_label = tk.Label(root, text="Shift Semitones:")
shift_label.pack(pady=5)

shift_entry = tk.Spinbox(root, from_=-12, to=12, increment=1, width=15)
shift_entry.pack(pady=5)
shift_entry.delete(0, "end")  # Clear any default text
shift_entry.insert(0, "0")  # Default value of "0" (no pitch shift)

save_btn = tk.Button(root, text="Save Video", command=save_video)
save_btn.pack(pady=10)

status_label = tk.Label(root, text="No video loaded.")
status_label.pack(pady=5)

# Add frame for progress bars
progress_frame = tk.Frame(root)
progress_frame.pack(pady=10)

# Add progress bars for audio and video processing
audio_label = tk.Label(progress_frame, text="Audio Processing:")
audio_label.pack()
audio_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
audio_progress.pack(pady=5)

video_label = tk.Label(progress_frame, text="Video Processing:")
video_label.pack()
video_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
video_progress.pack(pady=5)

root.mainloop()
