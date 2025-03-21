function updateDate() {
    let today = new Date();
    let formattedDate = (today.getMonth()+1) + '/' + today.getDate() + '/' + today.getFullYear();
    document.getElementById("current-date").innerText = formattedDate;
}
window.onload = updateDate;

const uploadBox = document.getElementById("upload-box");
const fileInput = document.getElementById("file-input");

uploadBox.addEventListener("click", () => fileInput.click());

uploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadBox.classList.add("drag-over");
});

uploadBox.addEventListener("dragleave", () => {
    uploadBox.classList.remove("drag-over");
});

uploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadBox.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
});

fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) handleFileUpload(file);
});

function handleFileUpload(file) {
    if (!file.type.startsWith("image/")) {
    alert("Please upload an image file.");
    return;
    }
    alert(`File uploaded: ${file.name}`);
}