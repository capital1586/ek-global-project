const profileCreateForm = document.querySelector('#profile-create-form');


if (profileCreateForm) {
    const profileCreateButton = profileCreateForm.querySelector('.submit-btn');

    addOnPostAndOnResponseFuncAttr(profileCreateButton, 'Processing...');

    profileCreateForm.onsubmit = function(e) {
        e.stopImmediatePropagation();
        e.preventDefault();

        const data = getProfileFormData(profileCreateForm);
        const criteria = data.criteria;
        if (!criteria.length) {
            pushNotification("error", "At least one criterion is required!");
            return;
        }

        profileCreateButton.onPost();
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            mode: 'same-origin',
            body: JSON.stringify(data),
        }

        fetch(this.action, options).then((response) => {
            if (!response.ok) {
                profileCreateButton.onResponse();
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
                            
                            let field = this.querySelector(`*[name=${fieldName}]`);
                            if (!field) return;
                            field.scrollIntoView({"block": "center"});
                            formFieldHasError(field.parentElement, msg);
                        };

                    }else{
                        pushNotification("error", data.detail ?? data.message ?? 'An error occurred!');
                    };
                });

            }else{
                profileCreateButton.onResponse();
                profileCreateButton.disabled = true;

                response.json().then((data) => {
                    pushNotification("success", data.detail ?? data.message ?? 'Request successful!');

                    const redirectURL  = data.redirect_url ?? null
                    if(!redirectURL) return;

                    setTimeout(() => {
                        window.location.href = redirectURL;
                    }, 2000);
                });
            }
        }).catch(
            (error) => {
                console.error(error);
                profileCreateButton.onResponse();
                pushNotification("error", "An error occurred!");
            }
        );
    };
};

