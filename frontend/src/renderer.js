// Function to fetch and log file review
async function fetchFileReview() {
  console.log(document.getElementById("file-path").value);
  const filePath = document.getElementById("file-path").value;
  try {
    const response = await fetch(
      `http://localhost:8000/review_file?file_path=${encodeURIComponent(
        filePath
      )}`
    );
    const data = await response.json();

    // Extracting the markdown review content
    const review = Object.values(data.review)[0]; // Get the first value from the review object

    document.getElementById("file-review-result").innerHTML =
      marked.parse(review);
  } catch (error) {
    console.error("Error fetching file review:", error);
    document.getElementById("file-review-result").textContent =
      "Error: " + error.message;
  }
}

// Function to fetch and log folder review
async function fetchFolderReview() {
  const projectPath = document.getElementById("project-path").value;
  const ignoreFiles = document.getElementById("ignore-files").value;
  const fileExtensions = document.getElementById("file-extensions").value;
  try {
    const response = await fetch(
      `http://localhost:8000/review_folder?project_path=${encodeURIComponent(
        projectPath
      )}&ignore_files=${encodeURIComponent(
        ignoreFiles
      )}&file_extensions=${encodeURIComponent(fileExtensions)}`
    );
    const data = await response.json();
    console.log("Folder Review:", data);
    document.getElementById("folder-review-result").textContent =
      JSON.stringify(data, null, 2);
  } catch (error) {
    console.error("Error fetching folder review:", error);
    document.getElementById("folder-review-result").textContent =
      "Error: " + error.message;
  }
}

// Function to fetch and log bug fixer result
async function fetchBugFixer() {
  const filePath = document.getElementById("bug-file-path").value;
  const errorMsg = document.getElementById("error-msg").value;
  try {
    const response = await fetch(
      `http://localhost:8000/bug_fixer?file_path=${encodeURIComponent(
        filePath
      )}&error_msg=${encodeURIComponent(errorMsg)}`
    );
    const data = await response.json();
    console.log("Bug Fixer Result:", data);
    document.getElementById("bug-fixer-result").textContent = JSON.stringify(
      data,
      null,
      2
    );
  } catch (error) {
    console.error("Error fetching bug fixer result:", error);
    document.getElementById("bug-fixer-result").textContent =
      "Error: " + error.message;
  }
}

// Add event listeners to buttons
document
  .getElementById("review-file-btn")
  .addEventListener("click", fetchFileReview);
document
  .getElementById("review-folder-btn")
  .addEventListener("click", fetchFolderReview);
document.getElementById("fix-bug-btn").addEventListener("click", fetchBugFixer);
