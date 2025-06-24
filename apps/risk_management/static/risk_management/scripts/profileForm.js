
/**
 * Resets the values of the given form inputs
 * @param {HTMLElement} formInputs 
 */
function resetFormInputs(formInputs) {
    formInputs.forEach(formInput => {
        formInput.value = null;
    });
}


function extractCriterionCreationFormInputsData(formInputs) {
    const data = {}

    formInputs.forEach(input => {
        const options = input.dataset.options ?? null;
        if (options) {
            data[input.name] = {
                "name": input.value,
                "kwargs": JSON.parse(options),
            }
        }
        else {
            data[input.name] = input.value
        }
    });

    return data;
}


/**
 * Makes an HTMLElement holding the criterion data
 * @param {Object} criterionData
 * @returns {HTMLButtonElement}
 */
function makeCriterionElement(criterionData) {
    const criterionEl = document.createElement("button");
    criterionEl.type = "button";
    criterionEl.dataset.data = JSON.stringify(criterionData);
    criterionEl.classList.add("btn", "btn-outline-primary", "btn-xs", "criterion");

    const criterionName = `${criterionData.func1.name} ${criterionData.op} ${criterionData.func2.name}`;
    criterionEl.innerHTML = `
        ${criterionName}
        <i class="fas fa-times fa-xs"></i>
    `

    criterionEl.addEventListener("click", () => {
        criterionEl.remove();
    });

    return criterionEl;
}


function extractSelectedCriteriaData(selectedCriteriaContainer) {
    const selectedCriteria = selectedCriteriaContainer.querySelectorAll(".criterion");
    const data = []

    selectedCriteria.forEach(criterion => {
        const criterionData = criterion.dataset.data ?? null;
        if (!criterionData) return;

        data.push(JSON.parse(criterionData));
    });

    return data;
}


function getProfileFormData(profileForm) {
    const topLevelFormInputs = document.querySelectorAll(`#${profileForm.id} > .form-fields > .form-field > .form-input`);
    const selectedCriteriaContainer = profileForm.querySelector('.criteria-selected');
    const data = {}

    topLevelFormInputs.forEach(input => {
        data[input.name] = input.value
    });
    data["criteria"] = extractSelectedCriteriaData(selectedCriteriaContainer);

    return data;
}


function captureFunctionSelection(functionsModal, inputField) {
    const options = functionsModal.querySelectorAll(".option");

    options.forEach(option => {
        const optionSubOptions = option.querySelector(".sub-options");

        if (!optionSubOptions) {
            option.addEventListener("click", () => {
                const functionName = option.dataset.function ?? null;
                if (!functionName) return;

                inputField.value = functionName;
                inputField.dataset.options = null;

                functionsModal.close();
            });
            return;
        };

        const doneBtns = functionsModal.querySelectorAll(".done-btn");
        doneBtns.forEach(doneBtn => {
            doneBtn.addEventListener("click", () => {
                const parentFormFieldContainer = doneBtn.closest(".form-fields");
                const formFieldsData = getSubOptionFormFieldsData(parentFormFieldContainer);
                inputField.value = formFieldsData.name;
                inputField.dataset.options = JSON.stringify(formFieldsData.options);
        
                functionsModal.close();
            });
        });
    });
};


const profileForms = document.querySelectorAll('.profile-form');

profileForms.forEach(profileForm => {
    const selectedCriteriaContainer = profileForm.querySelector('.criteria-selected');
    const selectedCriteria = selectedCriteriaContainer.querySelectorAll(".criterion");
    const criterionCreationSection = profileForm.querySelector(".criterion-creation-section");
    const criterionCreationSectionToggle = profileForm.querySelector('.criterion-creation-section-toggle');
    const criterionCreationFieldsContainer = criterionCreationSection.querySelector(".criterion-creation-fields");
    const criterionCreationFormFields = criterionCreationFieldsContainer.querySelector(".form-fields");
    const criterionCreationFormInputs = criterionCreationSection.querySelectorAll(".criterion-creation-fields > .form-fields > .form-field > .form-input");
    const functionInputs = criterionCreationFormFields.querySelectorAll("input.function-input");
    const criterionAddButton = criterionCreationFieldsContainer.querySelector(".add-btn");
    

    selectedCriteriaContainer.addCriteria = (criteriaData) => {
        const criterionEl = makeCriterionElement(criteriaData);
        selectedCriteriaContainer.appendChild(criterionEl);
    }

    selectedCriteria.forEach(criterion => {
        criterion.addEventListener("click", () => {
            criterion.remove();
        });
    });

    criterionCreationSectionToggle.addEventListener("click", () => {
        criterionCreationSection.classList.toggle("show-block");
    });

    
    functionInputs.forEach((input) => {
        input.addEventListener("click", () => {
            const functionsModal = input.parentElement.querySelector(".functions-modal");
            if (!functionsModal) return;

            functionsModal.open();
            captureFunctionSelection(functionsModal, input);
        });
    });


    criterionCreationFieldsContainer.addEventListener("pointerover", () => {
        const allFieldsHaveValues = Array.from(criterionCreationFormInputs).every((input) => {
            if (!input.value){
                return false
            }
            return true
        })

        if (allFieldsHaveValues){
            criterionAddButton.disabled = false;
        }else {
            criterionAddButton.disabled = true;
        }
    });


    criterionAddButton.addEventListener("click", () => {
        const criteriaData = extractCriterionCreationFormInputsData(criterionCreationFormInputs);
        selectedCriteriaContainer.addCriteria(criteriaData);
        
        criterionCreationSection.classList.remove("show-block");
        resetFormInputs(criterionCreationFormInputs);
    });

});
