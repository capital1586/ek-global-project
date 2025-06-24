const functionsModals = document.querySelectorAll(".functions-modal");


/**
 * Returns the visible element with the highest z-index from a given list of elements.
 *
 * @param {HTMLElement[]} elements - An array or NodeList of HTML elements to check.
 * @returns {HTMLElement|null} - The visible element with the highest z-index. Returns null if no visible element has a valid z-index.
 *
 * @example
 * const elements = document.querySelectorAll('.some-class');
 * const highestVisibleElement = getElementWithHighestZIndex(elements);
 * if (highestVisibleElement) {
 *     console.log('Visible element with highest z-index:', highestVisibleElement, 'with z-index:', window.getComputedStyle(highestVisibleElement).zIndex);
 * } else {
 *     console.log('No visible element with a valid z-index found.');
 * }
 */
function getVisibleElementWithHighestZIndex(elements) {
    let highestVisibleElement = null;
    let highestZIndex = -Infinity;
    const elementArray = Array.isArray(elements) ? elements : Array.from(elements);

    // Filter elements array down to those that are visible
    const visibleElements = elementArray.filter((element) => {
        if (!element) return false;

        const style = window.getComputedStyle(element);
        const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
        return isVisible
    })

    visibleElements.forEach(element => {
        const style = window.getComputedStyle(element);
        let zIndex = parseInt(style.zIndex, 10);
        if (isNaN(zIndex)) {
            zIndex = 0;
        }

        // Check if zIndex is greater than the highest z-index
        if (zIndex >= highestZIndex) {
            highestZIndex = zIndex;
            highestVisibleElement = element;
        }
    });

    return highestVisibleElement;
}


function getSubOptionFormFieldsData(formfieldsContainer) {
    const data = {
        "name": null,
        "options": {}
    };
    const formFields = formfieldsContainer.querySelectorAll(".form-field");

    formFields.forEach(formField => {
        const formInput = formField.querySelector(".form-input");
        data.options[formInput.name] = formInput.value;
    });

    data.name = formfieldsContainer.dataset.function;
    return data;
}


functionsModals.forEach(functionsModal => {
    const functionsModalCloseBtn = functionsModal.querySelector(".modal-head .btn-close");
    const optionsSearchInput = functionsModal.querySelector(".options-search-input");
    const mainOptionSet = functionsModal.querySelector(".function-options.options");
    const subOptionSets = functionsModal.querySelectorAll(".sub-options");
    const allOptionSets = [...subOptionSets, mainOptionSet];
    const allOptions = functionsModal.querySelectorAll(".option");


    allOptionSets.forEach(optionSet => {
        optionSet.close = () => {
            optionSet.classList.remove("show-flex");
    
            // Reset all form inputs to their default values
            const formInputs = document.querySelectorAll(".form-input");
            formInputs.forEach(formInput => {
                formInput.value = formInput.dataset.default ?? formInput.value;
            });
        };
    
        optionSet.open = () => {
            optionSet.classList.add("show-flex");
        };
    });
    
    
    subOptionSets.forEach(subOptionSet => {
        const formFieldsDoneBtns = subOptionSet.querySelectorAll(".form-fields .done-btn");
    
        formFieldsDoneBtns.forEach(doneBtn => {
            doneBtn.addEventListener("click", () => {
                subOptionSet.close();
            });
        });
    });
    
    
    functionsModal.reset = () => {
        subOptionSets.forEach(subOptionSet => {
            subOptionSet.close();
        });
    }
    
    functionsModal.open = () => {
        functionsModal.classList.add("show-flex");
    }
    
    functionsModal.close = () => {
        functionsModal.classList.remove("show-flex");
    }
    
    
    // Search functionality
    optionsSearchInput.addEventListener('input', function () {
        const filter = this.value.toLowerCase();
        const targetOptionSet = getVisibleElementWithHighestZIndex(allOptionSets);
    
        targetOptionSet.querySelectorAll('.option').forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = text.includes(filter) ? '' : 'none';
        });
    });
    
    
    allOptions.forEach(option => {
        const optionLabel = option.querySelector(".option-label");
        const subOptionSet = option.querySelector(".sub-options");
        // If the option does not have sub options, ther's no point
        // add a click listener to option the sub options
        if (!subOptionSet) return;
    
        optionLabel.addEventListener("click", () => {
            // Revert the scroll of the parent container
            option.parentElement.scrollTop = 0;
    
            subOptionSet.open();
            const subOptionBackArrow = subOptionSet.querySelector(".sub-options-head > .arrow");
    
            subOptionBackArrow.addEventListener("click", () => {
                subOptionSet.close();
            });
        });
    });
    
    
    functionsModalCloseBtn.addEventListener("click", () => {
        functionsModal.close();
    });
    
});
