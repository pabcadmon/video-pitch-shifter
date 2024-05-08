import moviepy.editor as mpy
from tempfile import mktemp
import os
import torch
from numpy import swapaxes
from scipy.io import wavfile
from torch_pitch_shift import *

def pitch_shift_audio_torch(temp_audio_path, shift_amount):
    SAMPLE_RATE, sample = wavfile.read(temp_audio_path)
    dtype = sample.dtype
    sample = torch.tensor(
        [swapaxes(sample, 0, 1)],
        dtype=torch.float32,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    up = pitch_shift(sample, shift_amount, SAMPLE_RATE)
    wavfile.write(
        temp_audio_path,
        SAMPLE_RATE,
        swapaxes(up.cpu()[0].numpy(), 0, 1).astype(dtype),
    )

def process_video(video_path, output_path, shift_amount):
    try:
        video_clip = mpy.VideoFileClip(video_path)
        temp_audio_path = mktemp('.wav')
        video_clip.audio.write_audiofile(temp_audio_path)

        pitch_shift_audio_torch(temp_audio_path, shift_amount)

        new_audioclip = mpy.AudioFileClip(temp_audio_path)
        video_clip.audio = new_audioclip
        video_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=video_clip.fps)
        os.remove(temp_audio_path)

        return {"status": "success", "message": "Video saved successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
