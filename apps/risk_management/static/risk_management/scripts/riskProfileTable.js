const profileTabs = document.querySelectorAll('.tabs-section .tab');
const profileTabToggles = document.querySelectorAll('.tab-toggle');
const profileTabDataReloaders = document.querySelectorAll('.tab-data-reloader');

/**
 * Update the cell properties based on whether its value is thruthy or not
 * @param {*} cell 
 * @param {*} formatterParams 
 * @param {*} onRendered 
 * @returns cell value
 */
function truthyArrowFormatter(cell, formatterParams, onRendered) {
    let value = cell.getValue();
    cell.getElement().style.textAlign = "center";

    if (value) {
        cell.getElement().classList.add("text-success");
        return '<i class="fas fa-arrow-up"></i>';
    } else {
        cell.getElement().classList.add("text-danger");
        return '<i class="fas fa-arrow-down"></i>';
    }
};


/**
 * Format the background and color of the cell based on the value. 
 * The color transitions from red (low values) to yellow (mid values) to green (high values).
 * Sort of like a heatmap
 * @param {*} cell 
 * @param {*} formatterParams 
 * @param {*} onRendered 
 * @returns The cell value as percentage
 */
function heatMapFormatter(cell, formatterParams, onRendered) {
    let value = cell.getValue();
    let intensity = parseInt(value, 10) / 100; // value as a fraction of 100

    let red = 255;
    let green = 0;

    // Transition from red (low values) to yellow (mid values) to green (high values)
    if (intensity < 0.5) {
        green = Math.floor(510 * intensity); // increase green up to 255 (yellow)
    } else {
        green = 255; // stay at max green
        red = Math.floor(510 * (1 - intensity)); // decrease red from 255 to 0 (green)
    }
    let color = `rgba(${red}, ${green}, 0, 0.7)`; // final color with adjusted opacity

    cell.getElement().style.backgroundColor = color;
    cell.getElement().style.color = "#e0e0e0";
    return value;
}

const comparisonOperators = ['<', '>', '<=', '>=', '=', '!='];

function columnDefinitionsHandler(definitions) {
    definitions.forEach((column, index) => {
        // Freeze the first two columns
        if (index in [0, 1]) {
            column.frozen = true;
        }
        // For columns whose title contains comparison operators, set the formatter to truthyArrowFormatter
        else if (comparisonOperators.some((op) => column.title.includes(op))) {
            column.formatter = truthyArrowFormatter;
        }
        // For the last cell, set the background color of the cell based on the value
        else if (index === definitions.length - 1) {
            column.formatter = heatMapFormatter;
        }
        column.title = column.title.toUpperCase();
    });
    return definitions;
}


function buildTable(tableData, tableElement) {
    var table = new Tabulator(tableElement, {
        data: tableData,
        autoColumns: true,
        autoColumnsDefinitions: columnDefinitionsHandler,
        autoResize: true,
        resizableColumnFit: true,
        pagination: "local",
        paginationSize: 30,
        paginationSizeSelector: [10, 20, 30, 40, 50, 100],
        movableColumns: true,
        paginationCounter: "rows",
        // layout: "fitColumns",
        layoutColumnsOnNewData: true,
    });

    // Sort the table by descending order of the last column
    // PS: The last column is the ranking of each stock
    table.on("tableBuilt", function () {
        // Get the column definitions
        let columns = table.getColumns();
        // Get the field name of the last column
        if (!columns.length) return;
        let lastColumnField = columns[columns.length - 1].getField();
        // Apply sorting to the last column
        table.setSort(lastColumnField, "desc");
    });
    return table;
};


function getStockSetFormData(tabEl) {
    const stockSetForm = tabEl.querySelector(".stockset-form");
    const formData = new FormData(stockSetForm)
    const data = {};
    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }
    return data
}

profileTabDataReloaders.forEach((reloader, index) => {

    reloader.addEventListener('click', () => {
        const tabDataUrl = reloader.dataset.tabDataUrl;

        // Get the tab corresponding to the reloader's index
        const profileTab = profileTabs[index];
        const tabTable = profileTab.querySelector('.risk-profile-table');

        if (!tabDataUrl) return;

        const options = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            mode: 'same-origin',
        }

        const url = new URL(tabDataUrl, window.location.origin);
        const stockset = getStockSetFormData(profileTab).stockset;
        if (stockset) {
            url.searchParams.append('stockset', stockset);
        }

        // Add the spin class to the reloader and disable it
        reloader.classList.add("spin", "disabled");
        fetch(url, options).then((response) => {
            // On response, remove the spin class and enable the reloader
            reloader.classList.remove("spin", "disabled");

            if (!response.ok) {
                response.json().then((data) => {
                    pushNotification("error", data.detail ?? data.message ?? 'An error occurred!');
                });

            } else {
                response.json().then((data) => {
                    const tabData = data.data ?? null;
                    if (!tabData) return;
                    buildTable(tabData, tabTable);
                });
            }
        }).catch(
            (error) => {
                console.error(error);
                pushNotification("error", "An error occurred!");
                // On error, remove the spin class and enable the reloader
                reloader.classList.remove("spin", "disabled");
            }
        );
    });
});


/**
 * Render the table data for the profile tab if it has not been rendered
 * @param {HTMLElement} profileTab 
 */
function renderProfileTabTableData(profileTab) {
    const profileTable = profileTab.querySelector('.risk-profile-table');
    const profileTabDataReloader = profileTab.querySelector('.tab-data-reloader');

    // If the table element contains a tabulator js table element, it means the table has been rendered
    const tableHasBeenRendered = profileTable.querySelector(".tabulator-table") !== null;
    // If it does not, click on the tab data reloader to fetch and render table data
    if (!tableHasBeenRendered) {
        profileTabDataReloader.click();
    }
};


profileTabToggles.forEach((toggle, index) => {

    toggle.addEventListener('click', () => {
        const profileTab = profileTabs[index];
        renderProfileTabTableData(profileTab);
    });
});


profileTabs.forEach((profileTab) => {
    const profileTabDataReloader = profileTab.querySelector('.tab-data-reloader');
    const stockSetForm = profileTab.querySelector(".stockset-form");

    stockSetForm.addEventListener("change", () => {
        profileTabDataReloader.click();
    });
});


// On page load, click on the first active tab toggle
// If there are no active tab toggles, click on the first tab toggle
// So that the table data is rendered if it has not been rendered yet
document.addEventListener("DOMContentLoaded", () => {
    // If there are no profile tabs, return
    if (profileTabToggles.length === 0) return;

    // Get the active tab toggles
    const activeTabToggles = Array.from(profileTabToggles).filter(
        (toggle) => toggle.classList.contains("active")
    );

    // If there are active tab toggles, click on the first active tab toggle
    if (activeTabToggles.length > 0){
        const activeTabToggle = activeTabToggles[0];
        activeTabToggle.click();
    }else{
        // If there are no active tab toggles, click on the first tab toggle
        profileTabToggles[0].click();
    }
})
