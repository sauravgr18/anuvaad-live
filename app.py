from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
from moviepy.editor import VideoFileClip, AudioFileClip
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
from werkzeug.utils import secure_filename
import uuid
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure application
app.template_folder = 'templates'
app.static_folder = 'static'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Define allowed extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}

# Define the Downloads folder path
DOWNLOADS_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")

# Define languages dictionary
languages = {
    "Hindi": "hi",
    "Odia": "or",
    "Bengali": "bn",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Marathi": "mr",
    "Urdu": "ur",
    "Assamese": "as",
    "Sanskrit": "sa",
    "Kashmiri": "ks",
    "Konkani": "kok",
    "Santali": "sat",
    "Nepali": "ne",
    "Maithili": "maith",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Russian": "ru",
    "Chinese": "zh",
    "Arabic": "ar",
    "Portuguese": "pt",
    "Japanese": "ja",
    "Korean": "ko",
    "Turkish": "tr",
    "Persian": "fa",
    "Italian": "it",
    "Dutch": "nl",
    "Swedish": "sv",
    "Finnish": "fi",
    "Danish": "da",
    "Norwegian": "no",
    "Thai": "th",
    "Vietnamese": "vi",
    "Filipino": "tl",
    "Czech": "cs",
    "Hungarian": "hu",
    "Romanian": "ro",
    "Bulgarian": "bg",
    "Slovak": "sk",
    "Croatian": "hr",
    "Serbian": "sr",
    "Slovenian": "sl",
    "Ukrainian": "uk",
    "Lithuanian": "lt",
    "Latvian": "lv",
    "Estonian": "et",
    "Hebrew": "he",
    "Malay": "ms",
    "Indonesian": "id",
    "Swahili": "sw",
    "Hausa": "ha",
    "Yoruba": "yo",
    "Igbo": "ig",
    "Amharic": "am",
    "Somali": "so",
    "Burmese": "my",
    "Thai (Central)": "th",
    "Khmer": "km",
    "Lao": "lo",
    "Tagalog": "tl",
    "Tigrinya": "ti",
    "Nepal Bhasa": "new",
    "Fijian": "fj",
    "Hmong": "hmn",
    "Samoan": "sm",
    "Māori": "mi",
    "Tahitian": "ty",
    "Haitian Creole": "ht",
    "Zulu": "zu",
    "Xhosa": "xh",
    "Kazakh": "kk",
    "Uzbek": "uz",
    "Turkmen": "tk",
    "Azerbaijani": "az",
    "Tatar": "tt",
    "Armenian": "hy",
    "Georgian": "ka",
    "Macedonian": "mk",
    "Albanian": "sq",
    "Bosnian": "bs",
    "Bengali (Bangladesh)": "bn-BD",
    "Bengali (India)": "bn-IN",
    "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW",
    "English (UK)": "en-GB",
    "English (US)": "en-US",
    "French (Canada)": "fr-CA",
    "Spanish (Mexico)": "es-MX",
}


def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the original extension"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    return f"{str(uuid.uuid4())}.{ext}"


def clean_up_files(*files):
    """Clean up temporary files"""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            logger.error(f"Error cleaning up file {file}: {str(e)}")

# Routes
@app.route('/')
def index():
    """Serve the frontend"""
    return render_template('index.html')


@app.route('/api/supported-languages', methods=['GET'])
def get_supported_languages():
    """Return list of supported languages"""
    try:
        return jsonify(list(languages.keys()))
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/translate-video', methods=['POST'])
def translate_video():
    """Handle video translation"""
    try:
        # Check if video file is present in request
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check if target language is provided and valid
        target_language = request.form.get('target_language')
        if not target_language or target_language not in languages:
            logger.error(
                f"Invalid or missing target language: {target_language}")
            return jsonify({'error': 'Invalid target language'}), 400

        if video_file and allowed_file(video_file.filename):
            # Generate a unique filename for the final output
            original_filename = secure_filename(video_file.filename)
            video_path = os.path.join(tempfile.gettempdir(
            ), generate_unique_filename(original_filename))

            # Save translated video directly to the Downloads folder
            final_output_path = os.path.join(
                DOWNLOADS_FOLDER, f"translated_{original_filename}")

            try:
                # Save uploaded video
                video_file.save(video_path)
                logger.info(f"Video saved: {video_path}")

                # Extract audio using a temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_tempfile:
                    video = VideoFileClip(video_path)
                    video.audio.write_audiofile(audio_tempfile.name)
                    logger.info("Audio extracted successfully")

                    # Transcribe audio
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(audio_tempfile.name) as source:
                        audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio)
                    logger.info("Audio transcribed successfully")

                    # Translate text
                    translator = Translator()
                    translated = translator.translate(
                        text, dest=languages[target_language])
                    logger.info("Text translated successfully")

                    # Convert to speech using another temporary file
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as translated_audio_tempfile:
                        tts = gTTS(text=translated.text,
                                   lang=languages[target_language])
                        tts.save(translated_audio_tempfile.name)
                        logger.info("Text converted to speech successfully")

                        # Merge audio with video
                        translated_audio = AudioFileClip(
                            translated_audio_tempfile.name)
                        final_video = video.set_audio(translated_audio)
                        final_video.write_videofile(
                            final_output_path, codec="libx264", audio_codec="aac")
                        logger.info("Video processing completed successfully")

                # Release resources and close video and audio clips
                video.close()
                translated_audio.close()

                # Send the processed video file
                response = send_file(
                    final_output_path,
                    mimetype='video/mp4',
                    as_attachment=True,
                    download_name=original_filename
                )

                # Clean up files after sending
                @response.call_on_close
                def cleanup():
                    clean_up_files(video_path, final_output_path,
                                   audio_tempfile.name, translated_audio_tempfile.name)

                return response

            except Exception as e:
                # Clean up files in case of error
                clean_up_files(video_path, final_output_path)
                logger.error(f"Error processing video: {str(e)}")
                return jsonify({'error': 'Error processing video'}), 500

        return jsonify({'error': 'Invalid file type'}), 400

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy'
    })


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
