/**
 * OCR/PDF module — integrates with pywebview API for image and PDF OCR.
 *
 * Features:
 * - OCR from single image
 * - OCR from multi-page PDF with progress
 * - OCR from folder of images
 * - Side-by-side preview panel (image | editable OCR text | converted text)
 * - Progress modal for long-running OCR jobs
 */

(function () {
    "use strict";

    // ── DOM refs ──────────────────────────────────────────────────────
    const $ = (id) => document.getElementById(id);

    let previewVisible = false;
    let ocrTextDebouncer = null;

    // ── Check if pywebview API is available ───────────────────────────
    function hasApi() {
        return typeof window.pywebview !== "undefined" && window.pywebview.api;
    }

    // ── Toast helper ──────────────────────────────────────────────────
    function showToast(message, type) {
        type = type || "success";
        var toast = $("toast");
        if (!toast) return;
        toast.querySelector(".toast-message").textContent = message;
        toast.className = "toast show " + type;
        setTimeout(function() { toast.className = "toast"; }, 3000);
    }

    // ── Progress modal ────────────────────────────────────────────────
    function showProgress(title, text) {
        var modal = $("progressModal");
        if (!modal) return;
        $("progressTitle").textContent = title || "Processing...";
        $("progressText").textContent = text || "Starting...";
        $("progressPage").textContent = "";
        $("progressBar").style.width = "0%";
        modal.hidden = false;
    }

    function updateProgress(progress, current, total) {
        var modal = $("progressModal");
        if (!modal || modal.hidden) return;
        var pct = Math.round(progress * 100);
        $("progressBar").style.width = pct + "%";
        if (current && total) {
            $("progressPage").textContent = "Page " + current + " of " + total;
        }
        $("progressText").textContent = "Processing... " + pct + "%";
    }

    function hideProgress() {
        var modal = $("progressModal");
        if (modal) modal.hidden = true;
    }

    // ── OCR Image ─────────────────────────────────────────────────────
    function runImageOcr() {
        if (!hasApi()) {
            showToast("OCR requires desktop app mode", "error");
            return;
        }

        window.pywebview.api.pick_image().then(function(path) {
            if (!path) return;

            showProgress("OCR Image", "Processing " + path.replace(/[/\\]/g, "/").split("/").pop());

            window.pywebview.api.ocr_image(path).then(function(result) {
                hideProgress();
                if (result.error) {
                    showToast("OCR error: " + result.error, "error");
                    return;
                }
                var ocrText = result.text || "";
                if (!ocrText.trim()) {
                    showToast("No text detected in image", "error");
                    return;
                }

                // Populate OCR text in preview panel
                $("ocrText").value = ocrText;
                showPreviewPanel();
                updatePreviewConversion();
                var wordCount = ocrText.split(/\s+/).filter(function(w){return w}).length;
                showToast("OCR complete — " + wordCount + " words", "success");
            }).catch(function(err) {
                hideProgress();
                showToast("OCR failed: " + err, "error");
            });
        });
    }

    // ── OCR PDF ───────────────────────────────────────────────────────
    function runPdfOcr() {
        if (!hasApi()) {
            showToast("OCR requires desktop app mode", "error");
            return;
        }

        window.pywebview.api.pick_pdf().then(function(path) {
            if (!path) return;

            window.pywebview.api.get_pdf_info(path).then(function(info) {
                if (info.page_count > 0) {
                    showProgress("OCR PDF", info.page_count + " pages — processing");
                } else {
                    showProgress("OCR PDF", "Reading PDF...");
                }
            });

            window.pywebview.api.ocr_pdf(path).then(function(jobId) {
                if (!jobId) {
                    showToast("OCR engine not available", "error");
                    hideProgress();
                }
            });
        });
    }

    // ── OCR Folder ────────────────────────────────────────────────────
    function runFolderOcr() {
        if (!hasApi()) {
            showToast("OCR requires desktop app mode", "error");
            return;
        }

        window.pywebview.api.pick_folder().then(function(path) {
            if (!path) return;
            showProgress("OCR Folder", "Scanning " + path.replace(/[/\\]/g, "/").split("/").pop() + "...");
            window.pywebview.api.ocr_folder(path, false).then(function(jobId) {
                if (!jobId) {
                    showToast("OCR engine not available", "error");
                    hideProgress();
                }
            });
        });
    }

    // ── Preview Panel ─────────────────────────────────────────────────
    function showPreviewPanel() {
        var panel = $("previewPanel");
        if (!panel) return;
        panel.hidden = false;
        previewVisible = true;
        if ($("previewBtn")) $("previewBtn").classList.add("active");
    }

    function hidePreviewPanel() {
        var panel = $("previewPanel");
        if (!panel) return;
        panel.hidden = true;
        previewVisible = false;
        if ($("previewBtn")) $("previewBtn").classList.remove("active");
    }

    function togglePreviewPanel() {
        if (previewVisible) {
            hidePreviewPanel();
        } else {
            showPreviewPanel();
        }
    }

    function updatePreviewConversion() {
        var ocrText = ($("ocrText") || {}).value || "";
        if (!ocrText) {
            $("previewConverted").value = "";
            return;
        }

        // Use the in-browser converter directly (faster, no round-trip)
        if (typeof convertUnicodeToTera === "function") {
            $("previewConverted").value = convertUnicodeToTera(ocrText);
        } else if (hasApi()) {
            window.pywebview.api.convert_unicode_to_tera(ocrText).then(function(result) {
                $("previewConverted").value = result;
            });
        }
    }

    // ── pywebview event handlers ──────────────────────────────────────
    window._onOCRProgress = function (jobId, progress, current, total) {
        updateProgress(progress, current, total);
    };

    window._onOCRDone = function (jobId, resultJson) {
        hideProgress();
        try {
            var result = JSON.parse(resultJson);
            if (result.error) {
                showToast("OCR error: " + result.error, "error");
                return;
            }
            var text = result.text || "";
            if (!text.trim()) {
                showToast("No text found", "error");
                return;
            }

            // Append OCR'd text to input
            var input = $("inputText");
            if (input) {
                var separator = input.value ? "\n\n" : "";
                input.value += separator + text;
                // Trigger conversion
                if (window.doConvert) window.doConvert();
            }

            // Also populate preview if visible
            if ($("ocrText")) {
                $("ocrText").value = text;
                showPreviewPanel();
                updatePreviewConversion();
            }

            var pages = result.total_pages || (result.pages ? result.pages.length : 0);
            showToast("OCR complete — " + pages + " page" + (pages !== 1 ? "s" : ""), "success");
        } catch (e) {
            showToast("OCR result parse error", "error");
        }
    };

    // ── Wire up buttons ───────────────────────────────────────────────
    document.addEventListener("DOMContentLoaded", function () {
        var ocrImageBtn = $("ocrImageBtn");
        var ocrPdfBtn = $("ocrPdfBtn");
        var previewBtn = $("previewBtn");
        var closePreviewBtn = $("closePreviewBtn");

        if (ocrImageBtn) ocrImageBtn.addEventListener("click", runImageOcr);
        if (ocrPdfBtn) ocrPdfBtn.addEventListener("click", runPdfOcr);
        if (previewBtn) previewBtn.addEventListener("click", togglePreviewPanel);
        if (closePreviewBtn) closePreviewBtn.addEventListener("click", hidePreviewPanel);

        // OCR text edit → debounce → auto-convert
        var ocrText = $("ocrText");
        if (ocrText) {
            ocrText.addEventListener("input", function () {
                clearTimeout(ocrTextDebouncer);
                ocrTextDebouncer = setTimeout(updatePreviewConversion, 300);
            });
        }

        // Keyboard shortcut: Ctrl+Shift+I for OCR image (avoid Ctrl+I italic conflict)
        document.addEventListener("keydown", function (e) {
            var isCtrl = e.ctrlKey || e.metaKey;
            if (isCtrl && e.shiftKey && e.key.toLowerCase() === "i") {
                e.preventDefault();
                runImageOcr();
            }
        });
    });
})();
