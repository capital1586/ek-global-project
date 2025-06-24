const tabsSections = document.querySelectorAll(".tabs-section");


tabsSections.forEach((tabSection, index) => {
    const tagToggles = tabSection.querySelectorAll(".tab-toggle");
    const tabs = tabSection.querySelectorAll(".tab");
    const tabURLParam = tabSection.dataset.urlparam ?? `tab_${index}`;

    tagToggles.forEach((tabToggle) => {
        tabToggle.clicked = function(){
            tagToggles.forEach((tabToggle) => {
                tabToggle.classList.remove("active")
            })
            this.classList.add("active");
        }

        tabToggle.addEventListener("click", function() {
            // Get the target tab's ID and display it (hiding other tabs)
            const targetTabID = this.dataset.tabtarget ?? null;
            if (!targetTabID) return;

            // Update the page's url params to refelect the current active tab
            updateURLParams(tabURLParam, targetTabID)
            tabToggle.clicked()

            tabs.forEach((tab) => {
                if (tab.id == targetTabID){
                    tab.classList.add("show-flex");
                }
                else{
                    tab.classList.remove("show-flex");
                }
            });
        });
    });

    // Get the first tab to show as defined in the page's url params
    const startTabID = URLParams[tabURLParam]
    if (!startTabID) return;
    // Get that tab's toggle
    const startTabToggle = tabSection.querySelector(`.tab-toggle[data-tabtarget='${startTabID}']`);
    if (!startTabToggle) return;
    // Click the tab's toggle to switch to the tab
    startTabToggle.click();
});
