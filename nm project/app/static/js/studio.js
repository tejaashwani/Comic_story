/**
 * ComicCraft Studio Interaction Script
 * Manages form inputs, presets (Scenario 1 & 2), and generation feedback.
 */

// Tone Tile Selection Handler
function onToneChanged(radioInput) {
    document.querySelectorAll('.tone-tile').forEach(tile => tile.classList.remove('selected'));
    if (radioInput.checked) {
        radioInput.closest('.tone-tile').classList.add('selected');
    }
}

// Art Style Card Selection Handler
function onStyleChanged(radioInput) {
    document.querySelectorAll('.style-card').forEach(card => card.classList.remove('selected'));
    if (radioInput.checked) {
        radioInput.closest('.style-card').classList.add('selected');
    }
}

// Scenario Presets Switcher
function applyPreset(presetType) {
    const promptInput = document.getElementById('prompt');
    const charInput = document.getElementById('character_name');
    const settingInput = document.getElementById('setting');
    const panelsSelect = document.getElementById('num_panels');

    document.querySelectorAll('.preset-pill').forEach(p => p.classList.remove('active-preset'));

    if (presetType === 'scenario1') {
        // Scenario 1: Brave Fox in Enchanted Forest (Dramatic & Anime)
        document.getElementById('preset-scenario-1')?.classList.add('active-preset');
        promptInput.value = "A brave fox exploring an enchanted forest, discovering hidden ancient spirits.";
        charInput.value = "Rusty the Fox";
        settingInput.value = "Enchanted luminescent forest";
        panelsSelect.value = "4";
        selectTone('dramatic');
        selectStyle('anime');
    } else if (presetType === 'scenario2') {
        // Scenario 2: Funny Cartoonish Comic Strip (Funny & Classic Comic Book)
        document.getElementById('preset-scenario-2')?.classList.add('active-preset');
        promptInput.value = "An apprentice wizard tries to bake a magical cake, but the dough comes alive and chases him through the kitchen.";
        charInput.value = "Barnaby the Wizard";
        settingInput.value = "Alchemical castle kitchen";
        panelsSelect.value = "4";
        selectTone('funny');
        selectStyle('comic book');
    } else if (presetType === 'cyberpunk') {
        document.getElementById('preset-scenario-3')?.classList.add('active-preset');
        promptInput.value = "A cyborg detective uncovers a stolen memory chip in the rain-slicked neon underworld.";
        charInput.value = "Cipher Vance";
        settingInput.value = "Neo-Shinjuku Sector 7";
        panelsSelect.value = "4";
        selectTone('mysterious');
        selectStyle('cyberpunk');
    }
}

function selectTone(toneValue) {
    const radio = document.querySelector(`input[name="tone"][value="${toneValue}"]`);
    if (radio) {
        radio.checked = true;
        onToneChanged(radio);
    }
}

function selectStyle(styleValue) {
    const radio = document.querySelector(`input[name="art_style"][value="${styleValue}"]`);
    if (radio) {
        radio.checked = true;
        onStyleChanged(radio);
    }
}

// Form Submission & Live Progress Animation
async function handleComicSubmission(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = document.getElementById('btn-generate-comic');

    // Extract form values
    const payload = {
        prompt: form.prompt.value.trim(),
        character_name: form.character_name.value.trim(),
        setting: form.setting.value.trim(),
        tone: form.tone.value,
        art_style: form.art_style.value,
        num_panels: parseInt(form.num_panels.value, 10)
    };

    if (!payload.prompt || !payload.character_name || !payload.setting) {
        alert("Please fill in all required fields!");
        return;
    }

    // Launch Animated Generation Modal
    const modal = document.getElementById('generation-modal');
    const progressBar = document.getElementById('generation-progress-bar');
    const titleElem = document.getElementById('modal-status-title');
    const descElem = document.getElementById('modal-status-desc');

    modal.style.display = 'flex';
    submitBtn.disabled = true;

    // Simulated Step Progress for real-time user feedback
    let progress = 15;
    progressBar.style.width = `${progress}%`;

    const timer1 = setTimeout(() => {
        progress = 40;
        progressBar.style.width = `${progress}%`;
        titleElem.innerText = "GEMINI STORYBOARDING...";
        descElem.innerText = `Crafting a ${payload.tone} storyline with punchy dialogues for ${payload.character_name}.`;
        document.getElementById('step-outline')?.classList.add('active');
    }, 1200);

    const timer2 = setTimeout(() => {
        progress = 65;
        progressBar.style.width = `${progress}%`;
        titleElem.innerText = "STABLE DIFFUSION SYNTHESIS...";
        descElem.innerText = `Rendering panel scenes in ${payload.art_style.toUpperCase()} style.`;
        document.getElementById('step-diffusers')?.classList.add('active');
    }, 3500);

    const timer3 = setTimeout(() => {
        progress = 85;
        progressBar.style.width = `${progress}%`;
        titleElem.innerText = "ASSEMBLING COMIC PANELS...";
        descElem.innerText = "layout_builder.py is binding narrative captions and speech bubbles.";
        document.getElementById('step-layout')?.classList.add('active');
    }, 6000);

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        // Clear mock timers
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);

        if (response.ok && result.success) {
            progressBar.style.width = '100%';
            titleElem.innerText = "COMIC READY! 💥";
            descElem.innerText = "Redirecting to your interactive preview...";
            document.getElementById('step-ready')?.classList.add('active');

            setTimeout(() => {
                window.location.href = result.data.preview_url;
            }, 800);
        } else {
            modal.style.display = 'none';
            submitBtn.disabled = false;
            alert("Generation failed: " + (result.message || "Unknown error"));
        }
    } catch (err) {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        modal.style.display = 'none';
        submitBtn.disabled = false;
        console.error("Submission error:", err);
        alert("Server error occurred during generation: " + err.message);
    }
}
