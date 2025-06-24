const transactionAddForm = document.querySelector('#transaction-add-form');
const transactionAddFormCard = transactionAddForm.parentElement;
const transactionAddButton = transactionAddForm.querySelector('.submit-btn');
const rateFetchButton = transactionAddForm.querySelector('#rate-fetch-btn');
const stockInputField = transactionAddForm.querySelector("select[name='stock']") 
const rateInputField = transactionAddForm.querySelector("input[name='rate']") 

addOnPostAndOnResponseFuncAttr(transactionAddButton, 'Processing...');
addOnPostAndOnResponseFuncAttr(rateFetchButton, 'Fetching Price...');


rateFetchButton.addEventListener("click", (e) => {
    e.stopImmediatePropagation();
    e.preventDefault();

    const url = rateFetchButton.dataset.url;
    const data = {
        "stock": stockInputField.value
    }

    rateFetchButton.onPost();
    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        mode: 'same-origin',
        body: JSON.stringify(data),
    }

    fetch(url, options).then((response) => {
        if (!response.ok) {
            rateFetchButton.onResponse();
            response.json().then((data) => {
                pushNotification("error", data.detail ?? data.message ?? 'An error occurred!');
            });

        }else{
            rateFetchButton.onResponse();

            response.json().then((data) => {
                const latestPrice  = data.data.latest_price ?? null
                if(!latestPrice) return;

                rateInputField.value = latestPrice;
            });
        }
    }).catch(
        (error) => {
            console.error(error);
            pushNotification("error", "An error occurred!");
            rateFetchButton.onResponse();
        }
    );
});


transactionAddForm.addEventListener("submit", function(e) {
    e.stopImmediatePropagation();
    e.preventDefault();

    const formData = new FormData(transactionAddForm);
    const data = {};
    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }

    transactionAddButton.onPost();
    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        mode: 'same-origin',
        body: JSON.stringify(data),
    }

    fetch(transactionAddForm.action, options).then((response) => {
        if (!response.ok) {
            transactionAddButton.onResponse();
            response.json().then((data) => {
                const errors = data.errors ?? null;
                if (errors){
                    console.log(errors)
                    if(!typeof errors === Object) throw new TypeError("Invalid data type for 'errors'")

                    for (const [fieldName, msg] of Object.entries(errors)){
                        if (fieldName == "__all__"){
                            if (typeof msg === Array){
                                msg.forEach((m) => {
                                    pushNotification("error", m);
                                });
                            }else{
                                pushNotification("error", msg);
                            };
                        };
                        
                        let field = transactionAddForm.querySelector(`*[name=${fieldName}]`);
                        if (!field) return;
                        field.scrollIntoView({"block": "center"});
                        formFieldHasError(field.parentElement, msg);
                    };

                }else{
                    pushNotification("error", data.detail ?? data.message ?? 'An error occurred!');
                };
            });

        }else{
            transactionAddButton.onResponse();
            transactionAddButton.disabled = true;

            response.json().then((data) => {
                pushNotification("success", data.detail ?? data.message ?? 'Request successful!');

                const redirectURL  = data.redirect_url ?? null
                if(!redirectURL) return;

                setTimeout(() => {
                    window.location.href = redirectURL;
                }, 1000);
            });
        }
    }).catch(
        (error) => {
            console.error(error);
            pushNotification("error", "An error occurred!");
            transactionAddButton.onResponse();
        }
    );
});

