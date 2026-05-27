const historyList = document.getElementById('history-list');
const clearHistoryBtn = document.getElementById('clear-history');
const clearClipboardBtn = document.getElementById('clear-clipboard');

let clipboardHistory = [];

async function loadHistory() {
    clipboardHistory = await window.electronAPI.getHistory();
    renderHistory();
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString(); // Formats to local date and time
}

function renderHistory() {
    historyList.innerHTML = '';
    if (!clipboardHistory || clipboardHistory.length === 0) {
        const emptyMsg = document.createElement('li');
        emptyMsg.textContent = 'History is empty';
        emptyMsg.style.justifyContent = 'center';
        emptyMsg.style.color = '#7f8c8d';
        historyList.appendChild(emptyMsg);
        return;
    }

    clipboardHistory.forEach((item, index) => {
        const listItem = document.createElement('li');

        const contentWrapper = document.createElement('div');
        contentWrapper.classList.add('content-wrapper');

        const textSpan = document.createElement('span');
        const itemText = item.text || '';
        const isLong = itemText.length > 100;
        textSpan.textContent = isLong ? itemText.substring(0, 100) + '...' : itemText;
        
        if (isLong) {
            const showMore = document.createElement('a');
            showMore.href = '#';
            showMore.textContent = ' show more';
            showMore.classList.add('show-more');
            showMore.addEventListener('click', (e) => {
                e.preventDefault();
                textSpan.textContent = itemText;
            });
            textSpan.appendChild(showMore);
        }
        contentWrapper.appendChild(textSpan);

        const timestamp = document.createElement('span');
        timestamp.classList.add('timestamp');
        timestamp.textContent = item.timestamp ? formatTimestamp(item.timestamp) : 'Unknown Time';
        contentWrapper.appendChild(timestamp);

        listItem.appendChild(contentWrapper);

        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'item-buttons';

        const copyBtn = document.createElement('button');
        copyBtn.textContent = 'Copy';
        copyBtn.classList.add('copy-btn');
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(itemText);
        });
        buttonContainer.appendChild(copyBtn);

        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.classList.add('delete-btn');
        deleteBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this item from history?')) {
                clipboardHistory.splice(index, 1);
                window.electronAPI.saveHistory(clipboardHistory);
                renderHistory();
            }
        });
        buttonContainer.appendChild(deleteBtn);

        listItem.appendChild(buttonContainer);
        historyList.appendChild(listItem);
    });
}

clearHistoryBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear the entire clipboard history?')) {
        clipboardHistory = [];
        window.electronAPI.saveHistory(clipboardHistory);
        renderHistory();
    }
});

clearClipboardBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear the current clipboard content?')) {
        window.electronAPI.clearClipboard();
    }
});

window.electronAPI.onHistoryUpdated(() => {
    loadHistory();
});

loadHistory();

// Add this to the bottom of your existing renderer.js
const exitBtn = document.getElementById('exit-btn');
if (exitBtn) {
    exitBtn.addEventListener('click', () => {
        window.electronAPI.quitApp();
    });
}