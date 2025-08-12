document.getElementById('hintForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const hint = document.getElementById('hint').value;
    const submitBtn = document.getElementById('submitBtn');
    const responseDiv = document.getElementById('response');
    
    if (!hint.trim()) {
        showResponse('Please enter a prompt.', 'error');
        return;
    }
    
    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';
    showResponse('<div class="loading">Processing your prompt...</div>', 'success');
    
    try {
        const formData = new FormData();
        formData.append('hint', hint);
        
        const response = await fetch('/submit-hint', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showResponse(`
                <h3>Agent Response:</h3>
                <p><strong>Your prompt:</strong> ${data.hint}</p>
                <p><strong>Agent response:</strong></p>
                <div style="white-space: pre-wrap;">${data.response}</div>
            `, 'success');
        } else {
            showResponse(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showResponse(`Network error: ${error.message}`, 'error');
    } finally {
        // Re-enable button
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit';
    }
});

function showResponse(message, type) {
    const responseDiv = document.getElementById('response');
    responseDiv.innerHTML = message;
    responseDiv.className = `response ${type}`;
    responseDiv.style.display = 'block';
}

document.getElementById('loadOutputBtn').addEventListener('click', async () => {
    const responseDiv = document.getElementById('dailyOutput');
    responseDiv.innerHTML = 'Loading...';
    responseDiv.style.display = 'block';

    try {
        const res = await fetch('/daily_output.txt');
        const data = await res.json();

        if (data.success) {
            responseDiv.innerHTML = `<h3>Daily AI Output:</h3><pre>${data.output}</pre>`;
            //responseDiv.innerHTML = `<h3>Daily AI Output: </h3><pre>Yelow</pre>`;
        } else {
            responseDiv.innerHTML = `<span class="error">Error: ${data.error}</span>`;
        }
    } catch (err) {
        responseDiv.innerHTML = `<span class="error">Fetch failed: ${err.message}</span>`;
    }
});