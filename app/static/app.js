const API_URL = '/workflows';
let currentRunId = null;
let pollInterval = null;

const elements = {
    input: document.getElementById('requestInput'),
    btn: document.getElementById('generateBtn'),
    error: document.getElementById('errorMsg'),
    statusCard: document.getElementById('workflowStatus'),
    runId: document.getElementById('runId'),
    globalStatus: document.getElementById('globalStatus'),
    createTime: document.getElementById('createTime'),
    originalRequest: document.getElementById('originalRequest'),
    nodesList: document.getElementById('nodesList'),
    clarificationSection: null // Will be dynamically added
};

let conversationContext = "";

// Add global variable for pending question
let pendingClarificationQuestion = null;

async function submitRequest() {
    const request = elements.input.value.trim();
    if (!request) return;

    elements.btn.disabled = true;
    elements.btn.textContent = 'Processing...';
    elements.error.classList.add('hidden');
    elements.nodesList.innerHTML = '<div class="placeholder-text">Consulting agents...</div>';

    // If there was a pending question, append it and the new answer to context
    if (pendingClarificationQuestion) {
        conversationContext += `\nAgent: ${pendingClarificationQuestion}\nUser: ${request}\n`;
        pendingClarificationQuestion = null; // Reset
    }

    // Build payload with context if available
    const payload = { request };
    if (conversationContext) {
        payload.context = conversationContext;
    }

    try {
        const response = await fetch(`${API_URL}/from-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to generate workflow');
        }

        const data = await response.json();

        // Handle Clarification
        if (data.status === 'NEEDS_CLARIFICATION') {
            handleClarification(data.clarification);
            elements.btn.disabled = false;
            elements.btn.textContent = 'Generate & Run Workflow';
            return;
        }

        // Handle Success
        startPolling(data.run_id);
        renderDashboard(data);

        // Reset context on successful start
        conversationContext = "";

    } catch (err) {
        elements.error.textContent = err.message;
        elements.error.classList.remove('hidden');
        elements.btn.disabled = false;
        elements.btn.textContent = 'Generate & Run Workflow';
    }
}

function handleClarification(question) {
    elements.nodesList.innerHTML = '';

    // Store the question so we can pair it with the next user input
    pendingClarificationQuestion = question;

    const container = document.createElement('div');
    container.className = 'status-card';
    container.style.border = '1px solid #f59e0b'; // Warning color

    container.innerHTML = `
        <div style="color: #f59e0b; font-weight: bold; margin-bottom: 10px;">⚠️ Needs Clarification</div>
        <div style="font-size: 1.1rem; margin-bottom: 15px;">${question}</div>
        <div style="font-size: 0.9rem; color: #94a3b8; font-style: italic;">
            Please refine your request in the input box above.
        </div>
    `;

    elements.nodesList.appendChild(container);
}

function startPolling(runId) {
    if (pollInterval) clearInterval(pollInterval);
    currentRunId = runId;

    pollInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_URL}/${runId}`);
            const data = await res.json();
            renderDashboard(data);

            if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                clearInterval(pollInterval);
                elements.btn.disabled = false;
                elements.btn.textContent = 'Generate & Run Workflow';
            }
        } catch (err) {
            console.error('Polling error:', err);
        }
    }, 1000); // Poll every second
}

function renderDashboard(data) {
    elements.statusCard.classList.remove('hidden');
    elements.runId.textContent = data.run_id;
    elements.globalStatus.textContent = data.status;
    elements.globalStatus.className = `status-badge ${data.status}`;
    elements.createTime.textContent = new Date(data.created_at * 1000).toLocaleString();
    if (data.original_request) {
        elements.originalRequest.textContent = data.original_request;
    }

    elements.nodesList.innerHTML = '';

    // Sort nodes to ensure consistent order (optional logic could sort by dependency)
    Object.entries(data.nodes).forEach(([nodeId, node]) => {
        const card = document.createElement('div');
        card.className = 'node-card';

        let outputHtml = '';
        if (node.output) {
            // Check for image URL (ChartAgent)
            if (node.output.image_url) {
                outputHtml = `
                    <div class="node-output text-center">
                        <img src="${node.output.image_url}" alt="Generated Chart" style="max-width: 100%; border-radius: 8px; border: 1px solid #334155; margin-top: 10px;">
                        ${node.output.description ? `<p style="font-size: 0.9rem; color: #94a3b8; margin-top: 5px;">${node.output.description}</p>` : ''}
                    </div>`;
            }
            // Check for summary (SummarizerAgent)
            else if (node.output.summary) {
                outputHtml = `
                    <div class="node-output">
                        <strong>Summary:</strong>
                        <div style="background: #1e293b; padding: 10px; border-radius: 6px; margin-top: 5px; color: #e2e8f0; white-space: pre-wrap;">${node.output.summary}</div>
                    </div>`;
            }
            // Check for analysis (AnalysisAgent)
            else if (node.output.analysis) {
                outputHtml = `
                    <div class="node-output">
                        <strong>Analysis:</strong>
                        <div style="background: #1e293b; padding: 10px; border-radius: 6px; margin-top: 5px; color: #e2e8f0; white-space: pre-wrap;">${node.output.analysis}</div>
                    </div>`;
            }
            // Default JSON view
            else {
                outputHtml = `
                    <div class="node-output">
                        <strong>Output:</strong>
                        <div class="json-block">${JSON.stringify(node.output, null, 2)}</div>
                    </div>`;
            }
        } else if (node.error) {
            outputHtml = `
                <div class="node-output error">
                    <strong>Error:</strong> ${node.error}
                </div>`;
        }

        const statusClass = `status-badge ${node.status}`;

        card.innerHTML = `
            <div class="node-header">
                <span class="node-title">${nodeId}</span>
                <span class="${statusClass}">${node.status}</span>
            </div>
            
            <div class="node-logs">
                ${node.logs.length ? node.logs.join('<br>') : 'Waiting to start...'}
            </div>
            ${outputHtml}
        `;
        elements.nodesList.appendChild(card);
    });
}

elements.btn.addEventListener('click', submitRequest);
