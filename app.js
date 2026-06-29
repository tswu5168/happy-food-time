/**
 * METAFOOD TAIWAN: Interactive & Futuristic Application Logic (Sanitized & Compliant)
 */

document.addEventListener("DOMContentLoaded", () => {
    // ---------------------------------------------------------
    // 1. Core State Management
    // ---------------------------------------------------------
    let activeTheme = "food";
    let filteredStores = [];
    let currentPage = 1;
    const itemsPerPage = 24;
    let activeTag = null;
    let STORES_DATA = window.STORES_DATA || [];

    // DOM Elements Cache
    const preloader = document.getElementById("preloader");
    const loaderProgress = document.getElementById("loader-progress");
    const loaderStatus = document.getElementById("loader-status");
    const viewCounterEl = document.getElementById("view-counter");
    const storeGrid = document.getElementById("store-grid");
    const loadMoreContainer = document.getElementById("load-more-container");
    const loadMoreBtn = document.getElementById("load-more-btn");
    const matchCountEl = document.getElementById("match-count");
    const statusModeEl = document.getElementById("status-mode");

    // Filter Controls
    const searchInput = document.getElementById("search-input");
    const clearSearchBtn = document.getElementById("clear-search");
    const regionSelect = document.getElementById("region-select");
    const cuisineSelect = document.getElementById("cuisine-select");
    const sortSelect = document.getElementById("sort-select");
    const tagsContainer = document.getElementById("tags-container");

    // ---------------------------------------------------------
    // 2. Cumulative View Counter (localStorage-based)
    // ---------------------------------------------------------
    function updateViewCounter() {
        let views = localStorage.getItem("metafood_views");
        if (!views) {
            // Seed visitors count to look dynamic
            views = Math.floor(Math.random() * 10500) + 24800;
        } else {
            views = parseInt(views) + 1;
        }
        localStorage.setItem("metafood_views", views);
        if (viewCounterEl) {
            viewCounterEl.textContent = String(views).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
    }
    updateViewCounter();

    // ---------------------------------------------------------
    // 3. Cyberpunk Floating Particles Generator
    // ---------------------------------------------------------
    function createParticles() {
        const container = document.getElementById("particles");
        const count = 35;
        for (let i = 0; i < count; i++) {
            const particle = document.createElement("div");
            particle.classList.add("particle");
            
            // Random styling
            const size = Math.random() * 3 + 1;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${Math.random() * 100}vw`;
            
            // Animation variables
            particle.style.setProperty("--duration", `${Math.random() * 15 + 10}s`);
            particle.style.setProperty("--drift", `${(Math.random() - 0.5) * 200}px`);
            particle.style.animationDelay = `${Math.random() * 10}s`;
            
            container.appendChild(particle);
        }
    }
    createParticles();

    // ---------------------------------------------------------
    // 4. Preloader Progress Bar Simulation
    // ---------------------------------------------------------
    function loadDataAndSimulate() {
        let progress = 0;
        let dataLoaded = false;
        
        const steps = [
            { limit: 25, status: "CONNECTING TO DATA NODE..." },
            { limit: 60, status: "PARSING GEOGRAPHIC DATA..." },
            { limit: 85, status: "ESTABLISHING DIGITAL PORTAL..." },
            { limit: 100, status: "HappyFoodTime PORTAL ONLINE." }
        ];

        let currentStepIndex = 0;
        
        const supabaseUrl = window.SUPABASE_URL;
        const supabaseAnonKey = window.SUPABASE_ANON_KEY;
        
        const isSupabaseConfigured = supabaseUrl && 
                                     supabaseAnonKey && 
                                     !supabaseUrl.includes("your-project-id") && 
                                     !supabaseAnonKey.includes("your-anon-public-key");
                                     
        if (isSupabaseConfigured) {
            console.log("Supabase config detected. Loading cloud data...");
            fetch(`${supabaseUrl.replace(/\/+$/, '')}/rest/v1/stores?select=*`, {
                headers: {
                    "apikey": supabaseAnonKey,
                    "Authorization": `Bearer ${supabaseAnonKey}`
                }
            })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                return res.json();
            })
            .then(data => {
                if (Array.isArray(data) && data.length > 0) {
                    STORES_DATA = data;
                    console.log(`Loaded ${data.length} stores from Supabase.`);
                }
                dataLoaded = true;
            })
            .catch(err => {
                console.error("Failed to load data from Supabase. Falling back to local backup:", err);
                dataLoaded = true; 
            });
        } else {
            console.log("Supabase config not set. Using local backup database.");
            dataLoaded = true;
        }

        const interval = setInterval(() => {
            const maxProgress = dataLoaded ? 100 : 90;
            
            if (progress < maxProgress) {
                progress += Math.floor(Math.random() * 12) + 5;
                if (progress > maxProgress) progress = maxProgress;
            }
            
            if (progress >= 100) {
                loaderProgress.style.width = "100%";
                loaderStatus.textContent = steps[steps.length - 1].status;
                clearInterval(interval);
                
                // Initialize filteredStores and render once STORES_DATA is loaded
                filteredStores = [...STORES_DATA];
                applySort();
                initFilters();
                renderStores(false);
                
                setTimeout(() => {
                    preloader.classList.add("fade-out");
                    animateCounters();
                }, 500);
            } else {
                loaderProgress.style.width = `${progress}%`;
                if (progress >= steps[currentStepIndex].limit && currentStepIndex < steps.length - 1) {
                    currentStepIndex++;
                }
                loaderStatus.textContent = steps[currentStepIndex].status;
            }
        }, 80);
    }
    loadDataAndSimulate();

    function animateCounters() {
        const themeStores = STORES_DATA.filter(s => (s.theme || "food") === activeTheme);
        const totalStores = themeStores.length;
        const regions = new Set();
        const cuisines = new Set();
        
        themeStores.forEach(s => {
            if (s.region && s.region !== "未知") regions.add(s.region);
            if (s.cuisine) cuisines.add(s.cuisine);
        });
        
        const totalEl = document.getElementById("stat-total");
        const regionsEl = document.getElementById("stat-regions");
        const cuisinesEl = document.getElementById("stat-cuisines");
        
        if (totalEl) totalEl.setAttribute("data-target", totalStores);
        if (regionsEl) regionsEl.setAttribute("data-target", regions.size || 0);
        if (cuisinesEl) cuisinesEl.setAttribute("data-target", cuisines.size || 0);

        const counters = [
            { id: "stat-total", target: totalStores },
            { id: "stat-regions", target: regions.size || 0 },
            { id: "stat-cuisines", target: cuisines.size || 0 }
        ];

        counters.forEach(counter => {
            const el = document.getElementById(counter.id);
            if (!el) return;
            
            let current = 0;
            const target = counter.target;
            const duration = 800; // ms
            const stepTime = Math.max(Math.floor(duration / (target || 1)), 10);
            
            if (el.dataset.intervalId) {
                clearInterval(parseInt(el.dataset.intervalId));
            }
            
            const timer = setInterval(() => {
                if (target === 0) {
                    el.textContent = 0;
                    clearInterval(timer);
                    return;
                }
                current += Math.ceil(target / 20);
                if (current >= target) {
                    el.textContent = target;
                    clearInterval(timer);
                } else {
                    el.textContent = current;
                }
            }, stepTime);
            
            el.dataset.intervalId = timer;
        });
    }

    // ---------------------------------------------------------
    // 6. Dynamic Filter Selects Population
    // ---------------------------------------------------------
    function initFilters() {
        const themeStores = STORES_DATA.filter(store => (store.theme || "food") === activeTheme);
        const regions = new Set();
        const cuisines = new Set();
        const regionCounts = {};

        themeStores.forEach(store => {
            if (store.region && store.region !== "未知") {
                regions.add(store.region);
                regionCounts[store.region] = (regionCounts[store.region] || 0) + 1;
            }
            if (store.cuisine && store.cuisine !== "未知") {
                cuisines.add(store.cuisine);
            }
        });

        // Populate regions
        regionSelect.innerHTML = '<option value="">ALL REGIONS // 全部縣市</option>';
        const sortedRegions = Array.from(regions).sort();
        sortedRegions.forEach(reg => {
            const opt = document.createElement("option");
            opt.value = reg;
            opt.textContent = reg;
            regionSelect.appendChild(opt);
        });

        // Populate cuisines
        cuisineSelect.innerHTML = '<option value="">ALL CUISINES // 全部類別</option>';
        const sortedCuisines = Array.from(cuisines).sort();
        sortedCuisines.forEach(cui => {
            const opt = document.createElement("option");
            opt.value = cui;
            opt.textContent = cui;
            cuisineSelect.appendChild(opt);
        });

        // Dynamic popular regions tags (Top 10)
        tagsContainer.innerHTML = '';
        const popularRegions = Object.entries(regionCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(entry => entry[0]);

        popularRegions.forEach(reg => {
            const btn = document.createElement("button");
            btn.className = "tag-btn";
            btn.dataset.search = reg;
            btn.textContent = reg;
            if (activeTag === reg) {
                btn.classList.add("active");
            }
            tagsContainer.appendChild(btn);
        });
    }
    initFilters();

    // ---------------------------------------------------------
    // 7. Store Cards Rendering
    // ---------------------------------------------------------
    function createStoreCardHTML(store) {
        // Query param for Google search
        const searchQuery = encodeURIComponent(store.name);
        
        // Query param for Google Maps navigation (Fallback to address search)
        let mapQuery = "";
        if (store.lat && store.lon) {
            mapQuery = `${store.lat},${store.lon}`;
        } else {
            const hasRealAddress = store.address && !store.address.includes("地址請至");
            mapQuery = hasRealAddress 
                ? encodeURIComponent(`${store.name} ${store.address}`)
                : encodeURIComponent(store.name);
        }
        const mapUrl = `https://www.google.com/maps/search/?api=1&query=${mapQuery}`;

        return `
            <div class="store-card">
                <div class="card-header">
                    <div>
                        <span class="region-badge">${store.region}</span>
                        <span class="cuisine-badge">${store.cuisine}</span>
                    </div>
                </div>
                <div class="card-body">
                    <h3 class="store-name">${store.name}</h3>
                    
                    <div class="detail-row">
                        <span class="detail-label">店家地址:</span>
                        <span class="detail-value">${store.address}</span>
                    </div>
                    
                    ${store.time ? `
                    <div class="detail-row">
                        <span class="detail-label">營業時間:</span>
                        <span class="detail-value">${store.time}</span>
                    </div>` : ''}
                </div>
                <div class="card-actions">
                    <a href="${mapUrl}" target="_blank" rel="noopener noreferrer" class="action-btn btn-map">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg>
                        導航地圖
                    </a>
                    <a href="https://www.google.com/search?q=${searchQuery}" target="_blank" rel="noopener noreferrer" class="action-btn btn-search">
                        <svg viewBox="0 0 24 24"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                        搜尋此店
                    </a>
                </div>
            </div>
        `;
    }

    function renderStores(append = false) {
        if (!append) {
            storeGrid.innerHTML = "";
            currentPage = 1;
        }

        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const pageItems = filteredStores.slice(start, end);

        if (pageItems.length === 0 && !append) {
            storeGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #718096; font-family: var(--font-mono); border: 1px dashed var(--border-dim); border-radius: 8px;">
                    NO MATCHING ITEMS FOUND // 未找到匹配項目
                </div>
            `;
            loadMoreContainer.style.display = "none";
            return;
        }

        const fragment = document.createDocumentFragment();
        pageItems.forEach(store => {
            const container = document.createElement("div");
            container.innerHTML = createStoreCardHTML(store);
            fragment.appendChild(container.firstElementChild);
        });

        storeGrid.appendChild(fragment);

        // Manage Load More visibility
        if (end >= filteredStores.length) {
            loadMoreContainer.style.display = "none";
        } else {
            loadMoreContainer.style.display = "flex";
        }

        matchCountEl.textContent = filteredStores.length;

        // Update dynamic theme total
        const themeStores = STORES_DATA.filter(s => (s.theme || "food") === activeTheme);
        const totalThemeCountEl = document.getElementById("total-theme-count");
        if (totalThemeCountEl) {
            totalThemeCountEl.textContent = themeStores.length;
        }
    }

    // ---------------------------------------------------------
    // 8. Search & Filtering Core Logic
    // ---------------------------------------------------------
    function applyFilters() {
        const query = searchInput.value.trim().toLowerCase();
        const selectedRegion = regionSelect.value;
        const selectedCuisine = cuisineSelect.value;

        // Show/hide clear button
        clearSearchBtn.style.display = query ? "block" : "none";

        // Update status text
        if (query || selectedRegion || selectedCuisine) {
            statusModeEl.textContent = "FILTERED";
            statusModeEl.classList.add("accent-text");
        } else {
            statusModeEl.textContent = "READY";
            statusModeEl.classList.remove("accent-text");
        }

        filteredStores = STORES_DATA.filter(store => {
            // Theme matching
            const t = store.theme || "food";
            if (t !== activeTheme) return false;

            // Text Search matching
            let textMatch = true;
            if (query) {
                textMatch = 
                    store.name.toLowerCase().includes(query) ||
                    store.address.toLowerCase().includes(query) ||
                    store.cuisine.toLowerCase().includes(query) ||
                    store.region.toLowerCase().includes(query);
            }

            // Select Dropdown matching
            const regionMatch = !selectedRegion || store.region === selectedRegion;
            const cuisineMatch = !selectedCuisine || store.cuisine === selectedCuisine;

            return textMatch && regionMatch && cuisineMatch;
        });

        // Apply Sorting
        applySort();
        // Render
        renderStores(false);
    }

    function applySort() {
        const sortVal = sortSelect.value;
        if (sortVal === "region-asc") {
            filteredStores.sort((a, b) => a.region.localeCompare(b.region, "zh-Hant"));
        } else if (sortVal === "name-asc") {
            filteredStores.sort((a, b) => a.name.localeCompare(b.name, "zh-Hant"));
        }
    }

    // ---------------------------------------------------------
    // 9. Event Listeners
    // ---------------------------------------------------------

    // Search Input Events
    searchInput.addEventListener("input", applyFilters);
    clearSearchBtn.addEventListener("click", () => {
        searchInput.value = "";
        applyFilters();
        // Clear active tags
        document.querySelectorAll(".tag-btn").forEach(btn => btn.classList.remove("active"));
        activeTag = null;
    });

    // Selects Events
    regionSelect.addEventListener("change", applyFilters);
    cuisineSelect.addEventListener("change", applyFilters);
    sortSelect.addEventListener("change", () => {
        applySort();
        renderStores(false);
    });

    // Quick Tags Click Event
    tagsContainer.addEventListener("click", (e) => {
        const tagBtn = e.target.closest(".tag-btn");
        if (!tagBtn) return;

        const tagText = tagBtn.dataset.search;

        if (activeTag === tagText) {
            tagBtn.classList.remove("active");
            searchInput.value = "";
            activeTag = null;
        } else {
            document.querySelectorAll(".tag-btn").forEach(btn => btn.classList.remove("active"));
            tagBtn.classList.add("active");
            searchInput.value = tagText;
            activeTag = tagText;
        }

        applyFilters();
    });

    // Load More Button Event
    loadMoreBtn.addEventListener("click", () => {
        currentPage++;
        renderStores(true);
    });

    // Theme Switcher Events
    const themeSwitcher = document.querySelector(".theme-switcher");
    if (themeSwitcher) {
        themeSwitcher.addEventListener("click", (e) => {
            const tabBtn = e.target.closest(".theme-tab");
            if (!tabBtn) return;
            
            const newTheme = tabBtn.dataset.theme;
            if (newTheme === activeTheme) return;
            
            document.querySelectorAll(".theme-tab").forEach(btn => btn.classList.remove("active"));
            tabBtn.classList.add("active");
            
            activeTheme = newTheme;
            
            // Reset search and filter values on theme switch
            searchInput.value = "";
            activeTag = null;
            
            initFilters();
            
            regionSelect.value = "";
            cuisineSelect.value = "";
            
            applyFilters();
            animateCounters();
        });
    }

    // ---------------------------------------------------------
    // 10. Initialization Render (Executed inside preloader after async load)
    // ---------------------------------------------------------
});
