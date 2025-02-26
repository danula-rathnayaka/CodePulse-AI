const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000';  // Adjust this to match your FastAPI server address

async function reviewFile() {
    const filePath = document.getElementById('file-path').value;
    try {
        const response = await axios.get(`${API_BASE_URL}/review_file`, {
            params: { file_path: filePath }
        });
        document.getElementById('file-review-result').innerText = JSON.stringify(response.data, null, 2);
    } catch (error) {
        console.error('Error reviewing file:', error);
        document.getElementById('file-review-result').innerText = 'Error reviewing file';
    }
}

async function reviewFolder() {
    const projectPath = document.getElementById('project-path').value;
    const ignoreFiles = document.getElementById('ignore-files').value;
    const fileExtensions = document.getElementById('file-extensions').value;
    try {
        const response = await axios.get(`${API_BASE_URL}/review_folder`, {
            params: {
                project_path: projectPath,
                ignore_files: ignoreFiles,
                file_extensions: fileExtensions
            }
        });
        document.getElementById('folder-review-result').innerText = JSON.stringify(response.data, null, 2);
    } catch (error) {
        console.error('Error reviewing folder:', error);
        document.getElementById('folder-review-result').innerText = 'Error reviewing folder';
    }
}

async function fixBug() {
    const filePath = document.getElementById('bug-file-path').value;
    const errorMsg = document.getElementById('error-msg').value;
    try {
        const response = await axios.get(`${API_BASE_URL}/bug_fixer`, {
            params: {
                file_path: filePath,
                error_msg: errorMsg
            }
        });
        document.getElementById('bug-fixer-result').innerText = JSON.stringify(response.data, null, 2);
    } catch (error) {
        console.error('Error fixing bug:', error);
        document.getElementById('bug-fixer-result').innerText = 'Error fixing bug';
    }
}

// Expose functions to the global scope
window.reviewFile = reviewFile;
window.reviewFolder = reviewFolder;
window.fixBug = fixBug;
