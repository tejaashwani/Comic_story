/**
 * ComicCraft Main Script
 * Handles global UI helpers, navigation events, and common API actions.
 */

// Global Export to PDF function (Triggers Scenario 3 layout_builder & exporters pipeline)
async function exportToPDF(comicId) {
    // Show quick loading indicator on button
    const btn = document.getElementById("btn-download-pdf-top") || document.getElementById("btn-export-pdf-bottom");
    let originalHtml = "";
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.innerHTML = "⏳ Compiling PDF via exporters.py...";
        btn.disabled = true;
    }

    try {
        const response = await fetch("/api/export-pdf", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                comic_id: comicId,
                include_cover: true,
                page_format: "A4",
                orientation: "P"
            })
        });

        const data = await response.json();
        if (response.ok && data.success) {
            // Redirect to Export Success Page as specified in Scenario 3
            window.location.href = data.export_success_url;
        } else {
            alert("Error exporting PDF: " + (data.detail || data.message || "Unknown error"));
            if (btn) {
                btn.innerHTML = originalHtml;
                btn.disabled = false;
            }
        }
    } catch (err) {
        console.error("Export error:", err);
        alert("Network error while exporting PDF: " + err.message);
        if (btn) {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    }
}

// Toast notification helper
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `comic-toast toast-${type}`;
    toast.innerText = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.add("show");
    }, 10);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
