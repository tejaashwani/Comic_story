/**
 * ComicCraft Preview & Reader Script
 * Manages comic reading, Scenario 2 mood/style iterations, and single panel editing.
 */

// Scenario 2: Mood & Style Iteration Modal Handlers
function openRegenerateModal() {
    const modal = document.getElementById('iterate-modal');
    if (modal) modal.style.display = 'flex';
}

function closeRegenerateModal() {
    const modal = document.getElementById('iterate-modal');
    if (modal) modal.style.display = 'none';
}

async function handleIterationSubmit(event) {
    event.preventDefault();
    const form = event.target;

    const payload = {
        prompt: form.prompt.value,
        character_name: form.character_name.value,
        setting: form.setting.value,
        tone: form.tone.value,
        art_style: form.art_style.value,
        num_panels: parseInt(form.num_panels.value, 10)
    };

    closeRegenerateModal();

    // Show generation modal
    const genModal = document.getElementById('generation-modal');
    if (genModal) {
        genModal.style.display = 'flex';
        document.getElementById('modal-status-title').innerText = "REGENERATING COMIC PIPELINE...";
        document.getElementById('modal-status-desc').innerText = `Re-drafting with "${payload.tone.toUpperCase()}" tone and "${payload.art_style.toUpperCase()}" style...`;
    }

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (response.ok && data.success) {
            window.location.href = data.data.preview_url;
        } else {
            if (genModal) genModal.style.display = 'none';
            alert("Iteration failed: " + (data.message || "Unknown error"));
        }
    } catch (err) {
        if (genModal) genModal.style.display = 'none';
        alert("Server error during regeneration: " + err.message);
    }
}

// Single Panel Edit / Re-roll Handlers
function openPanelEditModal(panelNum, currentDialogue, currentCaption) {
    const modal = document.getElementById('panel-edit-modal');
    if (!modal) return;

    document.getElementById('panel-edit-title').innerText = `Edit / Re-roll Panel #${panelNum}`;
    document.getElementById('edit-panel-num').value = panelNum;
    document.getElementById('edit-dialogue').value = currentDialogue || '';
    document.getElementById('edit-caption').value = currentCaption || '';
    document.getElementById('edit-custom-prompt').value = '';

    modal.style.display = 'flex';
}

function closePanelEditModal() {
    const modal = document.getElementById('panel-edit-modal');
    if (modal) modal.style.display = 'none';
}

async function handlePanelEditSubmit(event) {
    event.preventDefault();
    const panelNum = parseInt(document.getElementById('edit-panel-num').value, 10);
    const comicId = document.getElementById('edit-comic-id').value;
    const dialogue = document.getElementById('edit-dialogue').value.trim();
    const caption = document.getElementById('edit-caption').value.trim();
    const customPrompt = document.getElementById('edit-custom-prompt').value.trim();

    const saveBtn = document.getElementById('btn-save-panel-edit');
    const origText = saveBtn.innerText;
    saveBtn.innerText = "⏳ Regenerating...";
    saveBtn.disabled = true;

    try {
        const response = await fetch(`/api/regenerate-panel?comic_id=${comicId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                panel_number: panelNum,
                custom_prompt: customPrompt || null,
                updated_dialogue: dialogue,
                updated_caption: caption
            })
        });

        const result = await response.json();
        if (response.ok && result.success) {
            closePanelEditModal();
            // Reload page to reflect composite updates
            window.location.reload();
        } else {
            alert("Failed to update panel: " + (result.detail || result.message));
        }
    } catch (err) {
        alert("Error updating panel: " + err.message);
    } finally {
        saveBtn.innerText = origText;
        saveBtn.disabled = false;
    }
}
