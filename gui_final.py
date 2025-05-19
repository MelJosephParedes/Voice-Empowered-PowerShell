import tkinter as tk
import random
import numpy as np
import sounddevice as sd
from transformers import T5ForConditionalGeneration, T5Tokenizer, WhisperProcessor, WhisperForConditionalGeneration
import threading
import sounddevice as sd
import numpy as np
import time
import sys
import struct
import pvporcupine
import pyaudio
from ps_commands import main
import string
from tkinter import messagebox
import customtkinter as ctk
import io
import sys

logs_box = None

def log_output(message, font_size=12):
    #timestamp = datetime.now().strftime("[%H:%M:%S]")
    #full_message = f"{timestamp} {message.strip()}\n"
    full_message = f"{message.strip()}\n"
    try:
        if hasattr(sys, "logs_box") and sys.logs_box:
            sys.logs_box.insert("end", full_message)
            sys.logs_box.yview("end")
            sys.logs_box.config(font=("Helvetica", font_size))
    except Exception as e:
        pass  # You can optionally print to default stderr if logging fails

class OutputRedirector(io.StringIO):
    def __init__(self, log_function):
        super().__init__()
        self.log_function = log_function

    def write(self, message):
        if message.strip():
            self.log_function(message)


def setup_logging_widget(text_widget):
    sys.logs_box = text_widget
    sys.stdout = OutputRedirector(log_output)
    sys.stderr = OutputRedirector(log_output)

class ImprovedUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Voice Assistant UI")
        self.configure(bg="#2D2D2D")
        self.geometry("500x300")
        self.resizable(False, False)
        self.animation_running = False
        self.stream = None

        # Box 1: Main frame
        self.main_frame = tk.Frame(self, bg="#2D2D2D", padx=20, pady=20)
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.pack_propagate(False)

        # Box 2: Container
        self.container = tk.Frame(self.main_frame, bg="#3A3A3A", padx=10, pady=10, width=460, height=260)
        self.container.pack(side="left")
        self.container.pack_propagate(False)

        # Box 3: Main content
        self.main_content = tk.Frame(self.container, bg="#3A3A3A", width=460)
        self.main_content.pack(side="left", fill="y")
        self.main_content.pack_propagate(False)

        # Box 5: Content area
        self.content_area = tk.Frame(self.main_content, bg="#3A3A3A")
        self.content_area.pack(fill="both", expand=True)

        # Box 6: Left frame
        self.left_frame = tk.Label(self.content_area, bg="#3A3A3A", width=450)
        self.left_frame.pack(side="left", fill="both", padx=(0, 10))
        self.left_frame.pack_propagate(False)

        # Box 4: Header
        self.header_frame = tk.Frame(self.left_frame, bg="#444444", height=50)
        self.header_frame.pack(fill="x", pady=(0, 10))
        self.header_frame.pack_propagate(False)

        ai_icon_frame = tk.Frame(self.header_frame, bg="#252525")
        ai_icon_frame.place(x=10, y=7)

        try:
            self.ai_icon_image = tk.PhotoImage(file="ui/logo.png")
            self.ai_icon_image = self.ai_icon_image.subsample(1, 1)
            self.ai_icon_image_ref = self.ai_icon_image
            ai_icon_label = tk.Label(ai_icon_frame, image=self.ai_icon_image)
            ai_icon_label.place(relx=0.5, rely=0.5, anchor="center")
        except tk.TclError:
            print("Error: logo.png not found. Please check the file path.")

        try:
            self.logo_top_left = tk.PhotoImage(file="ui/logo.png")
            self.logo_top_left = self.logo_top_left.subsample(30, 30)
            self.logo_ref = self.logo_top_left
            logo_label = tk.Label(self.header_frame, image=self.logo_top_left, bg="#444444")
            logo_label.place(x=10, y=7, anchor="nw")
        except tk.TclError:
            print("Error: logo.png not found. Please check the file path.")

        try:
            self.info_icon = tk.PhotoImage(file="ui/info.png")
            self.help_icon = tk.PhotoImage(file="ui/help.png")
        except tk.TclError:
            print("Error: info.png/help.png not found.")

        circle_btn1 = tk.Button(self.header_frame, image=self.info_icon, bg="#444444",
                                relief="flat", borderwidth=0, command=self.toggle_logs)
        circle_btn1.place(relx=0.83, y=7, width=35, height=35)

        circle_btn2 = tk.Button(self.header_frame, image=self.help_icon, bg="#444444",
                                relief="flat", borderwidth=0, command=self.show_help_popup)
        circle_btn2.place(relx=0.9, y=7, width=35, height=35)

        # Box 7: Icon row
        icon_row = tk.Frame(self.left_frame, bg="#3A3A3A", height=60)
        icon_row.pack(fill="x", pady=(0, 10))

        mic_frame = tk.Frame(icon_row, bg="#8B5D8A", width=50, height=50)
        mic_frame.place(x=0, y=0)

        try:
            self.mic_icon = tk.PhotoImage(file="ui/mic.png")
            self.mic_icon_ref = self.mic_icon
            mic_button = tk.Button(mic_frame, image=self.mic_icon, bg="#8B5D8A", relief="flat", command=self.start_listening_thread)
            mic_button.place(relx=0.5, rely=0.5, anchor="center")
        except tk.TclError:
            print("Error: mic.png not found. Please check the file path.")

        # Visualization canvas
        self.vis_canvas = tk.Canvas(icon_row, bg="#353535", width=50, height=50, highlightthickness=0)
        self.vis_canvas.place(x=60, y=0)

        self.bars = []
        for i in range(4):
            bar = self.vis_canvas.create_rectangle(10 + (i * 10), 40, 16 + (i * 10), 50, fill="#6A5ACD", outline="")
            self.bars.append(bar)

        # Text panel
        self.curr_directory = tk.Label(icon_row, bg="#555555", fg="white", anchor="w", font=("Segoe UI", 10))
        self.curr_directory.place(x=120, y=0, width=330, height=50)

        # Bottom panel (as Label instead of Frame)
        self.output_result = tk.Label(self.left_frame, bg="#444444", fg="white", anchor="w", font=("Segoe UI", 10),
                        text="Status: Ready", width=330, height=4)
        self.output_result.pack(anchor="sw", padx=(0, 0), pady=(5, 0))

        # Right panel
        self.logs_box = tk.Text(self.main_frame, bg="#444444",fg="white", width=200)
        setup_logging_widget(self.logs_box)
        self.logs_visible = False

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

        self.custom_stop_words = set([
            'a', 'an', 'the', 'and', 'but', 'or', 'so', 'because', 'on', 'in', 'at', 'to', 'for', 'with', 'about', 'as', 'by', 'of', 'that', 'which', 'be', 'could', "would",
            'called', 'folder', 'folder?', 'folder.', 'can', 'you', 'file', 'directory?', 'directory.', 'directory', 'name', 'named',
            'full', 'their', 'filename'
        ])

        self.start_wake_word_detection_thread()

        # Define a list of common file extensions that should be preserved
        self.file_extensions = set(['txt', 'py', 'jpg', 'png', 'csv', 'json', 'html', 'md', 'cpp', 'java', 'docx', 'pptx', 'xlsx'])

        self.update_label()
    
    def toggle_logs(self):
        if self.logs_visible:
            self.logs_box.pack_forget()
            self.logs_visible = False
            self.geometry("500x300")
        else:
            self.logs_box.pack(side="right", fill="y")
            self.logs_visible = True
            self.geometry("700x300")

    def toggle_animation(self):
        """Start or stop listening for sound"""

        if self.animation_running:
            self.listen_for_sound()
        else:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.reset_bars()

    def listen_for_sound(self):
        """Begin live mic sound detection"""
        
        def audio_callback(indata, frames, time, status):
            volume_norm = np.linalg.norm(indata) * 10
            if volume_norm > 1:  # You can adjust this threshold
                self.update_bars(volume_norm)
            else:
                self.reset_bars()

        self.stream = sd.InputStream(callback=audio_callback)
        self.stream.start()

    def update_bars(self, volume):
        """Move bars based on sound volume"""
        for i, bar in enumerate(self.bars):
            height = min(35, max(5, int(volume) + random.randint(-5, 5)))
            self.vis_canvas.coords(bar, 10 + (i * 10), 50 - height, 16 + (i * 10), 50)

    def reset_bars(self):
        """Reset bars to bottom position"""
        for i, bar in enumerate(self.bars):
            self.vis_canvas.coords(bar, 10 + (i * 10), 45, 16 + (i * 10), 50)

    def show_help_popup(self):
        help_window = tk.Toplevel(self)
        help_window.title("How to Use")
        help_window.geometry("400x250")
        help_window.configure(bg="#2D2D2D")
        help_window.resizable(False, False)

        title = tk.Label(help_window, text="🔊 How to Use the Voice Assistant",
                         font=("Segoe UI", 12, "bold"), fg="white", bg="#2D2D2D")
        title.pack(pady=(10, 5))

        instructions = (
            "1. Click the microphone icon to start listening.\n"
            "2. Speak clearly into your microphone.\n"
            "3. The bars next to the mic will animate during capture.\n"
            "4. Results or feedback will appear below or in the side panel.\n"
            "5. Use the 'i' button for additional information.\n"
        )

        label = tk.Label(help_window, text=instructions, justify="left", fg="white", bg="#2D2D2D", font=("Segoe UI", 10))
        label.pack(padx=20, pady=10)

        close_button = tk.Button(help_window, text="Close", command=help_window.destroy, bg="#6A5ACD", fg="white", relief="flat")
        close_button.pack(pady=(0, 15))

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

        self.display_window_paths = tk.Toplevel(app)  # Use a Toplevel window
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
        self.curr_directory.configure(text="Curr Directory: " + base_path)
        
        # Call this method again after a delay (e.g., every 1000ms)
        self.after(1000, self.update_label)

    def minimize(self):
        app.iconify()  # Minimize the window

    def start_listening_thread(self):
        # Start the listening function in a separate thread to avoid blocking the UI
        self.animation_running = True
        threading.Thread(target=self.start_listening, daemon=True).start()

    def start_listening(self):
        try:
            audio_data = self.record_audio()
            
            if audio_data is not None:
                # Transcribe the audio
                app.after(0, lambda: self.output_result.configure(text='Transcribing Audio...'))

                transcribe_audio_start = time.time()
                transcription = self.transcribe_audio(audio_data)
                transcribe_audio_end = time.time()
                transcribe_time_result = transcribe_audio_end - transcribe_audio_start
                print(f"Whisper Transcribing Runtime: {transcribe_time_result:.2f} seconds")
                
                if transcription:

                    print(f"Whisper Transcription output: \n{transcription}")
                    app.after(0, lambda: self.output_result.configure(text=f'Transcription Output: {transcription}'))

                    t5_process_start = time.time()
                    t5_process_output =  self.process_with_t5(transcription)
                    t5_process_end = time.time()

                    t5_time_result = t5_process_end - t5_process_start
                    print(f"T5 Processing Runtime: \n{t5_time_result:.2f} seconds")
                    print(f"T5 Output: {t5_process_output}")

                    filtered_transcription = self.filter_stop_words_and_preserve_extensions(t5_process_output)

                    if 'delete' in filtered_transcription:
                        answer = messagebox.askyesno("Delete Command Confirmation", f"Do you want to proceed with the deletion command :{transcription}? The item that will be deleted will not go to Recycle bin.")
                        if not answer: # If user clicks "No", cancel the operation
                            app.after(0, lambda: self.output_result.configure(text=f'Operation Canceled'))
                            return

                    print(f"Filtered t5 transcription: \n{filtered_transcription}")
                    app.after(0, lambda: self.output_result.configure(text=f'T5 output: \n{filtered_transcription}. \nProcessing...'))
                    
                    main_start = time.time()
                    result = main(filtered_transcription)
                    main_end = time.time()
                    
                    main_exec_time = main_end - main_start # Execution time of the PowerShell Algorithm

                    if 'multiple' in transcription:
                        app.after(0, self.display_window_path)

                    print(f"PowerShell execution time:\n {main_exec_time:.2f} seconds")

                    total_runtime = transcribe_time_result + t5_time_result + main_exec_time
                    print(f"Total Runtime From Whisper to PowerShell Algorithm:\n {total_runtime:.2f} seconds")
                    
                    print(f"Processed result: \n{result}")
                    # Update the output label with the result
                    app.after(0, lambda: self.output_result.configure(text=result))

                else:
                    # Handle case where transcription fails
                    print("No transcription available.")
                    app.after(0, lambda: self.output_result.configure(text="No transcription available."))
            else:
                # Handle case where audio recording fails
                print("Failed to capture audio.")
                app.after(0, lambda: self.output_result.configure(text="Failed to capture audio."))

        except Exception as e:
            # Handle unexpected exceptions
            print(f"Error in start_listening: {e}")
            app.after(0, lambda: self.output_result.configure(text="An error occurred."))

        finally:
            self.animation_running = False
            self.toggle_animation()
            print('The Process ended. Say "Hey Vox" again to use the program')


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
            self.animation_running = True
            self.toggle_animation()
            print("Recording audio...")
            app.after(0, lambda: self.output_result.configure(text="Recording Audio. Please speak your command."))
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


if __name__ == "__main__":
    app = ImprovedUI()
    app.mainloop()