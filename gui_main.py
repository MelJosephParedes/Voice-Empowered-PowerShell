from tkinter import messagebox
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from transformers import T5ForConditionalGeneration, T5Tokenizer, WhisperProcessor, WhisperForConditionalGeneration
import threading
import sounddevice as sd
import numpy as np
import time
import sys
import struct
import pvporcupine
import pyaudio
#from faster_whisper import WhisperModel
from ps_commands import main
import string
from help_window import show_info_window
import torchaudio

import nltk
#nltk.download('stopwords')
from langdetect import detect

class VoiceInteractionApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("600x250")
        self.root.title("Voice-Empowered Powershell")
        self.root.configure(bg="#1c1c1c")  # Dark background

        # Initialize Porcupine for wake word detection
        self.porcupine = pvporcupine.create(
            access_key = "x0dnKX2dXspJTJtGosmAws+o/6BqTX0UoVQI0kDQ3JLmSOeesNTYkQ==",
            keyword_paths=["Hey-vox/Hey-vox_en.ppn"]  # Path to downloaded wake word model
        )
        
        
        self.whisper_processor = WhisperProcessor.from_pretrained("./whisper-small-finetuned1")
        self.whisper_model = WhisperForConditionalGeneration.from_pretrained(
            "./whisper-small-finetuned1", use_safetensors=True
        )

        self.t5_model = T5ForConditionalGeneration.from_pretrained("./t5-folder-creation-final-1")
        self.t5_tokenizer = T5Tokenizer.from_pretrained("./t5-folder-creation-final-1")

        # Set up audio stream for Porcupine
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

        # Load icons for mic and speaker using CTkImage
        self.mic_img = ctk.CTkImage(Image.open("assets/mic_icon.png"), size=(40, 40))
        self.mic_active_img = ctk.CTkImage(Image.open("assets/mic_active_icon.png"), size=(40, 40))
        self.speaker_img_default = ctk.CTkImage(Image.open("assets/speaker_icon.png"), size=(40, 40))
        self.speaker_img_active = ctk.CTkImage(Image.open("assets/speaker_active_icon.png"), size=(40, 40))
        self.speaker_img_low = ctk.CTkImage(Image.open("assets/speaker_low_icon.png"), size=(40, 40))
        self.speaker_img_medium = ctk.CTkImage(Image.open("assets/speaker_medium_icon.png"), size=(40, 40))
        self.speaker_img_high = ctk.CTkImage(Image.open("assets/speaker_high_icon.png"), size=(40, 40))

        # Create the UI layout
        self.create_widgets()

        # Initialize speaker icon to default
        self.speaker_label.configure(image=self.speaker_img_default)

        self.update_label()
        # Start Porcupine in a separate thread
        self.start_wake_word_detection_thread()

        self.custom_stop_words = set([
            'a', 'an', 'the', 'and', 'but', 'or', 'so', 'because', 'on', 'in', 'at', 'to', 'for', 'with', 'about', 'as', 'by', 'of', 'that', 'which', 'be', 'could', "would",
            'called', 'folder', 'folder?', 'folder.', 'can', 'you', 'file', 'directory?', 'directory.', 'directory', 'name', 'named',
            'full', 'their', 'filename'
        ])

        # Define a list of common file extensions that should be preserved
        self.file_extensions = set(['txt', 'py', 'jpg', 'png', 'csv', 'json', 'html', 'md', 'cpp', 'java', 'docx', 'pptx', 'xlsx'])
    
    def start_wake_word_detection_thread(self):
        threading.Thread(target=self.listen_for_wake_word, daemon=True).start()

    def listen_for_wake_word(self):
        """
        Continuously listen for the wake word using Porcupine.
        """
        print("Listening for wake word...")
        while True:
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected!")
                # Simulate mic button click by calling start_listening_thread()
                self.start_listening_thread()

    def create_widgets(self):
        # Create a frame for the UI components
        self.frame = ctk.CTkFrame(self.root, corner_radius=20, fg_color="#f7f7f7")  # Rounded corners
        self.frame.pack(padx=15, pady=15, fill="x")

        # Mic button
        self.mic_button = ctk.CTkButton(self.frame, image=self.mic_img, text="", fg_color="#ededed", hover_color="#d3d3d3", command=self.start_listening_thread)
        self.mic_button.grid(row=0, column=0, padx=10, pady=10)

        # Speaker label
        self.speaker_label = ctk.CTkLabel(self.frame, image=self.speaker_img_default, text="", fg_color="#ededed", font=("Arial", 14))
        self.speaker_label.grid(row=0, column=1, padx=10, pady=10)

        # Current Directory Label
        self.cur_directory_label = ctk.CTkLabel(self.frame, text="", fg_color="#2c2c2c", text_color="white", font=("Arial", 12), width=500, height=40)
        self.cur_directory_label.grid(row=1, column=0, columnspan=3, padx=10, pady=5)

        # Text Label to display recognized speech
        self.output_label = ctk.CTkLabel(self.frame, text="Say something...", fg_color="#2c2c2c", text_color="white", font=("Arial", 14), width=500, height=60)
        self.output_label.grid(row=2, column=0, columnspan=3, padx=10)

        # Help Button
        #self.help_button = ctk.CTkButton(self.frame, text="Help", command=lambda: show_info_window(self.root))
        #self.help_button.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        #self.input_label = ctk.CTkLabel(self.frame, text="Input command:", font=("Arial", 14), width=100, height=50)
        #self.input_label.grid(row=3, column=0, columnspan=3, pady=10)

        #self.input_box = ctk.CTkEntry(self.frame, width=100, height=50)
        #self.input_box.grid(row=3, column=1, columnspan=3, pady=10)


    def read_found_paths(self):
        try:
            with open('paths.txt', 'r') as f:
                lines = f.readlines()
            
            paths_dict = {index + 1: line.strip() for index, line in enumerate(lines)}

            return paths_dict
        except FileNotFoundError:
            print("The file 'found_paths.txt' does not exist")
            return{}

    def display_window_path(self):
        if hasattr(self, 'display_window_paths') and self.display_window_paths.winfo_exists():
            # Bring the existing window to the front
            self.display_window_paths.lift()
            return

        self.display_window_paths = tk.Toplevel(self.root)  # Use a Toplevel window
        self.display_window_paths.title("Found Paths")
        self.display_window_paths.geometry("600x250")
        self.display_window_paths.configure(bg="#f2f0eb")
        self.display_window_paths.attributes('-topmost', True)
        #self.display_window_paths.grab_set()
        #self.display_window_paths.focus_set()

        self.paths_textbox = ctk.CTkTextbox(self.display_window_paths, wrap='word')
        self.paths_textbox.pack(expand=True, fill='both')

        paths = self.read_found_paths()
        if not paths:
            self.paths_textbox.insert('end', "No paths found in 'paths.txt'.\n")
        else:
            for index, path in paths.items():
                self.paths_textbox.insert('end', f"{index}: {path}\n")

    def update_label(self):
        with open('current_path.txt', 'r') as f:
            base_path = f.read()
        self.cur_directory_label.configure(text="Current Directory: " + base_path)
        
        # Call this method again after a delay (e.g., every 1000ms)
        self.root.after(1000, self.update_label)

    def minimize(self):
        self.root.iconify()  # Minimize the window

    def start_listening_thread(self):
        # Start the listening function in a separate thread to avoid blocking the UI
        threading.Thread(target=self.start_listening, daemon=True).start()

    def start_listening(self):
        try:
            # Change mic icon to active state
            self.mic_button.configure(image=self.mic_active_img)
            self.speaker_label.configure(image=self.speaker_img_active)

            # Initialize the audio analyzer
            self.audio_analyzer = AudioAnalyzer(self.update_speaker_icon)
            self.audio_analyzer.start()
            self.root.after(0, lambda: self.output_label.configure(text='Recording Audio...'))
            # Record audio
            audio_data = self.record_audio()

            if audio_data is not None:
                # Transcribe the audio
                self.root.after(0, lambda: self.output_label.configure(text='Transcribing Audio...'))

                transcribe_audio_start = time.time()
                transcription = self.transcribe_audio(audio_data)
                transcribe_audio_end = time.time()
                transcribe_time_result = transcribe_audio_end - transcribe_audio_start
                print(f"Whisper Transcribing Runtime: {transcribe_time_result:.2f} seconds")
                
                if transcription:

                    print(f"Whisper Transcription output: {transcription}")
                    self.root.after(0, lambda: self.output_label.configure(text=f'Transcription Output: {transcription}'))

                    t5_process_start = time.time()
                    t5_process_output =  self.process_with_t5(transcription)
                    t5_process_end = time.time()

                    t5_time_result = t5_process_end - t5_process_start
                    print(f"T5 Processing Runtime: {t5_time_result:.2f} seconds")
                    print(f"T5 Output: {t5_process_output}")

                    filtered_transcription = self.filter_stop_words_and_preserve_extensions(t5_process_output)

                    if 'delete' in filtered_transcription:
                        answer = messagebox.askyesno("Delete Command Confirmation", f"Do you want to proceed with the deletion command :{transcription}? The item that will be deleted will not go to Recycle bin.")
                        if not answer: # If user clicks "No", cancel the operation
                            self.root.after(0, lambda: self.output_label.configure(text=f'Operation Canceled'))
                            return

                    print(f"filtered t5 transcription: {filtered_transcription}")
                    self.root.after(0, lambda: self.output_label.configure(text=f'T5 output: {filtered_transcription}. Processing...'))
                    
                    main_start = time.time()
                    result = main(filtered_transcription)
                    main_end = time.time()
                    
                    main_exec_time = main_end - main_start # Execution time of the PowerShell Algorithm

                    if 'multiple' in transcription:
                        self.root.after(0, self.display_window_path)

                    print(f"PowerShell execution time: {main_exec_time:.2f} seconds")

                    total_runtime = transcribe_time_result + t5_time_result + main_exec_time
                    print(f"Total Runtime From Whisper to PowerShell Algorithm: {total_runtime:.2f} seconds")
                    
                    print(f"Processed result: {result}")
                    # Update the output label with the result
                    self.root.after(0, lambda: self.output_label.configure(text=result))

                else:
                    # Handle case where transcription fails
                    print("No transcription available.")
                    self.root.after(0, lambda: self.output_label.configure(text="No transcription available."))
            else:
                # Handle case where audio recording fails
                print("Failed to capture audio.")
                self.root.after(0, lambda: self.output_label.configure(text="Failed to capture audio."))

        except Exception as e:
            # Handle unexpected exceptions
            print(f"Error in start_listening: {e}")
            self.root.after(0, lambda: self.output_label.configure(text="An error occurred."))

        finally:
            # Stop the audio analyzer and reset icons
            self.audio_analyzer.stop()
            self.mic_button.configure(image=self.mic_img)
            self.root.after(200, lambda: self.speaker_label.configure(image=self.speaker_img_default))


    def filter_stop_words_and_preserve_extensions(self, t5_process_output):
        # Split transcription into words
        words = t5_process_output.split()

        # Filtered words will be stored here
        filtered_words = []

        # Iterate through each word in the input
        for i, word in enumerate(words):
            # Clean the word to remove punctuation (to deal with cases like pptx?)
            cleaned_word = word.strip(string.punctuation)

            # Check if the word is a file extension (has a dot or matches known extensions)
            if '.' in word or cleaned_word.lower() in self.file_extensions:
                # Combine previous word with extension if necessary (e.g., "that pptx" → "presentation.pptx")
                if cleaned_word.lower() in self.file_extensions and i > 0:
                    # Preserve punctuation, if any, by appending it back after combining
                    filtered_words[-1] += f".{cleaned_word}{word[len(cleaned_word):]}"  
                else:
                    filtered_words.append(word)
            elif word.lower() not in self.custom_stop_words:
                # If the word is not a stop word, keep it
                filtered_words.append(word)

        # Join the filtered words back into a sentence
        return ' '.join(filtered_words)

    def record_audio(self, duration=6):
        """Record audio from the microphone."""
        try:
            print("Recording audio...")
            audio_data = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype="float32")
            sd.wait()
            return audio_data.flatten()
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None, None
    
    def transcribe_audio(self, audio_data):
        """Transcribe audio Hugging Face Whisper Model."""
        print("Transcribing audio...")
        try:
            # Preprocess: convert raw audio to input features
            inputs = self.whisper_processor(audio_data, sampling_rate=16000, return_tensors="pt")

            # Move inputs to same device as model
            input_features = inputs.input_features.to(self.whisper_model.device)

            attention_mask = inputs.get("attention_mask", None)
            if attention_mask is not None:
                attention_mask = attention_mask.to(self.whisper_model.device)

            # Force decoder to use English transcription tokens
            forced_decoder_ids = self.whisper_processor.get_decoder_prompt_ids(language="en", task="transcribe")

            # Generate
            predicted_ids = self.whisper_model.generate(
                input_features,
                attention_mask=attention_mask,
                forced_decoder_ids=forced_decoder_ids
            )

            # Decode to text
            transcription = self.whisper_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

            return transcription

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None
        
    def process_with_t5(self, text):
        """Process the transcribed text using T5."""
        print("Processing with T5...")
        try:
            input_ids = self.t5_tokenizer.encode(text, return_tensors="pt")
            outputs = self.t5_model.generate(input_ids, max_length=100, num_beams=4, early_stopping=True)
            return self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            print(f"Error processing with T5: {e}")
            return "Processing error."
    
    def update_speaker_icon(self, loudness):
        # Determine which image to use based on loudness level
        if loudness < 0.001:
            img = self.speaker_img_active
        elif loudness < 0.01:  # Threshold adjusted for demonstration
            img = self.speaker_img_low
        elif loudness < 0.1:
            img = self.speaker_img_medium
        else:
            img = self.speaker_img_high
        
        self.speaker_label.configure(image=img)

    def on_closing(self):
        self.root.destroy()

class AudioAnalyzer:
    def __init__(self, update_callback):
        self.update_callback = update_callback
        self.is_listening = False

        self.sample_rate = 16000
        self.chunk = 1024
        self.audio = None

    def start(self):
        self.is_listening = True
        threading.Thread(target=self._listen, daemon=True).start()

    def stop(self):
        self.is_listening = False

    def _listen(self):
        with sd.InputStream(samplerate=self.sample_rate, channels=1, callback=self.audio_callback):
            while self.is_listening:
                time.sleep(0.1)

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        loudness = np.sqrt(np.mean(indata**2))  # Adjust this threshold as needed
        self.update_callback(loudness)

# Main program execution
if __name__ == "__main__":
    global app
    root = ctk.CTk()  # Use CTk for custom tkinter styling
    app = VoiceInteractionApp(root)  # Create an instance of the app
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    #commands_test.set_gui_instance_app(app)
    root.mainloop()  # Start the application
