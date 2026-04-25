const genBtn = document.getElementById('gen-btn');
const promptInput = document.getElementById('prompt-input');
const statusBadge = document.getElementById('status-badge');
const statusToast = document.getElementById('status-toast');
const resultImg = document.getElementById('result-img');
const placeholder = document.getElementById('image-placeholder');

let isGenerating = false;

async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        statusBadge.innerText = data.status;
        
        if (data.is_generating) {
            isGenerating = true;
            genBtn.classList.add('generating');
            placeholder.classList.remove('hidden');
            resultImg.classList.add('hidden');
        } else {
            isGenerating = false;
            genBtn.classList.remove('generating');
            
            if (data.last_image) {
                resultImg.src = `/api/images/${data.last_image}?t=${Date.now()}`;
                resultImg.classList.remove('hidden');
                placeholder.classList.add('hidden');
            }
        }
    } catch (err) {
        console.error("Status update failed", err);
    }
}

genBtn.addEventListener('click', async () => {
    if (isGenerating) return;

    const prompt = promptInput.get('value') || ""; // Wait, promptInput is a textarea
    const text = promptInput.value.trim();

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: text })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast("Generation started...");
        } else {
            showToast("Error: " + data.error);
        }
    } catch (err) {
        showToast("Connection failed");
    }
});

function showToast(msg) {
    statusToast.innerText = msg;
    statusToast.classList.remove('hidden');
    setTimeout(() => {
        statusToast.classList.add('hidden');
    }, 3000);
}

// Poll status every 2 seconds
setInterval(updateStatus, 2000);
updateStatus();
