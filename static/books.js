(() => {
    const CONFIG = {
        INITIAL_TODAY: window.APP_CONFIG.today,
        INITIAL_PREV_DATE: window.APP_CONFIG.yesterday,
        TIMEZONE_NAME: window.APP_CONFIG.timezoneName,
        IS_OWNER_HOST: window.APP_CONFIG.isOwnerHost,
        AMAZON_AFFILIATE_TAG: window.APP_CONFIG.amazonAffiliateTag,
        FUTURE_REFRESH_INTERVAL_MS: 2 * 60 * 60 * 1000,
        PREV_LOAD_TRIGGER_PX: 120,
    };

    const state = {
        nextDate: CONFIG.INITIAL_TODAY,
        prevDate: CONFIG.INITIAL_PREV_DATE,
        loadingNext: false,
        loadingPrev: false,
        nextLoadFailed: false,
        lastFutureRefreshAt: 0,
        prevLoadQueued: false,
        visibleSections: new Map(),
        sectionObserver: null,
        observerNext: null,
    };

    function getCurrentDateString() {
        return new Intl.DateTimeFormat("en-CA", {
            timeZone: CONFIG.TIMEZONE_NAME,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
        }).format(new Date());
    }

    function buildAmazonUrl(asin, withAffiliateTag = false) {
        let url = `https://www.amazon.co.jp/dp/${encodeURIComponent(asin)}`;
        if (withAffiliateTag && CONFIG.AMAZON_AFFILIATE_TAG) {
            url += `/ref=nosim?tag=${encodeURIComponent(CONFIG.AMAZON_AFFILIATE_TAG)}`;
        }
        return url;
    }

    function isMobileOrTablet() {
        const ua = navigator.userAgent.toLowerCase();
        return /iphone|ipad|ipod|android/.test(ua);
    }

    function shareOnTwitter(text, url) {
        const body = `${text} ${url}`;
        if (isMobileOrTablet()) {
            window.location.href = `twitter://post?message=${encodeURIComponent(body)}`;
        } else {
            window.open(
                `https://twitter.com/intent/tweet?text=${encodeURIComponent(body)}`,
                "_blank",
                "noopener,noreferrer"
            );
        }
    }

    function formatDateLabel(dateStr) {
        if (dateStr === getCurrentDateString()) {
            return `📅 今日発売 (${dateStr})`;
        }
        return dateStr;
    }

    function createShareButton(className, titleText, shareUrl) {
        const shareBtn = document.createElement("button");
        shareBtn.className = className;
        shareBtn.dataset.text = titleText;
        shareBtn.dataset.url = shareUrl;
        shareBtn.type = "button";
        shareBtn.setAttribute("aria-label", `${titleText} を X で共有`);

        const logo = document.createElement("img");
        logo.src = "/static/X-logo.svg";
        logo.alt = "";
        shareBtn.appendChild(logo);

        return shareBtn;
    }

    function createSection(books, currentDate) {
        const section = document.createElement("section");
        section.className = "date-section";
        section.dataset.date = currentDate;

        const isToday = currentDate === getCurrentDateString();
        if (isToday) {
            section.classList.add("is-today");
            section.id = "today-section";
            section.setAttribute("aria-label", `今日発売 ${currentDate}`);
        } else {
            section.setAttribute("aria-label", `${currentDate} 発売`);
        }

        const inner = document.createElement("div");
        inner.className = "date-section-inner";

        const title = document.createElement("div");
        title.className = "date-title";
        title.textContent = formatDateLabel(currentDate);
        inner.appendChild(title);

        if (isToday) {
            const subtitle = document.createElement("div");
            subtitle.className = "date-subtitle";
            subtitle.textContent = "ここが今日発売の本です。右下の「今日」ボタンでいつでもこの位置へ戻れます。";
            inner.appendChild(subtitle);
        }

        const grid = document.createElement("div");
        grid.className = "grid";

        books.forEach((book) => {
            const productUrl = buildAmazonUrl(book.asin, !CONFIG.IS_OWNER_HOST);
            const shareUrl = buildAmazonUrl(book.asin, CONFIG.IS_OWNER_HOST);

            const card = document.createElement("article");
            card.className = "card";

            const imgWrapper = document.createElement("div");
            imgWrapper.className = "image-wrapper";

            const imageLink = document.createElement("a");
            imageLink.href = productUrl;
            imageLink.target = "_blank";
            imageLink.rel = "noopener noreferrer";
            imageLink.className = "image-link";
            imageLink.setAttribute("aria-label", `${book.title} の Amazon ページを開く`);

            const img = document.createElement("img");
            img.src = book.image;
            img.loading = "lazy";
            img.alt = `${book.title} の表紙`;
            img.className = "book-image";
            imageLink.appendChild(img);

            imgWrapper.appendChild(imageLink);
            imgWrapper.appendChild(createShareButton("image-share-button", book.title, shareUrl));

            const cardHeader = document.createElement("div");
            cardHeader.className = "card-header";

            const cardText = document.createElement("div");
            cardText.className = "card-text";

            const titleLink = document.createElement("a");
            titleLink.href = productUrl;
            titleLink.target = "_blank";
            titleLink.rel = "noopener noreferrer";
            titleLink.textContent = book.title;
            titleLink.className = "title";

            const authorLink = document.createElement("a");
            authorLink.href = productUrl;
            authorLink.target = "_blank";
            authorLink.rel = "noopener noreferrer";
            authorLink.textContent = book.author;
            authorLink.className = "author";

            cardText.appendChild(titleLink);
            cardText.appendChild(authorLink);

            cardHeader.appendChild(cardText);
            cardHeader.appendChild(createShareButton("inline-share-button", book.title, shareUrl));

            card.appendChild(imgWrapper);
            card.appendChild(cardHeader);

            grid.appendChild(card);
        });

        inner.appendChild(grid);
        section.appendChild(inner);
        return section;
    }

    function createEmptyTodaySection(currentDate) {
        const section = document.createElement("section");
        section.className = "date-section is-today";
        section.dataset.date = currentDate;
        section.id = "today-section";
        section.setAttribute("aria-label", `今日発売 ${currentDate}`);

        const inner = document.createElement("div");
        inner.className = "date-section-inner";

        const title = document.createElement("div");
        title.className = "date-title";
        title.textContent = formatDateLabel(currentDate);
        inner.appendChild(title);

        const subtitle = document.createElement("div");
        subtitle.className = "date-subtitle";
        subtitle.textContent = "今日は新刊の予定がありません。右下の「今日」ボタンでいつでもこの位置へ戻れます。";
        inner.appendChild(subtitle);

        const empty = document.createElement("div");
        empty.className = "today-empty-message";
        empty.textContent = "本日の出版予定はありません。";
        inner.appendChild(empty);

        section.appendChild(inner);
        return section;
    }

    function observeSection(section) {
        if (!state.sectionObserver) return;
        state.sectionObserver.observe(section);
    }

    function appendBooks(books, currentDate, prepend = false) {
        if (!books.length) return false;

        const container = document.getElementById("book-container");
        if (container.querySelector(`[data-date="${CSS.escape(currentDate)}"]`)) {
            return false;
        }

        const section = createSection(books, currentDate);

        if (prepend) {
            container.prepend(section);
        } else {
            container.appendChild(section);
        }

        observeSection(section);
        updateStatusByViewport();
        return true;
    }

    function insertTodayPlaceholder(currentDate) {
        const container = document.getElementById("book-container");

        const existing = document.querySelector(`[data-date="${CSS.escape(currentDate)}"]`);
        if (existing) {
            if (!existing.id) {
                existing.id = "today-section";
            }
            existing.classList.add("is-today");
            existing.setAttribute("aria-label", `今日発売 ${currentDate}`);

            const title = existing.querySelector(".date-title");
            if (title) {
                title.textContent = formatDateLabel(currentDate);
            }

            if (!existing.querySelector(".date-subtitle")) {
                const subtitle = document.createElement("div");
                subtitle.className = "date-subtitle";
                subtitle.textContent = "今日は新刊の予定がありません。右下の「今日」ボタンでいつでもこの位置へ戻れます。";
                const inner = existing.querySelector(".date-section-inner");
                if (inner) {
                    const firstChildAfterTitle = inner.querySelector(".grid") || inner.children[1] || null;
                    inner.insertBefore(subtitle, firstChildAfterTitle);
                }
            }

            return existing;
        }

        const placeholder = createEmptyTodaySection(currentDate);

        const sections = [...container.querySelectorAll(".date-section")];
        const nextSection = sections.find((section) => (section.dataset.date || "") > currentDate);

        if (nextSection) {
            container.insertBefore(placeholder, nextSection);
        } else {
            container.appendChild(placeholder);
        }

        observeSection(placeholder);
        updateStatusByViewport();
        return placeholder;
    }

    async function fetchBooks(date, direction) {
        const res = await fetch(`/api/books?date=${encodeURIComponent(date)}&direction=${encodeURIComponent(direction)}`);
        if (!res.ok) {
            throw new Error("Network response was not ok");
        }
        return await res.json();
    }

    function updateStatusByViewport() {
        const statusText = document.getElementById("status-text");
        const statusBadge = document.getElementById("status-badge");

        const sections = [...document.querySelectorAll(".date-section")];
        if (!sections.length) {
            statusText.textContent = "読み込み中...";
            return;
        }

        let current = null;

        if (state.visibleSections.size > 0) {
            const visible = [...state.visibleSections.values()]
                .sort((a, b) => Math.abs(a.top) - Math.abs(b.top));
            current = visible[0]?.element || null;
        }

        if (!current) {
            current = sections.find((sec) => sec.getBoundingClientRect().top >= 0) || sections[sections.length - 1];
        }

        const currentDate = current?.dataset.date || "";
        if (!currentDate) {
            statusText.textContent = "読み込み中...";
            return;
        }

        const today = getCurrentDateString();

        if (currentDate === today) {
            statusBadge.textContent = "📅 今日";
            statusText.textContent = `現在位置: 今日発売 (${currentDate})`;
        } else if (currentDate < today) {
            statusBadge.textContent = "← 過去";
            statusText.textContent = `現在位置: ${currentDate} 発売（過去）`;
        } else {
            statusBadge.textContent = "未来 →";
            statusText.textContent = `現在位置: ${currentDate} 発売（未来）`;
        }
    }

    function setupSectionObserver() {
        state.sectionObserver = new IntersectionObserver((entries) => {
            for (const entry of entries) {
                const section = entry.target;
                if (entry.isIntersecting) {
                    state.visibleSections.set(section.dataset.date, {
                        element: section,
                        top: entry.boundingClientRect.top
                    });
                } else {
                    state.visibleSections.delete(section.dataset.date);
                }
            }
            updateStatusByViewport();
        }, {
            root: null,
            threshold: [0, 0.15, 0.3, 0.5, 0.8]
        });
    }

    async function loadNext() {
        const loader = document.getElementById("loader");
        if (!state.nextDate || state.loadingNext || state.nextLoadFailed) return false;

        state.loadingNext = true;
        loader.innerText = "Loading...";

        try {
            const requestedDate = state.nextDate;
            const data = await fetchBooks(state.nextDate, "next");
            const appended = appendBooks(data.books, data.current_date, false);
            state.nextDate = data.next_date;

            if (!state.nextDate) {
                loader.innerText = "これより先の発売予定はありません";
                if (state.observerNext) state.observerNext.unobserve(loader);
            } else {
                loader.innerText = "Loading...";
            }

            return requestedDate !== state.nextDate || appended;
        } catch (err) {
            console.error("Error loading next books:", err);
            state.nextLoadFailed = true;
            loader.innerText = "未来方向の読み込みに失敗しました";
            if (state.observerNext) state.observerNext.unobserve(loader);
            return false;
        } finally {
            state.loadingNext = false;
        }
    }

    async function loadPrev() {
        if (!state.prevDate || state.loadingPrev) return false;

        state.loadingPrev = true;
        try {
            const requestedDate = state.prevDate;
            const beforeHeight = document.documentElement.scrollHeight;
            const beforeTop = window.scrollY;

            const data = await fetchBooks(state.prevDate, "prev");
            const appended = appendBooks(data.books, data.current_date, true);
            state.prevDate = data.next_date;

            if (appended) {
                const afterHeight = document.documentElement.scrollHeight;
                const delta = afterHeight - beforeHeight;
                window.scrollTo(0, beforeTop + delta);
            }

            return requestedDate !== state.prevDate || appended;
        } catch (err) {
            console.error("Error loading previous books:", err);
            return false;
        } finally {
            state.loadingPrev = false;
        }
    }

    async function ensureScrollable() {
        while (document.body.scrollHeight <= window.innerHeight && state.nextDate && !state.nextLoadFailed) {
            const progressed = await loadNext();
            if (!progressed) break;
        }
    }

    function isLoaderNearViewport() {
        const loader = document.getElementById("loader");
        const rect = loader.getBoundingClientRect();
        return rect.top <= window.innerHeight + 200;
    }

    async function fillFutureUntilLoaderLeavesViewport(maxSteps = 20) {
        let steps = 0;

        while (state.nextDate && !state.nextLoadFailed && isLoaderNearViewport() && steps < maxSteps) {
            const beforeNextDate = state.nextDate;
            const progressed = await loadNext();
            steps += 1;

            if (!progressed || beforeNextDate === state.nextDate) {
                break;
            }
        }
    }

    async function maybeLoadPrevFromTop() {
        if (state.prevLoadQueued || state.loadingPrev || !state.prevDate) return;
        if (window.scrollY > CONFIG.PREV_LOAD_TRIGGER_PX) return;

        state.prevLoadQueued = true;
        try {
            await loadPrev();
        } finally {
            state.prevLoadQueued = false;
        }
    }

    function getSectionsFromToday() {
        const today = getCurrentDateString();
        return [...document.querySelectorAll(".date-section")].filter((section) => {
            const date = section.dataset.date || "";
            return date >= today;
        });
    }

    function clearSectionsFromToday() {
        const sections = getSectionsFromToday();
        for (const section of sections) {
            if (state.sectionObserver) {
                state.sectionObserver.unobserve(section);
            }
            state.visibleSections.delete(section.dataset.date);
            section.remove();
        }
    }

    function getViewportAnchor() {
        const sections = [...document.querySelectorAll(".date-section")];
        if (!sections.length) return null;

        let current = null;

        if (state.visibleSections.size > 0) {
            const visible = [...state.visibleSections.values()].sort((a, b) => Math.abs(a.top) - Math.abs(b.top));
            current = visible[0]?.element || null;
        }

        if (!current) {
            current = sections.find((sec) => sec.getBoundingClientRect().top >= 0) || sections[sections.length - 1];
        }

        if (!current) return null;

        return {
            date: current.dataset.date || "",
            offset: current.getBoundingClientRect().top,
        };
    }

    function restoreViewportAnchor(anchor) {
        if (!anchor || !anchor.date) return;

        const target = document.querySelector(`[data-date="${CSS.escape(anchor.date)}"]`) ||
            document.getElementById("today-section");
        if (!target) return;

        const top = window.scrollY + target.getBoundingClientRect().top - anchor.offset;
        window.scrollTo({ top, behavior: "auto" });
    }

    async function reloadFutureSections(anchor = null) {
        const loader = document.getElementById("loader");
        const today = getCurrentDateString();
        const targetDate = anchor?.date || "";

        clearSectionsFromToday();
        state.nextDate = today;
        state.nextLoadFailed = false;
        loader.innerText = "Loading...";

        if (state.observerNext) {
            state.observerNext.unobserve(loader);
            state.observerNext.observe(loader);
        }

        await loadNext();

        while (
            targetDate &&
            targetDate >= today &&
            !document.querySelector(`[data-date="${CSS.escape(targetDate)}"]`) &&
            state.nextDate &&
            !state.nextLoadFailed
        ) {
            const progressed = await loadNext();
            if (!progressed) break;
        }

        restoreViewportAnchor(anchor);
        await fillFutureUntilLoaderLeavesViewport();
        updateStatusByViewport();
    }

    async function refreshFutureSectionsIfNeeded(force = false) {
        const now = Date.now();
        if (!force && now - state.lastFutureRefreshAt < CONFIG.FUTURE_REFRESH_INTERVAL_MS) {
            return false;
        }

        const anchor = getViewportAnchor();
        await reloadFutureSections(anchor);
        state.lastFutureRefreshAt = now;
        return true;
    }

    async function ensureTodayVisible() {
        const today = getCurrentDateString();
        let el = document.getElementById("today-section");

        if (el && el.dataset.date === today) {
            el.scrollIntoView({ behavior: "auto", block: "start" });
            updateStatusByViewport();
            return;
        }

        if (el && el.dataset.date !== today) {
            el.removeAttribute("id");
            el.classList.remove("is-today");
            el.setAttribute("aria-label", `${el.dataset.date} 発売`);

            const oldSubtitle = el.querySelector(".date-subtitle");
            if (oldSubtitle) {
                oldSubtitle.remove();
            }

            const oldEmpty = el.querySelector(".today-empty-message");
            if (oldEmpty) {
                oldEmpty.remove();
            }

            const oldTitle = el.querySelector(".date-title");
            if (oldTitle) {
                oldTitle.textContent = formatDateLabel(el.dataset.date);
            }
        }

        const existingSection = document.querySelector(`[data-date="${CSS.escape(today)}"]`);
        if (existingSection) {
            existingSection.id = "today-section";
            existingSection.classList.add("is-today");
            existingSection.setAttribute("aria-label", `今日発売 ${today}`);

            const title = existingSection.querySelector(".date-title");
            if (title) {
                title.textContent = formatDateLabel(today);
            }

            if (!existingSection.querySelector(".date-subtitle")) {
                const subtitle = document.createElement("div");
                subtitle.className = "date-subtitle";
                subtitle.textContent = "ここが今日発売の本です。右下の「今日」ボタンでいつでもこの位置へ戻れます。";
                const inner = existingSection.querySelector(".date-section-inner");
                const grid = existingSection.querySelector(".grid");
                if (inner && grid) {
                    inner.insertBefore(subtitle, grid);
                }
            }

            existingSection.scrollIntoView({ behavior: "auto", block: "start" });
            await fillFutureUntilLoaderLeavesViewport();
            updateStatusByViewport();
            return;
        }

        // 今日に本が無い場合でも、前後関係の正しい位置に空の今日セクションを作る
        await fetchBooks(today, "next");  // 将来データが未ロードでもAPI疎通は確認
        el = insertTodayPlaceholder(today);
        el.scrollIntoView({ behavior: "auto", block: "start" });

        await fillFutureUntilLoaderLeavesViewport();
        updateStatusByViewport();
    }

    function setupShareHandler() {
        document.body.addEventListener("click", (event) => {
            const btn = event.target.closest(".image-share-button, .inline-share-button");
            if (!btn) return;

            event.preventDefault();
            event.stopPropagation();

            const text = btn.dataset.text;
            const url = btn.dataset.url;
            shareOnTwitter(text, url);
        });
    }

    function setupTodayButton() {
        document.getElementById("todayBtn").addEventListener("click", async () => {
            await refreshFutureSectionsIfNeeded(true);

            const today = getCurrentDateString();
            let el = document.getElementById("today-section");

            if (!el || el.dataset.date !== today) {
                await ensureTodayVisible();
                el = document.getElementById("today-section");
            }

            if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "start" });
            }

            await fillFutureUntilLoaderLeavesViewport();
        });
    }

    function setupNextObserver() {
        state.observerNext = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && !state.nextLoadFailed) {
                loadNext();
            }
        }, {
            root: null,
            rootMargin: "300px 0px",
            threshold: 0
        });

        state.observerNext.observe(document.getElementById("loader"));
    }

    function setupWindowEvents() {
        window.addEventListener("scroll", () => {
            updateStatusByViewport();
            maybeLoadPrevFromTop();
        }, { passive: true });

        window.addEventListener("resize", () => {
            updateStatusByViewport();
            maybeLoadPrevFromTop();
        });

        document.addEventListener("visibilitychange", async () => {
            if (document.visibilityState !== "visible") return;
            await refreshFutureSectionsIfNeeded(false);
        });
    }

    async function init() {
        setupShareHandler();
        setupSectionObserver();
        setupNextObserver();
        setupTodayButton();
        setupWindowEvents();

        await loadNext();

        const today = getCurrentDateString();
        if (!document.querySelector(`[data-date="${CSS.escape(today)}"]`)) {
            insertTodayPlaceholder(today);
        }

        await ensureScrollable();
        await fillFutureUntilLoaderLeavesViewport();
        await maybeLoadPrevFromTop();

        state.lastFutureRefreshAt = Date.now();
        updateStatusByViewport();
    }

    init();
})();
