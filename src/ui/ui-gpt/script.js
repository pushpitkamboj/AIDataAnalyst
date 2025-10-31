document.addEventListener("DOMContentLoaded", () => {
  const csvBtn = document.getElementById("csvBtn");
  const dbBtn = document.getElementById("dbBtn");
  const csvSection = document.getElementById("csvSection");
  const dbSection = document.getElementById("dbSection");

  const fileInput = document.getElementById("fileInput");
  const fileNameText = document.getElementById("fileNameText");
  const uploadBtn = document.getElementById("uploadBtn");
  const uploadStatus = document.getElementById("uploadStatus");

  // holds the public URL returned by the server after upload
  let uploadedCsvUrl = localStorage.getItem("uploadedCsvUrl") || null;

  // small helper to set status text
  function setStatus(text, isError = false) {
    uploadStatus.textContent = text;
    uploadStatus.style.color = isError ? "#b91c1c" : "#374151"; // red for error, gray for normal
  }

  // Tab switching (keeps previous simple behavior)
  function activateTab(selectedBtn, otherBtn, showSection, hideSection) {
    selectedBtn.classList.add("bg-white", "text-indigo-600", "border", "border-gray-200");
    otherBtn.classList.remove("bg-white", "text-indigo-600", "border", "border-gray-200");
    otherBtn.classList.add("bg-gray-100", "text-gray-500");

    showSection.classList.remove("hidden");
    hideSection.classList.add("hidden");
  }

  if (csvBtn && dbBtn && csvSection && dbSection) {
    csvBtn.addEventListener("click", () => {
      activateTab(csvBtn, dbBtn, csvSection, dbSection);
    });

    dbBtn.addEventListener("click", () => {
      activateTab(dbBtn, csvBtn, dbSection, csvSection);
    });
  }

  // Update file name when user selects file
  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    fileNameText.textContent = file ? file.name : "No file chosen";
    // reset status if a new file selected
    if (file) setStatus("");
  });

  // Upload handler
  uploadBtn.addEventListener("click", async () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) {
      setStatus("Please choose a CSV file before uploading.", true);
      return;
    }

    // Basic client-side validation: CSV mime/extension
    const isCsv =
      file.type === "text/csv" ||
      file.name.toLowerCase().endsWith(".csv") ||
      file.type === "application/vnd.ms-excel";
    if (!isCsv) {
      setStatus("Selected file does not appear to be a CSV. Please select a .csv file.", true);
      return;
    }

    const form = new FormData();
    form.append("file", file);

    // UI feedback
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading... 0%";
    setStatus("Starting upload...");

    try {
      const response = await axios.post("http://127.0.0.1:8000/upload", form, {
        // Let axios set Content-Type and boundary for FormData
        onUploadProgress: (progressEvent) => {
          if (progressEvent.lengthComputable) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            uploadBtn.textContent = `Uploading... ${percent}%`;
            setStatus(`Uploading... ${percent}%`);
          }
        },
        timeout: 120000, // 2 minutes just in case
      });

      // Expect server to return JSON like: { message: "https://public-url/path.csv" }
      if (response && response.data) {
        const serverMsg = response.data.message || response.data.url || null;

        if (serverMsg) {
          uploadedCsvUrl = serverMsg;
          // persist for future use
          try {
            localStorage.setItem("uploadedCsvUrl", uploadedCsvUrl); // ======================================================
            localStorage.setItem("uploadedCsvMeta", JSON.stringify({ value: uploadedCsvUrl, savedAt: Date.now() }));

          } catch (err) {
            // ignore storage errors
            // but still keep in variable
          }

          uploadBtn.textContent = "Upload File";
          uploadBtn.disabled = false;
          setStatus("Upload successful. File URL saved.");
          console.log("Uploaded CSV public URL:", uploadedCsvUrl);
          setTimeout(() => { window.location.href = "chat.html"; }, 500); // Redirect after short delay
        } else {
          throw new Error("Upload response did not contain a `message` field.");
        }
      } else {
        throw new Error("No response data from server.");
      }
    } catch (err) {
      console.error("Upload error:", err);
      const msg = err.response && err.response.data && err.response.data.error
        ? err.response.data.error
        : err.message || "Upload failed";
      setStatus(`Upload failed: ${msg}`, true);
      uploadBtn.textContent = "Upload File";
      uploadBtn.disabled = false;
    }
  });

  // Optional: expose the uploaded URL globally for quick dev access
  window.getUploadedCsvUrl = () => uploadedCsvUrl;
})


// ---- Replace existing second DOMContentLoaded block with this ----
document.addEventListener("DOMContentLoaded", () => {
  const dbInput = document.getElementById("dbInput");
  const connectDbBtn = document.getElementById("connectDbBtn");
  const dbStatus = document.getElementById("dbStatus");

  // Try to load saved DB meta (fallback to legacy plain key)
  let savedDbConn = (() => {
    const raw = localStorage.getItem("savedDbConnMeta");
    if (raw) {
      try { return JSON.parse(raw).value || null; } catch { /* fallthrough */ }
    }
    return localStorage.getItem("savedDbConn") || null;
  })();

  // Prefill input if a saved connection exists (do NOT show status automatically)
  if (savedDbConn && dbInput) dbInput.value = savedDbConn;

  function showDbStatus(text, isError = false) {
    if (!dbStatus) return;
    dbStatus.textContent = text;
    dbStatus.style.color = isError ? "#b91c1c" : "#374151";
  }

  function validateConnString(s) {
    if (!s || !s.trim()) return { ok: false, msg: "Connection string can't be empty." };
    if (s.length < 8) return { ok: false, msg: "Connection string too short to be valid." };
    if (!(/[/:@]/.test(s))) return { ok: false, msg: "Connection string looks suspicious. Check format." };
    return { ok: true };
  }

  if (connectDbBtn) {
    connectDbBtn.addEventListener("click", () => {
      const value = dbInput ? dbInput.value.trim() : "";
      const v = validateConnString(value);
      if (!v.ok) {
        showDbStatus(v.msg, true);
        return;
      }

      // Save in-memory
      savedDbConn = value;

      // Persist locally (meta form) and redirect same as CSV flow
      try {
        localStorage.setItem("savedDbConnMeta", JSON.stringify({ value, savedAt: Date.now() }));
        // optional legacy key keep: localStorage.setItem("savedDbConn", value);

        showDbStatus("Connection string saved for future use.");
        // mark intentional navigation
        sessionStorage.setItem("fromConnect", "1");
        // small delay to let user see status (matches CSV behavior)
        setTimeout(() => { window.location.href = "chat.html"; }, 500);

      } catch (err) {
        console.warn("Failed to save DB conn to localStorage:", err);
        showDbStatus("Saved in memory but could not persist to localStorage.", true);
      }
    });
  }

  // helpers
  window.clearSavedDbConn = function() {
    savedDbConn = null;
    try {
      localStorage.removeItem("savedDbConnMeta");
      localStorage.removeItem("savedDbConn");
    } catch (_) {}
    if (dbInput) dbInput.value = "";
    showDbStatus("Saved connection string cleared.");
  };

  window.getSavedDbConn = function() {
    return savedDbConn;
  };
});
// ---- end replacement block ----



