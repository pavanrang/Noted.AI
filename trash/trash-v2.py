import sys
import wave
import pyaudio
import threading
import pyttsx3
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QComboBox, QLabel, QLineEdit, QSpacerItem, QSizePolicy, QGroupBox, QHBoxLayout
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal
from groq import Groq
# import google.generativeai as genai
import os
import multiprocessing

# Initialize Groq client
# client = Groq()
client = Groq(
    api_key="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",
)
# Configure Gemini API
# genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def tts_process(text, stop_event):
    """
    Function to run the TTS engine in a separate process.

    Args:
        text: The text to be spoken.
        stop_event: A multiprocessing.Event object to signal when to stop playback.
    """
    tts_engine = pyttsx3.init() # Initialize tts_engine inside the function
    tts_engine.say(text)
    try:
        tts_engine.runAndWait()
    except RuntimeError as e:  # Catch RuntimeError if the process is terminated prematurely
        if "Process was terminated" in str(e):
            logging.info("TTS process terminated.")
        else:
            logging.error(f"Error during TTS playback: {e}")
    finally:
        stop_event.set()  # Signal that the process has finished


class AudioRecorder(QMainWindow):
    """
    Main window for audio recording, transcription, and LLM response.
    """

    def __init__(self):
        """
        Initialize the main window.
        """
        super().__init__()
        self.title = 'Meeting2LLM'  # Window title
        self.left = 100  # Window position
        self.top = 100
        self.width = 400  # Window size
        self.height = 600
        self.initUI()  # Initialize the user interface
        self.tts_process = None  # Process for TTS playback
        self.is_playing = False  # Flag to indicate if audio is being played
        self.response = None  # Initialize response attribute
        self.stop_event = None  # Event to signal TTS process to stop

    def initUI(self):
        """
        Initialize the user interface.
        """
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowIcon(QIcon('M2L_icon.png'))

        # Main layout and widget
        main_layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)  # Set the main widget

        # --- Styling ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0; /* Light gray background */
            }
            QPushButton {
                background-color: #007bff; /* Blue */
                border: none;
                color: white;
                padding: 12px 24px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 8px 4px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3; /* Darker blue on hover */
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ced4da; /* Light gray border */
                padding: 12px;
                font-size: 14px;
                font-family: Arial, Helvetica, sans-serif;
                border-radius: 5px;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #ced4da;
                padding: 8px;
                font-size: 14px;
                border-radius: 5px;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #ced4da;
                padding: 8px;
                font-size: 14px;
                border-radius: 5px;
            }
            QLabel {
                font-size: 14px;
                margin-bottom: 5px;
            }
            QGroupBox {
                border: 1px solid #ced4da;
                border-radius: 5px;
                margin-top: 10px; 
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """)

        # --- Settings Group Box ---
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()

        # System Prompt Input
        self.system_prompt_label = QLabel("System Prompt:")
        settings_layout.addWidget(self.system_prompt_label)

        self.system_prompt_input = QLineEdit(self)
        default_prompt = "You are an experienced professional. Please respond to the following interview question in a first-person, detailed, and professional manner."
        self.system_prompt_input.setText(default_prompt)
        settings_layout.addWidget(self.system_prompt_input)

        # Model Selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        model_layout.addWidget(model_label)
        self.model_selector = QComboBox(self)
        self.model_selector.addItem("llama3-70b-8192")
        self.model_selector.addItem("llama-3.1-70b-versatile")
        self.model_selector.addItem("mixtral-8x7b-32768")
        self.model_selector.addItem("gemma2-9b-it")
        # self.model_selector.addItem("gemini-1.5-flash")
        # self.model_selector.addItem("gemini-1.5-pro")
        model_layout.addWidget(self.model_selector)
        settings_layout.addLayout(model_layout)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # --- Controls Group Box ---
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout()

        self.record_button = QPushButton('Start Recording', self)
        self.record_button.clicked.connect(self.on_click_record)
        controls_layout.addWidget(self.record_button)

        self.stop_button = QPushButton('Stop Recording', self)
        self.stop_button.clicked.connect(self.on_click_stop)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)

        self.play_button = QPushButton('Play Response Audio', self)
        self.play_button.clicked.connect(self.play_audio_response)
        self.play_button.setEnabled(False)
        controls_layout.addWidget(self.play_button)

        self.stop_play_button = QPushButton('Stop Audio', self)
        self.stop_play_button.clicked.connect(self.stop_audio_response)
        self.stop_play_button.setEnabled(False)
        controls_layout.addWidget(self.stop_play_button)

        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group)

        # Add spacer for better layout
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)

        # --- Output Group Box ---
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()

        # Text edit for transcription and LLM response
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("Transcription and LLM responses will appear here.")

        # Set font size for QTextEdit
        font = QFont()
        font.setPointSize(12)
        self.text_edit.setFont(font)

        output_layout.addWidget(self.text_edit)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        self.show()  # Show the window

    @pyqtSlot()
    def on_click_record(self):
        """
        Handle the 'Start Recording' button click.
        """
        self.text_edit.clear()  # Clear the text edit area
        self.record_button.setEnabled(False)  # Disable record button
        self.stop_button.setEnabled(True)  # Enable stop button
        self.play_button.setEnabled(False)  # Disable play button
        self.stop_play_button.setEnabled(False)  # Disable stop playback button
        self.record_thread = threading.Thread(target=self.record_audio,
                                               args=("meeting_audio.wav",))  # Create recording thread
        self.record_thread.start()  # Start recording thread

    @pyqtSlot()
    def on_click_stop(self):
        """
        Handle the 'Stop Recording' button click.
        """
        self.stop_recording = True  # Set stop recording flag
        self.record_button.setEnabled(True)  # Enable record button
        self.stop_button.setEnabled(False)  # Disable stop button
        self.record_thread.join()  # Wait for recording thread to finish
        self.transcribe_and_respond("meeting_audio.wav")  # Transcribe and generate response

    def record_audio(self, filename):
        """
        Record audio from the microphone and save it to a WAV file.

        Args:
            filename: The name of the WAV file to save the recording to.
        """
        self.stop_recording = False  # Clear stop recording flag
        CHUNK = 1024  # Audio chunk size
        FORMAT = pyaudio.paInt16  # Audio format
        CHANNELS = 2  # Number of audio channels
        RATE = 44100  # Audio sample rate

        p = pyaudio.PyAudio()  # Initialize PyAudio
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                         frames_per_buffer=CHUNK)  # Open audio stream
        frames = []  # List to store recorded audio frames

        try:
            while not self.stop_recording:
                data = stream.read(CHUNK)  # Read audio data from stream
                frames.append(data)  # Append data to frames list
        except Exception as e:
            print(f"Error during recording: {e}")  # Print error message
        finally:
            stream.stop_stream()  # Stop audio stream
            stream.close()  # Close audio stream
            p.terminate()  # Terminate PyAudio

            # Check if any data was recorded
            if frames:
                wf = wave.open(filename, 'wb')  # Open WAV file for writing
                wf.setnchannels(CHANNELS)  # Set number of channels
                wf.setsampwidth(p.get_sample_size(FORMAT))  # Set sample width
                wf.setframerate(RATE)  # Set frame rate
                wf.writeframes(b''.join(frames))  # Write audio frames to file
                wf.close()  # Close WAV file
            else:
                print("No audio data recorded, file not created.")  # Print message if no data was recorded

    def transcribe_and_respond(self, filename):
        """
        Transcribe the audio file and generate an LLM response.

        Args:
            filename: The name of the audio file to transcribe.
        """
        # Create a separate thread for transcription and response generation
        self.processing_thread = threading.Thread(target=self._transcribe_and_respond, args=(filename,))
        self.processing_thread.start()

    def _transcribe_and_respond(self, filename):
        """
        Transcribe the audio file and generate an LLM response in a separate thread.

        Args:
            filename: The name of the audio file to transcribe.
        """
        try:
            transcription = self.transcribe_audio(filename)  # Transcribe the audio
            logging.info("Transcription completed.")  # Log transcription completion
            self.text_edit.append(
                "Transcription:\n" + transcription + "\n\n")  # Append transcription to text edit area

            self.response = self.get_llm_response(
                transcription)  # Generate LLM response and store it
            logging.info("LLM response generated.")  # Log response generation
            self.text_edit.append("LLM Response:\n" + self.response + "\n")  # Append response to text edit area
            self.play_button.setEnabled(True)  # Enable play button
        except Exception as e:
            logging.error(f"Error during transcription or response generation: {e}")  # Log error

    def transcribe_audio(self, filename):
        """
        Transcribe the audio file using the Groq API.

        Args:
            filename: The name of the audio file to transcribe.

        Returns:
            The transcribed text.
        """
        with open(filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(filename, file.read()),  # Pass the audio file to the API
                model="whisper-large-v3",  # Specify the transcription model
                response_format="verbose_json",  # Specify the response format
            )
        return transcription.text  # Return the transcribed text

    def get_llm_response(self, transcription):
        """
        Get an LLM response to the transcribed text.

        Args:
            transcription: The transcribed text.

        Returns:
            The LLM response.
        """
        selected_model = self.model_selector.currentText()  # Get the selected LLM model
        system_prompt = self.system_prompt_input.text()  # Retrieve system prompt

        if selected_model.startswith("gemini"):  # Check if the selected model is a Gemini model
            response = self.get_gemini_response(transcription, selected_model,
                                                 system_prompt)  # Get Gemini response
        else:
            response = self.get_groq_response(transcription, selected_model,
                                                 system_prompt)  # Get Groq response

        return response  # Return the LLM response

    def get_groq_response(self, transcription, model_name, system_prompt):
        """
        Get a response from a Groq LLM.

        Args:
            transcription: The transcribed text.
            model_name: The name of the Groq model to use.
            system_prompt: The system prompt to use.

        Returns:
            The Groq LLM response.
        """
        # Dictionary for model max tokens
        MODEL_MAX_TOKENS = {
            "llama3-70b-8192": 8192,
            "llama-3.1-70b-versatile": 8000,
            "mixtral-8x7b-32768": 32768,
            "gemma2-9b-it": 8192,
        }

        # Determine the correct max_tokens based on the selected model
        max_tokens = MODEL_MAX_TOKENS.get(model_name, 8000)  # Default to 8000 if not found

        completion = client.chat.completions.create(
            model=model_name,  # Specify the Groq model
            messages=[
                {
                    "role": "system",
                    "content": system_prompt  # Use the provided system prompt
                },
                {
                    "role": "user",
                    "content": transcription  # Pass the transcribed text as user input
                }
            ],
            temperature=0.7,  # Temperature parameter for response generation
            max_tokens=max_tokens,  # Maximum number of tokens for the response
            top_p=1,  # Top_p parameter for response generation
            stream=True,  # Stream the response
            stop=None,  # Stop sequence for response generation
        )

        response = ""  # Initialize an empty string to store the response
        for chunk in completion:  # Iterate through the streamed response chunks
            content = chunk.choices[0].delta.content or ""  # Extract the content from the chunk
            response += content  # Append the content to the response string
        return response  # Return the complete response

    def get_gemini_response(self, transcription, model_name, system_prompt):
        """
        Get a response from a Google Gemini LLM.

        Args:
            transcription: The transcribed text.
            model_name: The name of the Gemini model to use.
            system_prompt: The system prompt to use.

        Returns:
            The Gemini LLM response.
        """
        generation_config = {
            "temperature": 1,  # Temperature parameter for response generation
            "top_p": 0.95,  # Top_p parameter for response generation
            "top_k": 64,  # Top_k parameter for response generation
            "max_output_tokens": 8192,  # Maximum number of tokens for the response
            "response_mime_type": "text/plain",  # Specify the response format
        }

        model = genai.GenerativeModel(
            model_name=model_name,  # Specify the Gemini model
            generation_config=generation_config,  # Pass the generation configuration
            system_instruction=system_prompt,  # Use the provided system prompt
        )

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        transcription,  # Pass the transcribed text as user input
                    ],
                }
            ]
        )

        response = chat_session.send_message(transcription)  # Send the transcribed text to the model

        return response.text  # Return the text of the response

    def play_audio_response(self):
        """
        Play the LLM response audio in a separate process.
        """
        if self.is_playing:  # Check if audio is already playing
            return  # Do nothing if audio is already playing

        self.stop_event = multiprocessing.Event()  # Create an event to signal the process to stop
        self.tts_process = multiprocessing.Process(target=tts_process, 
                                                   args=(self.response, self.stop_event)) # Remove tts_engine from arguments
        self.tts_process.start()  # Start the TTS process

        self.is_playing = True  # Set audio playing flag
        self.play_button.setEnabled(False)  # Disable play button
        self.stop_play_button.setEnabled(True)  # Enable stop playback button

        # Create a timer to check if the process has finished
        self.timer = threading.Timer(0.1, self.check_tts_process)  # Check every 0.1 seconds
        self.timer.start()

    def stop_audio_response(self):
        """
        Stop the LLM response audio playback.
        """
        if self.tts_process and self.tts_process.is_alive():  # Check if the TTS process is running
            self.tts_process.terminate()  # Terminate the process
            self.stop_event.set()  # Set the stop event
            self.tts_process = None  # Reset the process variable

            self.is_playing = False  # Clear audio playing flag
            self.play_button.setEnabled(True)  # Enable play button
            self.stop_play_button.setEnabled(False)  # Disable stop playback button

    def check_tts_process(self):
        """
        Check if the TTS process has finished and update the GUI accordingly.
        """
        if self.stop_event.is_set():
            self.is_playing = False  # Clear audio playing flag
            self.play_button.setEnabled(True)  # Enable play button
            self.stop_play_button.setEnabled(False)  # Disable stop playback button
            self.timer.cancel()  # Stop the timer
        else:
            self.timer = threading.Timer(0.1, self.check_tts_process)  # Schedule the next check
            self.timer.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)  # Create QApplication instance
    ex = AudioRecorder()  # Create AudioRecorder instance
    sys.exit(app.exec_())  # Run the application event loop