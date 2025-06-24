const portfolioDataTabsSection = document.querySelector("#portfolio-data-tabs-section");

if (portfolioDataTabsSection) {
    const portfolioDataTableEl = portfolioDataTabsSection.querySelector("#portfolio-data-table");
    const stocksSummaryDataTableEl = portfolioDataTabsSection.querySelector("#stocks-summary-data-table");
    const stocksSummaryFilterURLParamName = "filter_summary_by";
    const stocksSummaryFiltersWrapper = portfolioDataTabsSection.querySelector("#stocks-summary-filters-wp");


    if (stocksSummaryFiltersWrapper) {
        const stocksSummaryFilters = stocksSummaryFiltersWrapper.querySelectorAll('.stocks-summary-filter');
        const activeFilterValue = stocksSummaryFiltersWrapper.dataset.activefilter ?? "";

        stocksSummaryFilters.forEach((filter) => {
            filter.onclick = function () {
                const filterValue = this.children[0].dataset.value;
                updateURLParams(stocksSummaryFilterURLParamName, filterValue);
                window.location.reload();
            }

            if (activeFilterValue) {
                const filterValue = filter.children[0].dataset.value ?? "";
                if (filterValue.toLowerCase() == activeFilterValue.toLowerCase()) {
                    filter.classList.add("active")
                }
                else {
                    filter.classList.remove("active")
                }
            }
        });
    }

    if (portfolioDataTableEl) {
        // Portfolio datatable configuration
        const portfolioDataTable = new DataTable(portfolioDataTableEl, {
            dom: "frtip",
            searchable: true,
            sortable: true,
            scrollX: false,
            paging: false,
            info: false,
            columnDefs: [{ targets: 'no-sort', orderable: false }]
        });
    }

    if (stocksSummaryDataTableEl) {
        // Stocks summary datatable configuration
        const stocksSummaryDataTable = new DataTable(stocksSummaryDataTableEl, {
            dom: "frtip",
            searchable: true,
            sortable: true,
            scrollX: false,
            paging: false,
            info: false,
            columnDefs: [
                { targets: 'no-sort', orderable: false }, 
            ]
        });
    }
}
