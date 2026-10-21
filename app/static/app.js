/**
 * ATELIER // Hyper-Personalized Retail Shopping Concierge Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // App State
  const state = {
    activeTab: "concierge",
    activeCustomerId: "CUST-101", // Default to Aarav Sharma for rich demo experience
    activeIntent: {},
    manualSize: null,
    manualBudget: null,
    latestEstimatedSize: null,
    selectedPhotoFile: null
  };

  // Elements
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatMessages = document.getElementById("chat-messages");
  const promptChips = document.querySelectorAll(".chip-btn");
  const recommendationsGrid = document.getElementById("recommendations-grid");
  const guardrailCounterBadge = document.getElementById("guardrail-counter-badge");
  const guardText = document.getElementById("guard-text");
  const guardAlert = document.getElementById("guardrail-alert");
  const guardNotesList = document.getElementById("guardrail-notes-list");
  const alertItemsCount = document.getElementById("alert-items-count");
  const activeIntentBar = document.getElementById("active-intent-bar");
  const intentTagsContainer = document.getElementById("intent-tags-container");
  const btnClearIntent = document.getElementById("btn-clear-intent");
  const activeCustomerIndicator = document.getElementById("active-customer-indicator");

  // Health Pills
  const ollamaPill = document.getElementById("ollama-pill");
  const chromaPill = document.getElementById("chroma-pill");
  const sqlitePill = document.getElementById("sqlite-pill");

  // Size Assistant Elements
  const consentCheckbox = document.getElementById("consent-checkbox");
  const photoDropZone = document.getElementById("photo-drop-zone");
  const photoFileInput = document.getElementById("photo-file-input");
  const dropZonePrompt = document.getElementById("drop-zone-prompt");
  const previewContainer = document.getElementById("preview-container");
  const imagePreview = document.getElementById("image-preview");
  const landmarkCanvas = document.getElementById("landmark-canvas");
  const btnRemovePhoto = document.getElementById("btn-remove-photo");
  const btnAnalyzeSize = document.getElementById("btn-analyze-size");
  const inputHeight = document.getElementById("input-height");
  const selectBrand = document.getElementById("select-brand");
  const selectCategory = document.getElementById("select-category");
  const selectGender = document.getElementById("select-gender");
  const sizeResultsEmpty = document.getElementById("size-results-empty");
  const sizeResultsContent = document.getElementById("size-results-content");
  const resRecommendedSize = document.getElementById("res-recommended-size");
  const resAltSizes = document.getElementById("res-alt-sizes");
  const resConfidenceBadge = document.getElementById("res-confidence-badge");
  const resCalibrationMethod = document.getElementById("res-calibration-method");
  const resChestCm = document.getElementById("res-chest-cm");
  const resWaistCm = document.getElementById("res-waist-cm");
  const resHipCm = document.getElementById("res-hip-cm");
  const chartTableBrandLabel = document.getElementById("chart-table-brand-label");
  const brandChartTbody = document.getElementById("brand-chart-tbody");
  const sizeNotesList = document.getElementById("size-notes-list");
  const sizeDisclaimerText = document.getElementById("size-disclaimer-text");
  const btnApplySizeToChat = document.getElementById("btn-apply-size-to-chat");

  // Catalog Elements
  const catalogGrid = document.getElementById("catalog-grid");
  const catalogCategoryFilter = document.getElementById("catalog-category-filter");
  const catalogFitFilter = document.getElementById("catalog-fit-filter");
  const btnRefreshCatalog = document.getElementById("btn-refresh-catalog");

  // Profile Elements
  const customerSelect = document.getElementById("customer-select");
  const preferencesForm = document.getElementById("preferences-form");
  const prefSize = document.getElementById("pref-size");
  const prefFit = document.getElementById("pref-fit");
  const prefBudget = document.getElementById("pref-budget");
  const prefColors = document.getElementById("pref-colors");
  const prefMaterials = document.getElementById("pref-materials");
  const prefNotes = document.getElementById("pref-notes");
  const purchasesList = document.getElementById("purchases-list");

  // Loading Overlay
  const loadingOverlay = document.getElementById("loading-overlay");
  const loadingText = document.getElementById("loading-text");

  function showLoading(msg = "Analyzing with local AI...") {
    loadingText.innerText = msg;
    loadingOverlay.style.display = "flex";
  }

  function hideLoading() {
    loadingOverlay.style.display = "none";
  }

  // --- 1. Tab Navigation ---
  navTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");
      switchTab(target);
    });
  });

  function switchTab(tabId) {
    state.activeTab = tabId;
    navTabs.forEach(t => {
      if (t.getAttribute("data-tab") === tabId) t.classList.add("active");
      else t.classList.remove("active");
    });
    tabPanes.forEach(p => {
      if (p.id === `pane-${tabId}`) p.classList.add("active");
      else p.classList.remove("active");
    });

    if (tabId === "catalog") {
      loadCatalog();
    } else if (tabId === "profile") {
      loadCustomerProfile(state.activeCustomerId);
    }
  }

  // --- 2. System Health Check ---
  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        // Ollama
        const ollamaDot = ollamaPill.querySelector(".pill-dot");
        if (data.ollama_connected) {
          ollamaDot.className = "pill-dot success";
          ollamaPill.title = `Ollama: Online (${data.ollama_model})`;
        } else {
          ollamaDot.className = "pill-dot warning";
          ollamaPill.title = "Ollama: Offline (NLP fallback active)";
        }

        // ChromaDB
        const chromaDot = chromaPill.querySelector(".pill-dot");
        if (data.vector_db_connected) {
          chromaDot.className = "pill-dot success";
          chromaPill.title = `ChromaDB: Connected (${data.vector_db_items_count} embeddings)`;
        } else {
          chromaDot.className = "pill-dot warning";
          chromaPill.title = "ChromaDB: Initializing / Fallback search";
        }

        // SQLite
        const sqliteDot = sqlitePill.querySelector(".pill-dot");
        if (data.sqlite_connected) {
          sqliteDot.className = "pill-dot success";
          sqlitePill.title = `SQLite: Live (${data.total_products_count} catalog items)`;
        }
      }
    } catch (e) {
      console.warn("Health check error:", e);
    }
  }

  // --- 3. Chat & Recommendations Workflow ---
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (query) {
      sendChatMessage(query);
      chatInput.value = "";
    }
  });

  promptChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      if (q) {
        sendChatMessage(q);
      }
    });
  });

  async function sendChatMessage(message) {
    appendUserMessage(message);

    // Append loading bubble
    const loadingBubble = appendBotLoading();

    try {
      const payload = {
        message: message,
        customer_id: state.activeCustomerId || null,
        manual_size: state.manualSize || null,
        manual_budget: state.manualBudget || null
      };

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Chat API returned status ${res.status}`);
      }

      const data = await res.json();
      loadingBubble.remove();

      appendBotMessage(data.reply);
      updateIntentBar(data.extracted_intent);
      renderRecommendations(data.recommendations, data.guardrail_summary);
    } catch (err) {
      loadingBubble.remove();
      appendBotMessage(`⚠️ Notice: I experienced an issue while processing your request (${err.message}). Showing general in-stock selections below.`);
      console.error(err);
    }
  }

  function appendUserMessage(text) {
    const wrap = document.createElement("div");
    wrap.className = "message-bubble user-message";
    wrap.innerHTML = `<div class="message-body">${escapeHtml(text)}</div>`;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendBotMessage(text) {
    const wrap = document.createElement("div");
    wrap.className = "message-bubble bot-message";
    // Simple markdown formatting: bold **text**, bullet points
    let formatted = escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n- (.*?)/g, '<br>&bull; $1')
      .replace(/\n/g, '<br>');

    wrap.innerHTML = `
      <div class="bot-avatar">◈</div>
      <div class="message-body">${formatted}</div>
    `;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendBotLoading() {
    const wrap = document.createElement("div");
    wrap.className = "message-bubble bot-message";
    wrap.innerHTML = `
      <div class="bot-avatar">◈</div>
      <div class="message-body">
        <em>Stylist is consulting ChromaDB vector index & verifying SQLite inventory...</em>
      </div>
    `;
    chatMessages.appendChild(wrap);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return wrap;
  }

  function updateIntentBar(intent) {
    if (!intent) return;
    state.activeIntent = intent;
    intentTagsContainer.innerHTML = "";
    let hasTags = false;

    if (intent.occasion) {
      addIntentTag(`Occasion: ${intent.occasion}`);
      hasTags = true;
    }
    if (intent.budget) {
      addIntentTag(`Max Budget: ₹${Number(intent.budget).toLocaleString()}`);
      hasTags = true;
    }
    if (intent.fit_preference) {
      addIntentTag(`Fit: ${intent.fit_preference}`);
      hasTags = true;
    }
    if (intent.color) {
      addIntentTag(`Color: ${intent.color}`);
      hasTags = true;
    }
    if (intent.material) {
      addIntentTag(`Fabric: ${intent.material}`);
      hasTags = true;
    }
    if (intent.size) {
      addIntentTag(`Size: ${intent.size}`);
      hasTags = true;
    }

    activeIntentBar.style.display = hasTags ? "flex" : "none";
  }

  function addIntentTag(text) {
    const span = document.createElement("span");
    span.className = "intent-tag";
    span.innerText = text;
    intentTagsContainer.appendChild(span);
  }

  btnClearIntent.addEventListener("click", () => {
    state.activeIntent = {};
    state.manualSize = null;
    state.manualBudget = null;
    activeIntentBar.style.display = "none";
    sendChatMessage("Reset filters and show popular in-stock outfits.");
  });

  function renderRecommendations(products, guardrailSummary) {
    // Update guardrail alert
    if (guardrailSummary) {
      const { candidate_count, approved_count, rejected_count, rejected_details } = guardrailSummary;
      guardText.innerText = `${approved_count} Verified In-Stock`;

      if (rejected_count > 0) {
        guardAlert.style.display = "block";
        alertItemsCount.innerText = `${rejected_count} candidate(s) filtered out`;
        guardNotesList.innerHTML = rejected_details.map(d =>
          `<li><strong>${escapeHtml(d.name)}</strong>: ${escapeHtml(d.reason)}</li>`
        ).join("");
      } else {
        guardAlert.style.display = "none";
      }
    }

    if (!products || products.length === 0) {
      recommendationsGrid.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-icon">🔍</div>
          <h3>No Exact Matches Found</h3>
          <p>All items matching this exact combination are currently out of stock or exceed the budget ceiling.</p>
        </div>
      `;
      return;
    }

    recommendationsGrid.innerHTML = products.map(prod => `
      <div class="product-card">
        <div class="product-image-wrap">
          <img src="${prod.image_url}" alt="${escapeHtml(prod.name)}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500&auto=format&fit=crop&q=80'">
          <div class="match-score-badge">
            <span class="score-star">★</span> ${(prod.relevance_score * 100).toFixed(0)}% Match
          </div>
          <div class="guardrail-verified-tag">✓ SQLite Stock Verified</div>
        </div>
        <div class="product-info">
          <span class="product-brand">${escapeHtml(prod.brand)}</span>
          <h4 class="product-title">${escapeHtml(prod.name)}</h4>
          <div class="product-price-row">
            <span class="product-price">₹${Number(prod.price).toLocaleString()}</span>
          </div>

          <div class="attribute-tags">
            <span class="attr-tag">${escapeHtml(prod.material)}</span>
            <span class="attr-tag">${escapeHtml(prod.fit_type)} Fit</span>
            <span class="attr-tag">${escapeHtml(prod.occasion)}</span>
          </div>

          <div class="stock-sizes-row">
            <span class="sizes-label">Available Sizes:</span>
            ${prod.available_sizes.map(s => `<span class="size-pill ${state.manualSize === s ? 'active' : ''}">${s}</span>`).join("")}
          </div>

          <div class="rationale-box">
            <div class="rationale-title">Why it matches:</div>
            <ul class="rationale-list">
              ${prod.match_reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("")}
            </ul>
          </div>
        </div>
      </div>
    `).join("");
  }

  // --- 4. Photo-Based Size Assistant Workflow ---
  consentCheckbox.addEventListener("change", () => {
    btnAnalyzeSize.disabled = !consentCheckbox.checked || !state.selectedPhotoFile;
  });

  photoDropZone.addEventListener("click", () => {
    if (!state.selectedPhotoFile) {
      photoFileInput.click();
    }
  });

  photoDropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    photoDropZone.style.borderColor = "var(--accent-gold)";
  });

  photoDropZone.addEventListener("dragleave", () => {
    photoDropZone.style.borderColor = "var(--border-light)";
  });

  photoDropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    photoDropZone.style.borderColor = "var(--border-light)";
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  photoFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  btnRemovePhoto.addEventListener("click", (e) => {
    e.stopPropagation();
    state.selectedPhotoFile = null;
    photoFileInput.value = "";
    previewContainer.style.display = "none";
    dropZonePrompt.style.display = "block";
    btnAnalyzeSize.disabled = true;
    const ctx = landmarkCanvas.getContext("2d");
    ctx.clearRect(0, 0, landmarkCanvas.width, landmarkCanvas.height);
  });

  function handleFileSelected(file) {
    if (!file.type.match(/^image\/(jpeg|png|webp)$/)) {
      alert("Please upload a valid JPEG, PNG, or WebP image.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert("File exceeds maximum size limit of 5MB.");
      return;
    }

    state.selectedPhotoFile = file;
    const reader = new FileReader();
    reader.onload = (evt) => {
      imagePreview.src = evt.target.result;
      dropZonePrompt.style.display = "none";
      previewContainer.style.display = "flex";
      btnAnalyzeSize.disabled = !consentCheckbox.checked;
    };
    reader.readAsDataURL(file);
  }

  btnAnalyzeSize.addEventListener("click", async () => {
    if (!consentCheckbox.checked) {
      alert("Explicit consent is required to process photographs.");
      return;
    }
    if (!state.selectedPhotoFile) {
      alert("Please select a photo first.");
      return;
    }

    showLoading("Extracting MediaPipe body landmarks & calibrating size chart...");

    const formData = new FormData();
    formData.append("consent", "true");
    formData.append("file", state.selectedPhotoFile);
    if (inputHeight.value) {
      formData.append("height_cm", inputHeight.value);
    }
    formData.append("brand", selectBrand.value);
    formData.append("category", selectCategory.value);
    formData.append("gender", selectGender.value);

    try {
      const res = await fetch("/api/size-assistant/analyze", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with status ${res.status}`);
      }

      const data = await res.json();
      hideLoading();
      displaySizeResults(data);
    } catch (err) {
      hideLoading();
      alert(`Size Assistant error: ${err.message}`);
      console.error(err);
    }
  });

  function displaySizeResults(data) {
    sizeResultsEmpty.style.display = "none";
    sizeResultsContent.style.display = "block";

    state.latestEstimatedSize = data.recommended_size;

    resRecommendedSize.innerText = data.recommended_size;
    resAltSizes.innerText = `Alternative Options: ${data.alternative_sizes.join(", ")}`;

    resConfidenceBadge.innerText = `${data.confidence_level.toUpperCase()} (${(data.confidence_score * 100).toFixed(0)}%)`;
    resConfidenceBadge.className = `confidence-badge ${data.confidence_level === 'high' ? 'success' : ''}`;
    resCalibrationMethod.innerText = data.calibration_method;

    const meas = data.estimated_measurements_cm || {};
    resChestCm.innerText = meas.chest_cm ? `${meas.chest_cm} cm` : "--";
    resWaistCm.innerText = meas.waist_cm ? `${meas.waist_cm} cm` : "--";
    resHipCm.innerText = meas.hip_cm ? `${meas.hip_cm} cm` : "--";

    chartTableBrandLabel.innerText = `${data.brand_used} (${data.category_used}) Size Chart`;

    // Populate Size Chart Table
    brandChartTbody.innerHTML = (data.brand_size_chart || []).map(row => {
      const isMatch = row.size_label === data.recommended_size;
      return `
        <tr class="${isMatch ? 'highlighted-size' : ''}">
          <td><strong>${row.size_label} ${isMatch ? '★' : ''}</strong></td>
          <td>${row.chest_min_cm}-${row.chest_max_cm} cm</td>
          <td>${row.waist_min_cm}-${row.waist_max_cm} cm</td>
          <td>${row.garment_chest_cm || row.garment_waist_cm} cm</td>
          <td>${row.fit_type}</td>
        </tr>
      `;
    }).join("");

    // Notes
    sizeNotesList.innerHTML = (data.notes || []).map(n => `<li>${escapeHtml(n)}</li>`).join("");
    sizeDisclaimerText.innerText = data.disclaimer || "";
  }

  btnApplySizeToChat.addEventListener("click", () => {
    if (state.latestEstimatedSize) {
      state.manualSize = state.latestEstimatedSize;
      switchTab("concierge");
      sendChatMessage(`I've calibrated my tentative size to ${state.latestEstimatedSize}. Please show matching outfits.`);
    }
  });

  document.querySelectorAll(".manual-size-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const sz = btn.getAttribute("data-size");
      state.manualSize = sz;
      switchTab("concierge");
      sendChatMessage(`I prefer size ${sz}. What outfits do you have available?`);
    });
  });

  // --- 5. Catalog Tab ---
  async function loadCatalog() {
    try {
      const cat = catalogCategoryFilter.value;
      const fit = catalogFitFilter.value;
      let url = "/api/products?in_stock_only=false";
      if (cat) url += `&category=${encodeURIComponent(cat)}`;
      if (fit) url += `&fit_type=${encodeURIComponent(fit)}`;

      const res = await fetch(url);
      if (res.ok) {
        const items = await res.json();
        renderCatalog(items);
      }
    } catch (e) {
      console.error("Error loading catalog:", e);
    }
  }

  function renderCatalog(items) {
    if (!items || items.length === 0) {
      catalogGrid.innerHTML = `
        <div class="empty-state-card">
          <p>No products found matching these filters.</p>
        </div>
      `;
      return;
    }

    catalogGrid.innerHTML = items.map(p => `
      <div class="product-card">
        <div class="product-image-wrap">
          <img src="${p.image_url}" alt="${escapeHtml(p.name)}" loading="lazy">
          <div class="guardrail-verified-tag ${p.in_stock ? '' : 'out-of-stock'}">
            ${p.in_stock ? '● In Stock' : '✕ Out of Stock'}
          </div>
        </div>
        <div class="product-info">
          <span class="product-brand">${escapeHtml(p.brand)}</span>
          <h4 class="product-title">${escapeHtml(p.name)}</h4>
          <div class="product-price-row">
            <span class="product-price">₹${Number(p.base_price).toLocaleString()}</span>
          </div>
          <div class="attribute-tags">
            <span class="attr-tag">${escapeHtml(p.material)}</span>
            <span class="attr-tag">${escapeHtml(p.fit_type)}</span>
            <span class="attr-tag">${escapeHtml(p.occasion)}</span>
          </div>
          <div class="stock-sizes-row">
            <span class="sizes-label">Sizes:</span>
            ${p.available_sizes.length > 0 ? p.available_sizes.map(s => `<span class="size-pill">${s}</span>`).join("") : '<span class="label-hint">Sold out</span>'}
          </div>
        </div>
      </div>
    `).join("");
  }

  catalogCategoryFilter.addEventListener("change", loadCatalog);
  catalogFitFilter.addEventListener("change", loadCatalog);
  btnRefreshCatalog.addEventListener("click", loadCatalog);

  // --- 6. Customer Profile Tab ---
  customerSelect.addEventListener("change", () => {
    state.activeCustomerId = customerSelect.value;
    updateActiveCustomerBadge();
    loadCustomerProfile(state.activeCustomerId);
  });

  function updateActiveCustomerBadge() {
    const selectedOption = customerSelect.options[customerSelect.selectedIndex];
    if (customerSelect.value) {
      const name = selectedOption.text.split("(")[0].trim();
      activeCustomerIndicator.innerText = `👤 ${name}`;
    } else {
      activeCustomerIndicator.innerText = `👤 Guest Shopper`;
    }
  }

  async function loadCustomerProfile(cid) {
    if (!cid) {
      // Clear form
      prefSize.value = "";
      prefFit.value = "";
      prefBudget.value = "";
      prefColors.value = "";
      prefMaterials.value = "";
      prefNotes.value = "";
      purchasesList.innerHTML = `<div class="empty-state-card"><p>Guest Shopper profile has no saved history.</p></div>`;
      return;
    }

    try {
      const res = await fetch(`/api/customers/${cid}`);
      if (res.ok) {
        const data = await res.json();
        const p = data.preferences || {};
        prefSize.value = p.preferred_size || "";
        prefFit.value = p.preferred_fit || "";
        prefBudget.value = p.budget_max || "";
        prefColors.value = p.preferred_colors || "";
        prefMaterials.value = p.preferred_materials || "";
        prefNotes.value = p.explicit_style_notes || "";

        // Purchases
        if (data.recent_purchases && data.recent_purchases.length > 0) {
          purchasesList.innerHTML = data.recent_purchases.map(pur => `
            <div class="purchase-item">
              <div>
                <span class="purchase-brand">${escapeHtml(pur.brand)} &bull; ${escapeHtml(pur.category)}</span>
                <div class="purchase-title">${escapeHtml(pur.product_name)}</div>
                <span class="label-hint">Size: ${pur.size} | Color: ${pur.color}</span>
              </div>
              <div>
                <strong>₹${Number(pur.price_paid).toLocaleString()}</strong>
              </div>
            </div>
          `).join("");
        } else {
          purchasesList.innerHTML = `<div class="empty-state-card"><p>No previous orders recorded.</p></div>`;
        }
      }
    } catch (e) {
      console.error("Error loading profile:", e);
    }
  }

  preferencesForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.activeCustomerId) {
      alert("Please select a customer profile to save preferences.");
      return;
    }

    const payload = {
      preferred_size: prefSize.value || null,
      preferred_fit: prefFit.value || null,
      budget_max: prefBudget.value ? parseFloat(prefBudget.value) : null,
      preferred_colors: prefColors.value || null,
      preferred_materials: prefMaterials.value || null,
      explicit_style_notes: prefNotes.value || null
    };

    try {
      const res = await fetch(`/api/customers/${state.activeCustomerId}/preferences`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        alert("Customer preferences saved! These will now influence AI styling and ranking.");
      }
    } catch (err) {
      alert("Failed to update preferences: " + err.message);
    }
  });

  // Utility
  function escapeHtml(text) {
    if (!text) return "";
    return text.toString()
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Initial Boot
  checkHealth();
  updateActiveCustomerBadge();
  loadCustomerProfile(state.activeCustomerId);
});
