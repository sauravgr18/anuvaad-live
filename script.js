const API_URL = 'http://localhost:5000/api';
let selectedFile = null;

// Initialize elements
const videoInput = document.getElementById('video-input');
const fileName = document.getElementById('file-name');
const languageSelect = document.getElementById('language-select');
const translateBtn = document.getElementById('translate-btn');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const errorMessage = document.getElementById('error-message');

// Fetch supported languages
async function fetchLanguages() {
    try {
        const response = await axios.get(`${API_URL}/supported-languages`);
        const languages = response.data;
        
        languages.forEach(language => {
            const option = document.createElement('option');
            option.value = language;
            option.textContent = language;
            languageSelect.appendChild(option);
        });
    } catch (error) {
        showError('Failed to load supported languages');
    }
}

// Handle file selection
videoInput.addEventListener('change', (e) => {
    selectedFile = e.target.files[0];
    fileName.textContent = selectedFile ? selectedFile.name : 'Click to select video';
});

// Handle form submission
translateBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        showError('Please select a video file');
        return;
    }

    if (!languageSelect.value) {
        showError('Please select a target language');
        return;
    }

    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('video', selectedFile);
        formData.append('target_language', languageSelect.value);

        // Show progress bar
        showProgress();
        translateBtn.disabled = true;

        // Make API request
        const response = await axios.post(`${API_URL}/translate-video`, formData, {
            responseType: 'blob',
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                updateProgress(percentCompleted);
            }
        });

        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `translated_${selectedFile.name}`);
        document.body.appendChild(link);
        link.click();
        link.remove();

        // Reset form
        resetForm();
    } catch (error) {
        showError('Translation failed. Please try again.');
    } finally {
        hideProgress();
        translateBtn.disabled = false;
    }
});

// Utility functions
function showProgress() {
    progressContainer.classList.remove('hidden');
    errorMessage.classList.add('hidden');
}

function hideProgress() {
    progressContainer.classList.add('hidden');
}

function updateProgress(percent) {
    progressBar.style.width = `${percent}%`;
    progressText.textContent = `Please Wait! Video is Processing...`;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function resetForm() {
    videoInput.value = '';
    fileName.textContent = 'Click to select video';
    selectedFile = null;
    languageSelect.value = '';
    errorMessage.classList.add('hidden');
}

// Initialize the page
fetchLanguages();
