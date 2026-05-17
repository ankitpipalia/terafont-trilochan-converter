/**
 * api-bridge.js — server-mode shim for the PyWebView API.
 *
 * When the UI is loaded inside the desktop app, `window.pywebview.api`
 * is injected by PyWebView itself. When loaded as a normal web page
 * (e.g. served by app/server.py or from GitHub Pages), this shim
 * substitutes a fetch-based equivalent so the rest of the UI keeps
 * working without changes.
 *
 * Strategy:
 *   - If pywebview is present, do nothing (desktop wins).
 *   - Otherwise, check if /api/health is reachable. If yes → install
 *     a REST-backed `window.pywebview.api`. If not (e.g. GitHub Pages,
 *     no backend), install a stub that surfaces friendly errors and
 *     marks features as unavailable.
 */

(function () {
    "use strict";

    if (typeof window.pywebview !== "undefined" && window.pywebview.api) {
        return; // desktop mode — nothing to do
    }

    function jsonPost(url, body) {
        return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body || {}),
        }).then(r => {
            if (!r.ok) return r.text().then(t => { throw new Error(`${r.status}: ${t}`); });
            return r.json();
        });
    }

    function formPost(url, file) {
        const fd = new FormData();
        fd.append("file", file);
        return fetch(url, { method: "POST", body: fd })
            .then(r => {
                if (!r.ok) return r.text().then(t => { throw new Error(`${r.status}: ${t}`); });
                return r.json();
            });
    }

    function saveBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // ── REST-backed implementation ──────────────────────────────────
    const restApi = {
        convert_unicode_to_tera: (text) =>
            jsonPost("/api/convert/unicode-to-tera", { text }).then(r => r.text),
        convert_tera_to_unicode: (text) =>
            jsonPost("/api/convert/tera-to-unicode", { text }).then(r => r.text),

        get_version: () => fetch("/api/version").then(r => r.json()).then(r => r.version),
        doc_capabilities: () => fetch("/api/capabilities").then(r => r.json()),
        has_ocr: () => fetch("/api/capabilities").then(r => r.json()).then(r => !!r.ocr),

        // In server mode the browser drives file selection via <input>,
        // so the pick_* methods are no-ops. The UI's upload button
        // already falls back to a file input when no pywebview is available.
        pick_image: () => Promise.resolve(null),
        pick_pdf: () => Promise.resolve(null),
        pick_folder: () => Promise.resolve(null),
        pick_document: () => Promise.resolve(null),

        // Exports return a Blob which we trigger as a browser download.
        export_docx: (content, filename) =>
            fetch("/api/export/docx", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content, filename }),
            }).then(r => {
                if (!r.ok) return r.text().then(t => ({ path: null, error: t }));
                return r.blob().then(b => {
                    saveBlob(b, filename || "output.docx");
                    return { path: filename || "output.docx" };
                });
            }),
        export_pdf: (content, filename) =>
            fetch("/api/export/pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ content, filename }),
            }).then(r => {
                if (!r.ok) return r.text().then(t => ({ path: null, error: t }));
                return r.blob().then(b => {
                    saveBlob(b, filename || "output.pdf");
                    return { path: filename || "output.pdf" };
                });
            }),

        // OCR — files come from a hidden <input type=file> that the
        // UI surfaces when it sees we're in server mode.
        ocr_image: (file) => file ? formPost("/api/ocr/image", file) :
            Promise.resolve({ text: "", error: "no file" }),
        ocr_pdf: (file) => file ? formPost("/api/ocr/pdf", file) :
            Promise.resolve({ text: "", error: "no file" }),
        get_pdf_info: (file) => file ? formPost("/api/ocr/pdf-info", file) :
            Promise.resolve({}),

        // Server-mode settings are stateless for now. Persist client-side
        // via localStorage instead (the UI already does this for theme/mode).
        get_settings: () => Promise.resolve({
            engine: "paddle", dpi: 300,
            theme: localStorage.getItem("theme") || "dark",
            default_mode: localStorage.getItem("conv_mode") || "unicodeToTera",
        }),
        set_settings: (s) => Promise.resolve(s),
        reset_settings: () => Promise.resolve({}),
        get_recent_files: () => Promise.resolve([]),
        get_log_dir: () => Promise.resolve(""),

        // Save plain-text via blob download
        save_text: (content, filename) => {
            const blob = new Blob([content || ""], { type: "text/plain;charset=utf-8" });
            saveBlob(blob, filename || "output.txt");
            return Promise.resolve({ path: filename });
        },
        read_text_file: () => Promise.resolve({ text: "", error: "n/a in browser" }),
        read_docx: () => Promise.resolve({ text: "", error: "n/a in browser" }),
    };

    // ── Stub for fully-static deployments (GitHub Pages etc) ────────
    function stubMethod(name) {
        return () => Promise.reject(
            new Error(`${name} requires the desktop app or a self-hosted server`)
        );
    }
    const browserOnlyStub = {
        convert_unicode_to_tera: null,  // filled in below — used by in-page JS
        convert_tera_to_unicode: null,
        get_version: () => Promise.resolve("web"),
        doc_capabilities: () => Promise.resolve({ ocr: false, docx: false, pdf: false }),
        has_ocr: () => Promise.resolve(false),
        pick_image: stubMethod("Image picker"),
        pick_pdf: stubMethod("PDF picker"),
        pick_folder: stubMethod("Folder picker"),
        pick_document: stubMethod("Document picker"),
        export_docx: stubMethod("DOCX export"),
        export_pdf: stubMethod("PDF export"),
        ocr_image: stubMethod("Image OCR"),
        ocr_pdf: stubMethod("PDF OCR"),
        get_settings: () => Promise.resolve({
            theme: localStorage.getItem("theme") || "dark",
            default_mode: localStorage.getItem("conv_mode") || "unicodeToTera",
        }),
        set_settings: () => Promise.resolve({}),
        get_recent_files: () => Promise.resolve([]),
        save_text: restApi.save_text,
    };

    // ── Probe /api/health to decide which mode we're in ─────────────
    function probe() {
        return fetch("/api/health", { method: "GET" })
            .then(r => r.ok)
            .catch(() => false);
    }

    probe().then(hasBackend => {
        if (hasBackend) {
            window.pywebview = { api: restApi };
            // Optional UX nicety: show a small badge so users know they're
            // talking to a server (could be different from the embedded UI).
            console.info("[gujarati-converter] Connected to backend at " + location.origin);
        } else {
            // Fall back to browser-only mode. The in-page JS converter
            // continues to handle conversion; OCR/PDF/DOCX show errors.
            window.pywebview = { api: browserOnlyStub };
            console.info("[gujarati-converter] Browser-only mode — no backend detected");
        }
        document.dispatchEvent(new CustomEvent("pywebviewready", {
            detail: { mode: hasBackend ? "server" : "browser" },
        }));
    });
})();
