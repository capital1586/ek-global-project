const portfolioPerformanceSection = document.querySelector("#portfolio-performance");
const performanceDataRefreshInterval = 5 * 60 * 1000; // 1 minute


function getLineChartData(rawData) {
    if (typeof rawData === "string") {
        chartData = JSON.parse(rawData);
    } else {
        chartData = rawData;
    };
    const KSE100Data = chartData["KSE100"];
    const portfolioData = chartData["portfolio"];
    const colors = chartData["colors"];
    let datasets = [];

    // Function to parse server data into coordinates
    // for chart.js line chart
    function dataToCoordinates(data) {
        let parsedData = [];
        for (const [date, value] of Object.entries(data)) {
            parsedData.push({ x: date, y: value });
        };
        // Sort data by date
        parsedData.sort(
            (firstCoordinate, secondCoordinate) => (firstCoordinate.x > secondCoordinate.x) ? 1 : -1
        );
        return parsedData;
    };

    // Loop through portfolio data 
    // Create and add datasets and get date labels
    for (const [symbol, data] of Object.entries(portfolioData)) {
        let dataset = {
            label: symbol.toUpperCase(),
            data: dataToCoordinates(data),
            fill: false,
            borderColor: colors[symbol],
            borderWidth: 3.2,
            backgroundColor: colors[symbol],
            tension: 0.15,
            pointBackgroundColor: "#eee",
            pointHoverBackgroundColor: "#eee",
            pointHitRadius: 10,
            pointRadius: 5,
            pointStyle: 'circle',
            pointHoverRadius: 6,
        };
        datasets.push(dataset);
    };

    // Add KSE100 data to datasets
    datasets.push({
        label: "KSE100",
        data: dataToCoordinates(KSE100Data),
        fill: false,
        borderColor: colors["KSE100"],
        borderWidth: 3.2,
        backgroundColor: colors["KSE100"],
        tension: 0.15,
        pointBackgroundColor: "#eee",
        pointHoverBackgroundColor: "#eee",
        pointHitRadius: 10,
        pointRadius: 5,
        pointStyle: 'circle',
        pointHoverRadius: 6,
    });

    return {
        datasets: datasets
    };
};


if (portfolioPerformanceSection) {
    const portfolioPerformanceChartCanvas = portfolioPerformanceSection.querySelector("#portfolio-performance-chart");
    const portfolioPerformanceFiltersWrapper = portfolioPerformanceSection.querySelector("#portfolio-performance-filters");
    const portfolioPerformanceFilters = portfolioPerformanceSection.querySelectorAll(".portfolio-performance-filter");
    const stockComparisonSection = document.querySelector("#stock-comparison");
    const selectedStocksContainer = stockComparisonSection.querySelector("#selected-stocks");
    const stockChoicesContainer = stockComparisonSection.querySelector("#stock-choices");
    const stockChoices = stockComparisonSection.querySelectorAll(".stock-choice");
    const stockComparisonCounter = document.querySelector("#stock-comparison-counter");
    const filterURL = portfolioPerformanceSection.dataset.filterurl;

    const lineChartConfig = {
        type: 'line',
        // data: getLineChartData(portfolioPerformanceChartCanvas.dataset.chartdata),
        data: { datasets: [] },
        options: {
            responsive: true,
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Return (%)',
                        color: "#ddd",
                        font: {
                            size: 13,
                            weight: "bold"
                        }
                    },
                    stacked: true,
                    alignToPixels: true,
                    ticks: {
                        color: "#ddd",
                        major: {
                            enabled: true,
                            fontStyle: 'bold'
                        }
                    },
                    border: {
                        display: false
                    },
                    grid: {
                        color: '#ddd'
                    }
                },
                x: {
                    alignToPixels: true,
                    ticks: {
                        color: "#ddd",
                        major: {
                            enabled: true,
                            fontStyle: 'bold'
                        }
                    },
                    border: {
                        display: false
                    },
                    grid: {
                        display: false
                    }
                }
            },
            hover: {
                mode: 'nearest',
                intersect: true
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        font: {
                            size: 11,
                            weight: 500,
                        },
                        color: "#ddd",
                        textAlign: 'left',
                        padding: 10,
                    },
                    rtl: false,
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const value = context.dataset.data[context.dataIndex].y;
                            const label = context.dataset.label;
                            return `${label}: ${value.toFixed(2)}%`;
                        }
                    }
                }
            }
        }
    };

    const portfolioPerformanceChart = new Chart(portfolioPerformanceChartCanvas, lineChartConfig);
    const filterData = {
        "timezone": getClientTimezone(),
    };

    // Function to update chart with new data
    function updateLineChart(chart, rawData) {
        chart.data.datasets = getLineChartData(rawData).datasets;
        chart.update();
    };

    function updateStockComparisonCounter() {
        const stocksSelected = filterData.stocks ?? [];
        const count = stocksSelected.length;
        if (!count) {
            stockComparisonCounter.innerHTML = count;
            stockComparisonCounter.style.display = "none";
            return;
        };

        stockComparisonCounter.innerHTML = count;
        stockComparisonCounter.style.display = "block";
    };

    function moveStockChoiceToContainer(stockChoice, container) {
        const parentContainer = stockChoice.parentElement;
        if (container === parentContainer) {
            return;
        }
        _removeStockChoiceFromContainer(stockChoice, parentContainer);
        container.appendChild(stockChoice);
    };

    function _removeStockChoiceFromContainer(stockChoice, container) {
        container.removeChild(stockChoice);
    };

    function getActivePortofolioPerformanceFilter() {
        for (let i = 0; i < portfolioPerformanceFilters.length; i++) {
            const filter = portfolioPerformanceFilters[i];
            if (!filter.isActive()) {
                continue
            }
            return filter;
        }
        return;
    };

    function clickActivePortfolioPerformanceFilter() {
        const activeFilter = getActivePortofolioPerformanceFilter();

        if (activeFilter) {
            activeFilter.forceClick();
        };
    };

    function updatePortfolioPerformanceChartForFilter(filterValue, callbackFn = null) {
        filterData["dt_filter"] = filterValue;

        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            mode: 'same-origin',
            body: JSON.stringify(filterData),
        }

        fetch(filterURL, options).then((response) => {
            if (!response.ok) {
                response.json().then((data) => {
                    pushNotification("error", data.detail ?? data.message ?? 'An error occurred!');
                });

            } else {
                response.json().then((data) => {
                    const rawData = data.data;
                    console.log(rawData)
                    updateLineChart(portfolioPerformanceChart, rawData);

                    if (callbackFn) {
                        callbackFn();
                    };
                });
            }
        }).catch((error) => {
            console.error(error);
            pushNotification("error", error.message ?? 'An error occurred!');
        });
    };

    portfolioPerformanceFilters.forEach(filter => {
        filter.forceFetch = false;

        filter.isActive = () => {
            return filter.parentElement.classList.contains("active");
        };

        filter.setAsActive = () => {
            const activeFilterParentElement = portfolioPerformanceFiltersWrapper.querySelector("li.active");
            activeFilterParentElement.classList.remove("active");
            filter.parentElement.classList.add("active");
        };

        filter.forceClick = () => {
            filter.forceFetch = true;
            filter.click();
            filter.forceFetch = false;
        };

        filter.addEventListener("click", (e) => {
            e.preventDefault();
            if (filter.isActive() && !filter.forceFetch) return;

            const filterValue = filter.dataset.value;
            updatePortfolioPerformanceChartForFilter(filterValue, filter.setAsActive);
        });
    });

    stockChoices.forEach((stockChoice) => {
        stockChoice.changeIcon = () => {
            const innerIcon = stockChoice.querySelector("i");
            if (innerIcon.classList.contains("fa-times")) {
                innerIcon.classList.remove("fa-times");
                innerIcon.classList.add("fa-plus");
            } else {
                innerIcon.classList.remove("fa-plus");
                innerIcon.classList.add("fa-times");
            }
        };

        stockChoice.addEventListener("click", () => {
            const choice = stockChoice.dataset.value;
            const parentContainer = stockChoice.parentElement;

            if (parentContainer === stockChoicesContainer) {
                moveStockChoiceToContainer(stockChoice, selectedStocksContainer);
                stockChoice.changeIcon();

                const alreadySelectedStocks = filterData.stocks ?? []
                filterData["stocks"] = [...alreadySelectedStocks, choice];
                clickActivePortfolioPerformanceFilter();
            }

            else if (parentContainer === selectedStocksContainer) {
                moveStockChoiceToContainer(stockChoice, stockChoicesContainer);
                stockChoice.changeIcon();

                const alreadySelectedStocks = filterData.stocks ?? []
                if (alreadySelectedStocks) {
                    filterData["stocks"] = alreadySelectedStocks.filter(item => item !== choice);
                    clickActivePortfolioPerformanceFilter();
                };
            };

            updateStockComparisonCounter();
        });
    });

    // (Force) Click the first performance filter to trigger portfolio performance data fetch
    portfolioPerformanceFilters[0].forceClick();

    let refreshIntervalID;
    /**
     * Start refreshing performance data at a given interval
     */
    function startPerformanceDataRefresh() {
        refreshIntervalID = setInterval(
            clickActivePortfolioPerformanceFilter, performanceDataRefreshInterval
        );
    }

    /**
     * Stop refreshing performance data
     */
    function stopPerformanceDataRefresh() {
        clearInterval(refreshIntervalID);
    }

    // Visibility change event handler
    const visibilityHandler = createVisibilityHandler(
        startPerformanceDataRefresh, stopPerformanceDataRefresh
    );
    // Add visibility change event listener
    document.addEventListener("visibilitychange", visibilityHandler);
    // Stop performance data refresh when the window is closed or refreshed
    window.addEventListener("beforeunload", function (e) {
        stopPerformanceDataRefresh();
    });

    // Initial start of performance data refresh
    startPerformanceDataRefresh();
};


