(function (window, document) {
    "use strict";

    const SELECTOR =
        "select[data-djangospice-lookup]";

    const EVENT_PREFIX =
        "djangospice:lookup";

    const DEFAULTS = Object.freeze({
        delay: 250,
        pageSize: 20,
        minimumInputLength: 0,
        searchParam: "q",
        pageParam: "page",
        pageSizeParam: "page_size",
        placeholder: "Select...",
        searchPlaceholder: "Search...",
        allowClear: true,
        tokenHeader: "X-Lookup-Token",
    });

    const instances = new WeakMap();


    // ================================================================
    // Utilities
    // ================================================================

    function parseBoolean(value, fallback) {
        if (
            value === undefined ||
            value === null ||
            value === ""
        ) {
            return fallback;
        }

        return String(value).toLowerCase() === "true";
    }


    function parseInteger(value, fallback) {
        const parsed =
            Number.parseInt(value, 10);

        return Number.isFinite(parsed)
            ? parsed
            : fallback;
    }


    function parseDependencies(value) {
        if (!value) {
            return [];
        }

        return String(value)
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);
    }


    function debounce(callback, delay) {
        let timer = null;

        const debounced = function (...args) {
            window.clearTimeout(timer);

            timer = window.setTimeout(
                () => callback.apply(this, args),
                delay,
            );
        };

        debounced.cancel = function () {
            window.clearTimeout(timer);
            timer = null;
        };

        return debounced;
    }


    function escapeSelector(value) {
        if (
            window.CSS &&
            typeof window.CSS.escape === "function"
        ) {
            return window.CSS.escape(value);
        }

        return String(value).replace(
            /([!"#$%&'()*+,./:;<=>?@[\\\]^`{|}~])/g,
            "\\$1",
        );
    }


    function createElement(
        tag,
        className,
        attributes = {},
    ) {
        const element =
            document.createElement(tag);

        if (className) {
            element.className = className;
        }

        for (
            const [name, value]
            of Object.entries(attributes)
        ) {
            if (
                value === null ||
                value === undefined
            ) {
                continue;
            }

            if (value === true) {
                element.setAttribute(
                    name,
                    "",
                );
            } else if (value !== false) {
                element.setAttribute(
                    name,
                    String(value),
                );
            }
        }

        return element;
    }


    // ================================================================
    // LookupController
    // ================================================================

    class LookupController {

        constructor(select) {
            this.select = select;

            this.destroyed = false;

            this.loading = false;

            this.abortController = null;

            this.requestSequence = 0;

            this.page = 1;

            this.hasNext = false;

            this.highlightedIndex = -1;

            this.dependencies = [];

            this.dependencyListeners = [];

            this.config = this.readConfig();

            /*
             * Capture everything Django rendered initially.
             *
             * These options must survive the first remote lookup,
             * particularly for bound forms and initial values.
             */
            this.initialOptions =
                this.captureOptions();

            this.selectedValues =
                this.getSelectedValues();

            this.initialize();
        }


        // ============================================================
        // Configuration
        // ============================================================

        readConfig() {
            const data =
                this.select.dataset;

            return {
                url:
                    data.lookupUrl || "",

                name:
                    data.lookupName ||
                    this.select.name ||
                    "",

                delay:
                    DEFAULTS.delay,

                pageSize:
                    parseInteger(
                        data.lookupPageSize,
                        DEFAULTS.pageSize,
                    ),

                minimumInputLength:
                    parseInteger(
                        data.lookupMinSearchLength,
                        DEFAULTS.minimumInputLength,
                    ),

                searchParam:
                    data.lookupSearchParam ||
                    DEFAULTS.searchParam,

                pageParam:
                    data.lookupPageParam ||
                    DEFAULTS.pageParam,

                pageSizeParam:
                    data.lookupPageSizeParam ||
                    DEFAULTS.pageSizeParam,

                placeholder:
                    data.lookupPlaceholder ||
                    DEFAULTS.placeholder,

                searchPlaceholder:
                    data.lookupSearchPlaceholder ||
                    DEFAULTS.searchPlaceholder,

                allowClear:
                    parseBoolean(
                        data.lookupAllowClear,
                        DEFAULTS.allowClear,
                    ),

                token:
                    data.lookupToken ||
                    null,

                tokenHeader:
                    data.lookupTokenHeader ||
                    DEFAULTS.tokenHeader,
            };
        }


        // ============================================================
        // Initialization
        // ============================================================

        initialize() {
            this.dependencies =
                this.readDependencies();

            this.createInterface();

            this.bindEvents();

            this.bindDependencies();

            this.syncDisabledState();

            this.syncFromSelect();

            this.renderInitialResults();
        }


        readDependencies() {
            return parseDependencies(
                this.select.dataset
                    .lookupDependencies,
            );
        }


        // ============================================================
        // Initial Django options
        // ============================================================

        captureOptions() {
            return Array.from(
                this.select.options,
            ).map((option) => ({
                value: option.value,
                label: option.textContent,
                selected: option.selected,
                disabled: option.disabled,
            }));
        }


        renderInitialResults() {
            /*
             * Django has already rendered the current choices.
             *
             * Display them immediately rather than issuing an
             * unnecessary request.
             */
            this.renderResults(
                this.initialOptions.map(
                    (option) => ({
                        value: option.value,
                        label: option.label,
                    }),
                ),
            );
        }


        // ============================================================
        // Interface
        // ============================================================

        createInterface() {
            const parent =
                this.select.parentNode;

            if (!parent) {
                return;
            }

            this.wrapper = createElement(
                "div",
                "djangospice-lookup",
            );

            this.wrapper.dataset
                .djangospiceLookupWrapper = "";


            // --------------------------------------------------------
            // Selected values
            // --------------------------------------------------------

            if (this.select.multiple) {
                this.selection =
                    createElement(
                        "div",
                        "djangospice-lookup__selection",
                    );
            } else {
                this.selection = null;
            }


            // --------------------------------------------------------
            // Search
            // --------------------------------------------------------

            this.search = createElement(
                "input",
                "djangospice-lookup__input",
                {
                    type: "search",
                    autocomplete: "off",
                    role: "combobox",
                    "aria-autocomplete": "list",
                    "aria-expanded": "false",
                    "aria-haspopup": "listbox",
                    placeholder:
                        this.config.searchPlaceholder,
                },
            );


            // --------------------------------------------------------
            // Clear
            // --------------------------------------------------------

            if (this.config.allowClear) {
                this.clearButton =
                    createElement(
                        "button",
                        "djangospice-lookup__clear",
                        {
                            type: "button",
                            "aria-label":
                                "Clear selection",
                        },
                    );

                this.clearButton.textContent =
                    "×";
            } else {
                this.clearButton = null;
            }


            // --------------------------------------------------------
            // Dropdown
            // --------------------------------------------------------

            this.listbox = createElement(
                "div",
                "djangospice-lookup__dropdown",
                {
                    role: "listbox",
                    tabindex: "-1",
                },
            );


            // --------------------------------------------------------
            // Loading / empty / error
            // --------------------------------------------------------

            this.status = createElement(
                "div",
                "djangospice-lookup__status",
                {
                    role: "status",
                    "aria-live": "polite",
                },
            );

            this.status.hidden = true;


            // --------------------------------------------------------
            // Build DOM
            // --------------------------------------------------------

            parent.insertBefore(
                this.wrapper,
                this.select,
            );

            if (this.selection) {
                this.wrapper.appendChild(
                    this.selection,
                );
            }

            this.wrapper.appendChild(
                this.search,
            );

            if (this.clearButton) {
                this.wrapper.appendChild(
                    this.clearButton,
                );
            }

            this.wrapper.appendChild(
                this.listbox,
            );

            this.wrapper.appendChild(
                this.status,
            );

            /*
             * The native select remains the real form control.
             */
            this.wrapper.appendChild(
                this.select,
            );

            this.select.classList.add(
                "djangospice-lookup__native",
            );

            this.listbox.id =
                this.getListboxId();

            this.search.setAttribute(
                "aria-controls",
                this.listbox.id,
            );

            this.wrapper.classList.add(
                "is-enhanced",
            );
        }

        syncDisabledState() {
            const disabled = this.select.disabled;

            this.search.disabled = disabled;

            if (this.clearButton) {
                this.clearButton.disabled = disabled;
            }

            this.wrapper.classList.toggle(
                "is-disabled",
                disabled,
            );
        }


        getListboxId() {
            if (this.select.id) {
                return (
                    `${this.select.id}-lookup-listbox`
                );
            }

            return (
                `djangospice-lookup-${Math.random()
                    .toString(36)
                    .slice(2)}`
            );
        }


        // ============================================================
        // Events
        // ============================================================

        bindEvents() {
            this.handleSearch =
                debounce(
                    () => {
                        this.searchLookup();
                    },
                    this.config.delay,
                );

            this.search.addEventListener(
                "input",
                this.handleSearch,
            );


            this.search.addEventListener(
                "focus",
                () => {
                    this.open();
                },
            );


            this.search.addEventListener(
                "keydown",
                (event) => {
                    this.handleKeydown(event);
                },
            );


            this.listbox.addEventListener(
                "scroll",
                () => {
                    this.checkLoadMore();
                },
            );


            this.listbox.addEventListener(
                "mousedown",
                (event) => {
                    const option =
                        event.target.closest(
                            "[data-lookup-option]",
                        );

                    if (option) {
                        event.preventDefault();
                    }
                },
            );


            this.listbox.addEventListener(
                "click",
                (event) => {
                    const option =
                        event.target.closest(
                            "[data-lookup-option]",
                        );

                    if (!option) {
                        return;
                    }

                    this.selectResult(
                        option.dataset.lookupValue,
                    );
                },
            );


            this.select.addEventListener(
                "change",
                () => {
                    this.syncFromSelect();
                },
            );


            if (this.clearButton) {
                this.clearButton.addEventListener(
                    "click",
                    () => {
                        this.clearSelection();
                    },
                );
            }


            this.handleDocumentClick =
                (event) => {
                    if (
                        !this.wrapper.contains(
                            event.target,
                        )
                    ) {
                        this.close();
                    }
                };

            document.addEventListener(
                "mousedown",
                this.handleDocumentClick,
            );
        }


        // ============================================================
        // Dependencies
        // ============================================================

        bindDependencies() {
            for (
                const dependency
                of this.dependencies
            ) {
                const source =
                    this.findDependency(
                        dependency,
                    );

                if (!source) {
                    continue;
                }

                const handler =
                    () => {
                        this.handleDependencyChange();
                    };

                source.addEventListener(
                    "change",
                    handler,
                );

                this.dependencyListeners.push({
                    element: source,
                    handler,
                });
            }
        }


        findDependency(name) {
            if (!name) {
                return null;
            }

            const lookup =
                document.querySelector(
                    `[data-lookup-name="${escapeSelector(name)}"]`,
                );

            if (lookup) {
                return lookup;
            }

            return document.querySelector(
                `[name="${escapeSelector(name)}"]`,
            );
        }


        handleDependencyChange() {
            this.abortRequest();

            this.handleSearch.cancel();

            this.clearResults();

            this.clearSelection(false);

            this.page = 1;

            this.hasNext = false;

            this.close();
        }


        getDependencyValue(name) {
            const element =
                this.findDependency(name);

            if (!element) {
                return null;
            }

            if (element.multiple) {
                return Array.from(
                    element.selectedOptions,
                )
                    .map(
                        (option) =>
                            option.value,
                    )
                    .filter(Boolean);
            }

            return element.value || null;
        }


        // ============================================================
        // Search
        // ============================================================

        searchLookup() {
            const term =
                this.search.value.trim();

            if (
                term.length <
                this.config.minimumInputLength
            ) {
                this.clearRemoteResults();

                if (
                    this.config.minimumInputLength
                ) {
                    this.setStatus(
                        `Enter at least ${this.config.minimumInputLength} character${
                            this.config.minimumInputLength === 1
                                ? ""
                                : "s"
                        }.`,
                    );
                }

                return;
            }

            this.page = 1;

            this.hasNext = false;

            this.load({
                term,
                page: 1,
                replace: true,
            });
        }


        // ============================================================
        // Request
        // ============================================================

        async load({
            term = "",
            page = 1,
            replace = true,
        }) {
            if (
                this.destroyed ||
                !this.config.url
            ) {
                return;
            }

            const requestId =
                ++this.requestSequence;

            this.abortRequest();

            this.abortController =
                new AbortController();

            const url =
                new URL(
                    this.config.url,
                    window.location.origin,
                );

            if (term) {
                url.searchParams.set(
                    this.config.searchParam,
                    term,
                );
            }

            url.searchParams.set(
                this.config.pageParam,
                String(page),
            );

            url.searchParams.set(
                this.config.pageSizeParam,
                String(
                    this.config.pageSize,
                ),
            );

            this.appendDependencies(url);

            const headers = {
                Accept: "application/json",
            };

            if (this.config.token) {
                headers[
                    this.config.tokenHeader
                ] = this.config.token;
            }

            this.setLoading(true);

            try {
                const response =
                    await fetch(
                        url.toString(),
                        {
                            method: "GET",
                            headers,
                            credentials:
                                "same-origin",
                            signal:
                                this.abortController
                                    .signal,
                        },
                    );

                if (
                    this.destroyed ||
                    requestId !==
                        this.requestSequence
                ) {
                    return;
                }

                if (!response.ok) {
                    throw new Error(
                        `Lookup request failed: ${response.status}`,
                    );
                }

                const data =
                    await response.json();

                this.handleResponse(
                    data,
                    {
                        page,
                        replace,
                    },
                );

            } catch (error) {
                if (
                    error.name ===
                    "AbortError"
                ) {
                    return;
                }

                this.setError(
                    "Unable to load results.",
                );

                this.dispatch(
                    "error",
                    {
                        error,
                    },
                );

            } finally {
                if (
                    requestId ===
                    this.requestSequence
                ) {
                    this.setLoading(false);
                }
            }
        }


        appendDependencies(url) {
            for (
                const dependency
                of this.dependencies
            ) {
                const value =
                    this.getDependencyValue(
                        dependency,
                    );

                if (
                    value === null ||
                    value === undefined ||
                    value === ""
                ) {
                    continue;
                }

                if (Array.isArray(value)) {
                    for (
                        const item
                        of value
                    ) {
                        url.searchParams.append(
                            dependency,
                            item,
                        );
                    }

                    continue;
                }

                url.searchParams.set(
                    dependency,
                    value,
                );
            }
        }


        abortRequest() {
            if (this.abortController) {
                this.abortController.abort();

                this.abortController = null;
            }
        }


        // ============================================================
        // Response
        // ============================================================

        handleResponse(
            data,
            {
                page,
                replace,
            },
        ) {
            const results =
                Array.isArray(data?.results)
                    ? data.results
                    : [];

            if (replace) {
                this.clearRemoteResults();
            }

            this.renderResults(results);

            const pagination =
                data?.pagination || {};

            this.hasNext = Boolean(
                pagination.has_next ??
                pagination.more ??
                false,
            );

            this.page = page;

            if (!results.length) {
                this.setEmpty();
            } else {
                this.clearStatus();
            }

            this.open();
        }


        renderResults(results) {
            const selected =
                new Set(
                    this.getSelectedValues(),
                );

            /*
             * Do not duplicate results already rendered by Django
             * or by an earlier remote page.
             */
            const existing =
                new Set(
                    Array.from(
                        this.listbox.querySelectorAll(
                            "[data-lookup-option]",
                        ),
                    ).map(
                        (option) =>
                            option.dataset
                                .lookupValue,
                    ),
                );

            for (
                const result
                of results
            ) {
                const value =
                    result?.value ??
                    result?.id ??
                    "";

                const label =
                    result?.label ??
                    result?.text ??
                    "";

                if (!value) {
                    continue;
                }

                const stringValue =
                    String(value);

                if (
                    existing.has(
                        stringValue,
                    )
                ) {
                    continue;
                }

                const option =
                    createElement(
                        "div",
                        "djangospice-lookup__option",
                        {
                            role: "option",
                            "data-lookup-option":
                                "",
                            "data-lookup-value":
                                stringValue,
                        },
                    );

                option.textContent =
                    label;

                if (
                    selected.has(
                        stringValue,
                    )
                ) {
                    option.classList.add(
                        "is-selected",
                    );

                    option.setAttribute(
                        "aria-selected",
                        "true",
                    );
                } else {
                    option.setAttribute(
                        "aria-selected",
                        "false",
                    );
                }

                this.listbox.appendChild(
                    option,
                );

                existing.add(
                    stringValue,
                );
            }

            this.updateHighlight();
        }


        // ============================================================
        // Result state
        // ============================================================

        clearRemoteResults() {
            /*
             * Keep Django's original options.
             *
             * This is important for:
             *
             * - initial values
             * - bound forms
             * - validation errors
             * - disabled choices
             */
            this.listbox.innerHTML = "";

            this.renderResults(
                this.initialOptions.map(
                    (option) => ({
                        value: option.value,
                        label: option.label,
                    }),
                ),
            );

            this.hasNext = false;

            this.page = 1;

            this.clearStatus();
        }


        clearResults() {
            this.listbox.innerHTML = "";

            this.highlightedIndex = -1;

            this.clearStatus();
        }


        setLoading(value) {
            this.loading = value;

            this.wrapper.classList.toggle(
                "is-loading",
                value,
            );

            if (value) {
                this.setStatus(
                    "Loading...",
                );
            } else if (
                this.status.textContent ===
                "Loading..."
            ) {
                this.clearStatus();
            }
        }


        setEmpty() {
            this.setStatus(
                "No results found.",
            );
        }


        setError(message) {
            this.setStatus(message);

            this.wrapper.classList.add(
                "has-error",
            );
        }


        setStatus(message) {
            this.status.textContent =
                message;

            this.status.hidden =
                !message;
        }


        clearStatus() {
            this.status.textContent = "";

            this.status.hidden = true;

            this.wrapper.classList.remove(
                "has-error",
            );
        }


        // ============================================================
        // Selection
        // ============================================================

        selectResult(value) {
            if (!value) {
                return;
            }

            if (this.select.multiple) {
                this.toggleMultipleValue(
                    value,
                );
            } else {
                this.setSingleValue(
                    value,
                );

                this.close();
            }

            this.syncFromSelect();

            this.dispatch(
                "change",
                {
                    value:
                        this.getSelectedValues(),
                },
            );
        }


        setSingleValue(value) {
            const option =
                this.ensureNativeOption(
                    value,
                );

            this.select.value =
                option.value;

            this.dispatchNativeChange();
        }


        toggleMultipleValue(value) {
            const option =
                this.ensureNativeOption(
                    value,
                );

            option.selected =
                !option.selected;

            this.dispatchNativeChange();
        }


        ensureNativeOption(value) {
            const stringValue =
                String(value);

            let option =
                Array.from(
                    this.select.options,
                ).find(
                    (item) =>
                        item.value ===
                        stringValue,
                );

            if (!option) {
                const lookupOption =
                    this.listbox.querySelector(
                        `[data-lookup-value="${escapeSelector(stringValue)}"]`,
                    );

                option =
                    document.createElement(
                        "option",
                    );

                option.value =
                    stringValue;

                option.textContent =
                    lookupOption
                        ? lookupOption.textContent
                        : stringValue;

                this.select.appendChild(
                    option,
                );
            }

            return option;
        }


        clearSelection(
            dispatch = true,
        ) {
            if (this.select.multiple) {
                for (
                    const option
                    of this.select.options
                ) {
                    option.selected = false;
                }
            } else {
                this.select.value = "";
            }

            if (dispatch) {
                this.dispatchNativeChange();

                this.dispatch(
                    "clear",
                );
            }

            this.syncFromSelect();
        }


        dispatchNativeChange() {
            this.select.dispatchEvent(
                new Event(
                    "change",
                    {
                        bubbles: true,
                    },
                ),
            );
        }


        getSelectedValues() {
            return Array.from(
                this.select.selectedOptions,
            ).map(
                (option) =>
                    option.value,
            );
        }


        // ============================================================
        // Multiple selection chips
        // ============================================================

        renderSelection() {
            if (!this.selection) {
                return;
            }

            this.selection.innerHTML = "";

            const selected =
                Array.from(
                    this.select.selectedOptions,
                );

            for (
                const option
                of selected
            ) {
                const chip =
                    createElement(
                        "span",
                        "djangospice-lookup__chip",
                    );

                const label =
                    createElement(
                        "span",
                        "djangospice-lookup__chip-label",
                    );

                label.textContent =
                    option.textContent;

                const remove =
                    createElement(
                        "button",
                        "djangospice-lookup__chip-remove",
                        {
                            type: "button",
                            "aria-label":
                                `Remove ${option.textContent}`,
                        },
                    );

                remove.textContent = "×";

                remove.addEventListener(
                    "click",
                    (event) => {
                        event.preventDefault();

                        event.stopPropagation();

                        option.selected =
                            false;

                        this.dispatchNativeChange();
                    },
                );

                chip.appendChild(label);

                chip.appendChild(remove);

                this.selection.appendChild(
                    chip,
                );
            }
        }


        syncFromSelect() {
            const selected =
                new Set(
                    this.getSelectedValues(),
                );

            for (
                const option
                of this.listbox.querySelectorAll(
                    "[data-lookup-option]",
                )
            ) {
                const value =
                    option.dataset
                        .lookupValue;

                const isSelected =
                    selected.has(value);

                option.classList.toggle(
                    "is-selected",
                    isSelected,
                );

                option.setAttribute(
                    "aria-selected",
                    String(isSelected),
                );
            }

            this.renderSelection();

            if (this.clearButton) {
                this.clearButton.hidden =
                    selected.size === 0;
            }
        }


        // ============================================================
        // Keyboard navigation
        // ============================================================

        handleKeydown(event) {
            const options =
                this.getVisibleOptions();

            switch (event.key) {

                case "ArrowDown":
                    event.preventDefault();

                    this.open();

                    this.moveHighlight(1);

                    break;


                case "ArrowUp":
                    event.preventDefault();

                    this.open();

                    this.moveHighlight(-1);

                    break;


                case "Enter":
                    if (
                        this.highlightedIndex >=
                        0
                    ) {
                        event.preventDefault();

                        const option =
                            options[
                                this.highlightedIndex
                            ];

                        if (option) {
                            this.selectResult(
                                option.dataset
                                    .lookupValue,
                            );
                        }
                    }

                    break;


                case "Escape":
                    event.preventDefault();

                    this.close();

                    break;


                case "Home":
                    if (options.length) {
                        event.preventDefault();

                        this.highlightedIndex =
                            0;

                        this.updateHighlight();
                    }

                    break;


                case "End":
                    if (options.length) {
                        event.preventDefault();

                        this.highlightedIndex =
                            options.length - 1;

                        this.updateHighlight();
                    }

                    break;
            }
        }


        getVisibleOptions() {
            return Array.from(
                this.listbox.querySelectorAll(
                    "[data-lookup-option]",
                ),
            );
        }


        moveHighlight(direction) {
            const options =
                this.getVisibleOptions();

            if (!options.length) {
                return;
            }

            let index =
                this.highlightedIndex;

            index += direction;

            if (index < 0) {
                index =
                    options.length - 1;
            }

            if (
                index >=
                options.length
            ) {
                index = 0;
            }

            this.highlightedIndex =
                index;

            this.updateHighlight();
        }


        updateHighlight() {
            const options =
                this.getVisibleOptions();

            options.forEach(
                (option, index) => {
                    const active =
                        index ===
                        this.highlightedIndex;

                    option.classList.toggle(
                        "is-highlighted",
                        active,
                    );
                },
            );

            const active =
                options[
                    this.highlightedIndex
                ];

            if (!active) {
                this.search.removeAttribute(
                    "aria-activedescendant",
                );

                return;
            }

            const id =
                this.getOptionId(
                    active,
                );

            active.id = id;

            this.search.setAttribute(
                "aria-activedescendant",
                id,
            );

            active.scrollIntoView({
                block: "nearest",
            });
        }


        getOptionId(option) {
            return (
                this.listbox.id +
                "-" +
                option.dataset.lookupValue
                    .replace(
                        /[^a-zA-Z0-9_-]/g,
                        "-",
                    )
            );
        }


        // ============================================================
        // Dropdown
        // ============================================================

        open() {
            this.wrapper.classList.add(
                "is-open",
            );

            this.search.setAttribute(
                "aria-expanded",
                "true",
            );
        }


        close() {
            this.wrapper.classList.remove(
                "is-open",
            );

            this.search.setAttribute(
                "aria-expanded",
                "false",
            );

            this.highlightedIndex = -1;

            this.search.removeAttribute(
                "aria-activedescendant",
            );
        }


        // ============================================================
        // Pagination
        // ============================================================

        checkLoadMore() {
            if (
                this.loading ||
                !this.hasNext
            ) {
                return;
            }

            const threshold = 48;

            if (
                this.listbox.scrollTop +
                    this.listbox.clientHeight +
                    threshold >=
                this.listbox.scrollHeight
            ) {
                const term =
                    this.search.value.trim();

                this.load({
                    term,
                    page:
                        this.page + 1,
                    replace: false,
                });
            }
        }


        // ============================================================
        // Events
        // ============================================================

        dispatch(name, detail = {}) {
            this.select.dispatchEvent(
                new CustomEvent(
                    `${EVENT_PREFIX}:${name}`,
                    {
                        bubbles: true,
                        detail,
                    },
                ),
            );
        }


        // ============================================================
        // Lifecycle
        // ============================================================

        destroy() {
            if (this.destroyed) {
                return;
            }

            this.destroyed = true;

            this.abortRequest();

            this.handleSearch.cancel();

            for (
                const {
                    element,
                    handler,
                }
                of this.dependencyListeners
            ) {
                element.removeEventListener(
                    "change",
                    handler,
                );
            }

            this.dependencyListeners = [];

            document.removeEventListener(
                "mousedown",
                this.handleDocumentClick,
            );

            /*
             * Restore the original Django select
             * exactly where it belongs.
             */
            if (
                this.wrapper &&
                this.wrapper.parentNode
            ) {
                this.wrapper.parentNode.insertBefore(
                    this.select,
                    this.wrapper,
                );

                this.wrapper.remove();
            }

            this.select.classList.remove(
                "djangospice-lookup__native",
            );

            instances.delete(
                this.select,
            );
        }
    }


    // ================================================================
    // Public API
    // ================================================================

    function initialize(element) {
        if (!element) {
            return null;
        }

        const existing =
            instances.get(element);

        if (existing) {
            return existing;
        }

        const controller =
            new LookupController(element);

        instances.set(
            element,
            controller,
        );

        return controller;
    }


    function initializeAll(root = document) {
        if (
            !root ||
            !root.querySelectorAll
        ) {
            return;
        }

        if (
            root.matches &&
            root.matches(SELECTOR)
        ) {
            initialize(root);
        }

        root
            .querySelectorAll(SELECTOR)
            .forEach(initialize);
    }


    function destroy(element) {
        const controller =
            instances.get(element);

        if (controller) {
            controller.destroy();
        }
    }


    function destroyAll(root = document) {
        if (
            !root ||
            !root.querySelectorAll
        ) {
            return;
        }

        if (
            root.matches &&
            root.matches(SELECTOR)
        ) {
            destroy(root);
        }

        root
            .querySelectorAll(SELECTOR)
            .forEach(destroy);
    }


    function get(element) {
        return (
            instances.get(element) ||
            null
        );
    }


    // ================================================================
    // HTMX
    // ================================================================

    document.addEventListener(
        "htmx:beforeSwap",
        (event) => {
            const target =
                event.detail?.target;

            if (target) {
                destroyAll(target);
            }
        },
    );


    document.addEventListener(
        "htmx:afterSwap",
        (event) => {
            const target =
                event.detail?.target;

            initializeAll(
                target || document,
            );
        },
    );


    document.addEventListener(
        "htmx:oobAfterSwap",
        (event) => {
            const target =
                event.detail?.target;

            initializeAll(
                target || document,
            );
        },
    );


    // ================================================================
    // Initial page load
    // ================================================================

    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            () => initializeAll(),
            {
                once: true,
            },
        );
    } else {
        initializeAll();
    }


    // ================================================================
    // Global API
    // ================================================================

    window.DjangoSpice =
        window.DjangoSpice || {};

    window.DjangoSpice.Lookup = {
        initialize,
        initializeAll,
        destroy,
        destroyAll,
        get,
    };

})(window, document);